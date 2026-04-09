"""
Core migration engine for PostgreSQL Migrator.
Orchestrates the migration process from detection to completion.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .events.bus import MigrationEvent, MigrationEventType, get_event_bus
from .analyzer import AnalysisResult, CompatibilityAnalyzer
from .db_manager import prepare_target_db_from_dsn
from .detector import VersionDetector, VersionInfo
from .logger import get_logger
from .pg_upgrade_wrapper import DumpRestoreMigrator
from .python_migrator import PythonMigrator
from .utils import Timer, ensure_directory, generate_backup_name


class MigrationMethod(Enum):
    """Available migration methods."""
    PG_UPGRADE = "pg_upgrade"
    DUMP_RESTORE = "dump_restore"
    PYTHON = "python"  # Pure Python with psycopg2, no pg_dump dependency


class MigrationState(Enum):
    """Migration process states."""
    IDLE = "idle"
    CONNECTING = "connecting"
    DETECTING = "detecting"
    ANALYZING = "analyzing"
    BACKING_UP = "backing_up"
    MIGRATING = "migrating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationStep:
    """Represents a migration step."""
    name: str
    description: str
    status: str = "pending"  # pending, running, success, failed, skipped
    duration: Optional[float] = None
    error: Optional[str] = None


@dataclass
class MigrationContext:
    """Context for migration execution."""
    source_dsn: str
    target_dsn: str
    method: MigrationMethod = MigrationMethod.DUMP_RESTORE
    source_version: Optional[VersionInfo] = None
    target_version: Optional[VersionInfo] = None
    analysis_result: Optional[AnalysisResult] = None
    backup_path: Optional[Path] = None
    backup_dir: Path = field(default_factory=lambda: Path("./backups"))
    parallel_jobs: int = 4
    dry_run: bool = False

    # State tracking
    state: MigrationState = MigrationState.IDLE
    steps: List[MigrationStep] = field(default_factory=list)
    current_step: int = 0
    timer: Timer = field(default_factory=Timer)

    def add_step(self, name: str, description: str):
        """Add a migration step."""
        self.steps.append(MigrationStep(name=name, description=description))

    def get_current_step(self) -> Optional[MigrationStep]:
        """Get current step."""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None


class MigrationEngine:
    """
    Main migration engine that orchestrates the migration process.
    """

    def __init__(
        self,
        context: MigrationContext,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        """
        Initialize migration engine.
        
        Args:
            context: Migration context with configuration
            progress_callback: Optional callback for progress updates (message, percentage)
        """
        self.context = context
        self.progress_callback = progress_callback
        self.logger = get_logger()
        self.bus = get_event_bus()

        # Initialize steps
        self._init_steps()

    def _init_steps(self):
        """Initialize migration steps."""
        self.context.steps.clear()
        self.context.add_step("connect", "Connect to source database")
        self.context.add_step("detect", "Detect PostgreSQL versions")
        self.context.add_step("analyze", "Analyze compatibility")
        self.context.add_step("prepare", "Prepare target database")
        self.context.add_step("backup", "Create backup")
        self.context.add_step("migrate", "Perform migration")
        self.context.add_step("validate", "Validate migration")

    def _update_progress(self, message: str, percentage: Optional[float] = None):
        """Update progress via callback and event bus."""
        pct = percentage if percentage is not None else (
            (self.context.current_step / len(self.context.steps)) * 100
        )
        
        # Event bus
        self.bus.publish(MigrationEvent(
            type=MigrationEventType.PROGRESS,
            message=message,
            current=int(pct),
            total=100
        ))

        if self.progress_callback:
            self.progress_callback(message, pct)

    def _mark_step(self, status: str, error: Optional[str] = None):
        """Mark current step with status and publish event."""
        step = self.context.get_current_step()
        if step:
            step.status = status
            step.error = error
            
            event_type = MigrationEventType.STEP_COMPLETE
            if status == "running":
                event_type = MigrationEventType.STEP_START
            elif status == "failed":
                event_type = MigrationEventType.STEP_FAIL
            elif status == "skipped":
                event_type = MigrationEventType.STEP_SKIP
                
            self.bus.publish(MigrationEvent(
                type=event_type,
                message=step.description,
                payload={"step_name": step.name, "error": error}
            ))

    def run(self) -> bool:
        """
        Execute the full migration process.
        
        Returns:
            True if migration successful, False otherwise
        """
        self.context.timer.start()
        self.logger.migration_start(
            self.context.source_version.major if self.context.source_version else 0
        )

        try:
            # Step 1: Connect
            self.context.current_step = 0
            self.context.state = MigrationState.CONNECTING
            self._mark_step("running")
            self._update_progress("Connecting to databases...")

            if not self._step_connect():
                return self._fail("Failed to connect to databases")

            self._mark_step("success")

            # Step 2: Detect versions
            self.context.current_step = 1
            self.context.state = MigrationState.DETECTING
            self._mark_step("running")
            self._update_progress("Detecting PostgreSQL versions...")

            if not self._step_detect():
                return self._fail("Version detection failed")

            self._mark_step("success")

            # Step 3: Analyze compatibility
            self.context.current_step = 2
            self.context.state = MigrationState.ANALYZING
            self._mark_step("running")
            self._update_progress("Analyzing compatibility...")

            if not self._step_analyze():
                return self._fail("Compatibility analysis failed")

            self._mark_step("success")

            # Check for blockers
            if self.context.analysis_result and self.context.analysis_result.has_blockers:
                return self._fail("Migration blocked by critical issues")

            # Step 4: Prepare target database
            self.context.current_step = 3
            self.context.state = MigrationState.CONNECTING
            self._mark_step("running")
            self._update_progress("Preparing target database...")

            if not self.context.dry_run:
                if not self._step_prepare():
                    return self._fail("Failed to prepare target database")
            else:
                self.logger.info("Dry run: Skipping target database preparation")
                self._mark_step("skipped")

            if not self.context.dry_run:
                self._mark_step("success")

            # Step 5: Backup (skip for PYTHON method - no pg_dump dependency)
            self.context.current_step = 4
            self.context.state = MigrationState.BACKING_UP
            self._mark_step("running")
            self._update_progress("Creating backup...")

            if self.context.method == MigrationMethod.PYTHON:
                # PYTHON method doesn't need pg_dump backup
                self.logger.info("Python migration mode: Backup not required (direct copy)")
                self._mark_step("skipped")
            elif not self.context.dry_run:
                if not self._step_backup():
                    return self._fail("Backup creation failed")
                self._mark_step("success")
            else:
                self.logger.info("Dry run: Skipping backup")
                self._mark_step("skipped")

            # Step 6: Migrate
            self.context.current_step = 5
            self.context.state = MigrationState.MIGRATING
            self._mark_step("running")
            self._update_progress("Performing migration...")

            if not self.context.dry_run:
                if not self._step_migrate():
                    return self._fail("Migration failed")
            else:
                self.logger.info("Dry run: Skipping actual migration")
                self._mark_step("skipped")

            if not self.context.dry_run:
                self._mark_step("success")

            # Step 7: Validate
            self.context.current_step = 6
            self.context.state = MigrationState.VALIDATING
            self._mark_step("running")
            self._update_progress("Validating migration...")

            if not self.context.dry_run:
                if not self._step_validate():
                    return self._fail("Validation failed")
            else:
                self.logger.info("Dry run: Skipping validation")
                self._mark_step("skipped")

            if not self.context.dry_run:
                self._mark_step("success")

            # Complete
            self.context.state = MigrationState.COMPLETED
            self.context.timer.stop()
            self.logger.migration_complete(self.context.timer.formatted, True)
            
            self.bus.publish(MigrationEvent(
                type=MigrationEventType.COMPLETED,
                message="Migration completed successfully",
                payload={"duration": self.context.timer.formatted}
            ))

            return True

        except Exception as e:
            return self._fail(str(e))

    def _fail(self, error: str) -> bool:
        """Handle migration failure."""
        self.context.state = MigrationState.FAILED
        self._mark_step("failed", error)
        self.context.timer.stop()
        self.logger.error(error)
        self.logger.migration_complete(self.context.timer.formatted, False)
        
        self.bus.publish(MigrationEvent(
            type=MigrationEventType.ERROR,
            message=error,
            payload={"duration": self.context.timer.formatted}
        ))
        
        return False

    def _step_connect(self) -> bool:
        """Connect to source and target databases."""
        try:
            # Test source connection
            source_detector = VersionDetector(self.context.source_dsn)
            if not source_detector.connect():
                self.logger.error("Cannot connect to source database")
                return False
            source_detector.disconnect()
            self.logger.success("Connected to source database")

            # Test target connection - create database if it doesn't exist
            target_detector = VersionDetector(self.context.target_dsn)
            if not target_detector.connect():
                # Try to create the database
                self.logger.info("Target database not found, attempting to create...")
                if self._create_target_database_from_dsn():
                    # Try again
                    target_detector = VersionDetector(self.context.target_dsn)
                    if not target_detector.connect():
                        self.logger.error("Cannot connect to target database after creation")
                        return False
                else:
                    self.logger.error("Cannot connect to target database")
                    return False
            target_detector.disconnect()
            self.logger.success("Connected to target database")

            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def _create_target_database_from_dsn(self) -> bool:
        """Create the target database by parsing DSN and connecting to postgres db."""
        try:
            import psycopg2
            from psycopg2 import sql
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

            # Parse target DSN
            target_parts = {}
            for part in self.context.target_dsn.split():
                if '=' in part:
                    key, value = part.split('=', 1)
                    target_parts[key] = value

            dbname = target_parts.get('dbname', target_parts.get('database', 'postgres'))
            owner = target_parts.get('user', 'postgres')

            # Create DSN for postgres database
            postgres_dsn = self.context.target_dsn.replace(f"dbname={dbname}", "dbname=postgres")
            postgres_dsn = postgres_dsn.replace(f"database={dbname}", "database=postgres")

            # Connect to postgres database
            admin_conn = psycopg2.connect(postgres_dsn)
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            with admin_conn.cursor() as cur:
                # Create the database
                cur.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(dbname),
                        sql.Identifier(owner)
                    )
                )

            admin_conn.close()
            self.logger.success(f"Created target database: {dbname}")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to create database: {e}")
            return False

    def _step_detect(self) -> bool:
        """Detect PostgreSQL versions."""
        try:
            # Detect source version
            with VersionDetector(self.context.source_dsn) as detector:
                self.context.source_version = detector.detect_version()

                if not self.context.source_version:
                    self.logger.error("Could not detect source version")
                    return False

                is_valid, msg = detector.validate_source_version(self.context.source_version)
                if not is_valid:
                    self.logger.error(msg)
                    return False

                self.logger.success(f"Source: {self.context.source_version}")

            # Detect target version
            with VersionDetector(self.context.target_dsn) as detector:
                self.context.target_version = detector.detect_version()

                if not self.context.target_version:
                    self.logger.error("Could not detect target version")
                    return False

                is_valid, msg = detector.validate_target_version(self.context.target_version)
                if not is_valid:
                    self.logger.error(msg)
                    return False

                self.logger.success(f"Target: {self.context.target_version}")

                # Validate upgrade path
                is_valid, msg = detector.validate_upgrade_path(
                    self.context.source_version,
                    self.context.target_version
                )
                if not is_valid:
                    self.logger.error(msg)
                    return False

                self.logger.info(msg)  # Log the upgrade path info

            return True
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            return False

    def _step_analyze(self) -> bool:
        """Analyze compatibility."""
        try:
            if not self.context.source_version:
                return False

            with CompatibilityAnalyzer(
                self.context.source_dsn,
                self.context.source_version.major
            ) as analyzer:
                self.context.analysis_result = analyzer.analyze()

            result = self.context.analysis_result
            self.logger.info(f"Analyzed {result.tables_analyzed} tables in {result.schemas_analyzed} schemas")

            if result.critical_count > 0:
                self.logger.warning(f"Found {result.critical_count} critical issues")
            if result.warning_count > 0:
                self.logger.info(f"Found {result.warning_count} warnings")
            if len(result.opportunities) > 0:
                self.logger.info(f"Found {len(result.opportunities)} optimization opportunities")

            return True
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            return False

    def _step_prepare(self) -> bool:
        """
        Prepare target database for migration.
        If target database exists, drop it and recreate.
        If target database doesn't exist, create it.
        """
        try:
            self.logger.info("Preparing target database...")

            success, message = prepare_target_db_from_dsn(
                self.context.target_dsn,
                drop_if_exists=True,
            )

            if success:
                self.logger.success(message)
            else:
                self.logger.error(message)

            return success
        except Exception as e:
            self.logger.error(f"Prepare error: {e}")
            return False

    def _step_backup(self) -> bool:
        """Create database backup."""
        try:
            ensure_directory(self.context.backup_dir)
            backup_name = generate_backup_name()
            self.context.backup_path = self.context.backup_dir / f"{backup_name}.dump"

            migrator = DumpRestoreMigrator(
                source_dsn=self.context.source_dsn,
                target_dsn=self.context.target_dsn,
            )

            success, message = migrator.dump(
                self.context.backup_path,
                progress_callback=lambda msg: self.logger.info(msg),
            )

            if success:
                self.logger.success(f"Backup created: {self.context.backup_path}")
            else:
                self.logger.error(f"Backup failed: {message}")

            return success
        except Exception as e:
            self.logger.error(f"Backup error: {e}")
            return False

    def _step_migrate(self) -> bool:
        """Perform the migration."""
        try:
            if self.context.method == MigrationMethod.PYTHON:
                return self._migrate_python()
            elif self.context.method == MigrationMethod.DUMP_RESTORE:
                return self._migrate_dump_restore()
            else:
                return self._migrate_pg_upgrade()
        except Exception as e:
            self.logger.error(f"Migration error: {e}")
            return False

    def _migrate_python(self) -> bool:
        """Migrate using pure Python with psycopg2 (no pg_dump dependency)."""
        self.logger.info("Using pure Python migration (psycopg2)...")

        migrator = PythonMigrator(
            source_dsn=self.context.source_dsn,
            target_dsn=self.context.target_dsn,
            progress_callback=lambda msg, cur, tot: self.logger.info(msg),
        )

        success, message = migrator.run_migration()

        if success:
            self.logger.success("Migration completed")
        else:
            self.logger.error(f"Migration failed: {message}")

        return success

    def _migrate_dump_restore(self) -> bool:
        """Migrate using dump/restore method."""
        if not self.context.backup_path or not self.context.backup_path.exists():
            self.logger.error("Backup not found")
            return False

        migrator = DumpRestoreMigrator(
            source_dsn=self.context.source_dsn,
            target_dsn=self.context.target_dsn,
        )

        success, message = migrator.restore(
            self.context.backup_path,
            jobs=self.context.parallel_jobs,
            progress_callback=lambda msg: self.logger.info(msg),
        )

        if success:
            self.logger.success("Migration completed")
        else:
            self.logger.error(f"Migration failed: {message}")

        return success

    def _migrate_pg_upgrade(self) -> bool:
        """Migrate using pg_upgrade method."""
        self.logger.warning("pg_upgrade migration requires manual configuration")
        self.logger.info("Please use dump/restore method or configure pg_upgrade manually")
        return False

    def _step_validate(self) -> bool:
        """Validate the migration."""
        try:
            # Connect to target and verify
            with VersionDetector(self.context.target_dsn) as detector:
                version = detector.detect_version()

                if not version:
                    self.logger.error("Cannot connect to migrated database")
                    return False

                self.logger.success(f"Target database accessible: {version}")

            # Additional validation could be added here
            # - Table counts
            # - Row counts for key tables
            # - Constraint checks

            return True
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Get migration summary."""
        return {
            "state": self.context.state.value,
            "source_version": str(self.context.source_version) if self.context.source_version else None,
            "target_version": str(self.context.target_version) if self.context.target_version else None,
            "method": self.context.method.value,
            "duration": self.context.timer.formatted,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "error": s.error,
                }
                for s in self.context.steps
            ],
            "analysis": self.context.analysis_result.get_summary() if self.context.analysis_result else None,
        }
