"""
pg_upgrade wrapper for PostgreSQL 18 migration.
Leverages new PG18 features: --jobs, --swap, and planner statistics preservation.
"""

import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple


class UpgradeMode(Enum):
    """pg_upgrade execution modes."""
    CHECK = "check"     # Check only, don't upgrade
    UPGRADE = "upgrade"  # Perform the upgrade
    LINK = "link"       # Use hard links (faster, but modifies old cluster)


@dataclass
class UpgradeConfig:
    """Configuration for pg_upgrade execution."""
    old_bindir: Path
    new_bindir: Path
    old_datadir: Path
    new_datadir: Path
    old_port: int = 5432
    new_port: int = 5433
    jobs: int = 4
    use_link: bool = False
    use_swap: bool = True
    preserve_stats: bool = True
    username: str = "postgres"


@dataclass
class UpgradeResult:
    """Result of pg_upgrade execution."""
    success: bool
    return_code: int
    stdout: str
    stderr: str
    logs_path: Optional[Path] = None

    @property
    def error_summary(self) -> Optional[str]:
        """Extract error summary from stderr."""
        if self.success:
            return None

        lines = self.stderr.strip().split("\n")
        # Return last few lines as error summary
        return "\n".join(lines[-5:]) if lines else "Unknown error"


class PgUpgradeWrapper:
    """Wrapper for pg_upgrade tool with PG18 feature support."""

    def __init__(self, config: UpgradeConfig):
        """
        Initialize pg_upgrade wrapper.
        
        Args:
            config: Upgrade configuration
        """
        self.config = config
        self._pg_upgrade_path: Optional[Path] = None

    def find_pg_upgrade(self) -> Optional[Path]:
        """
        Find pg_upgrade binary.
        
        Returns:
            Path to pg_upgrade or None if not found
        """
        # Try new bindir first
        new_path = self.config.new_bindir / "pg_upgrade"
        if new_path.exists():
            self._pg_upgrade_path = new_path
            return new_path

        # Try system path
        system_path = shutil.which("pg_upgrade")
        if system_path:
            self._pg_upgrade_path = Path(system_path)
            return self._pg_upgrade_path

        return None

    def build_command(self, mode: UpgradeMode = UpgradeMode.UPGRADE) -> List[str]:
        """
        Build pg_upgrade command with all arguments.
        
        Args:
            mode: Upgrade mode (check, upgrade, link)
            
        Returns:
            List of command arguments
        """
        if not self._pg_upgrade_path:
            self.find_pg_upgrade()

        if not self._pg_upgrade_path:
            raise RuntimeError("pg_upgrade not found")

        cmd = [
            str(self._pg_upgrade_path),
            "--old-bindir", str(self.config.old_bindir),
            "--new-bindir", str(self.config.new_bindir),
            "--old-datadir", str(self.config.old_datadir),
            "--new-datadir", str(self.config.new_datadir),
            "--old-port", str(self.config.old_port),
            "--new-port", str(self.config.new_port),
            "--username", self.config.username,
        ]

        # PG18 specific: parallel jobs
        if self.config.jobs > 1:
            cmd.extend(["--jobs", str(self.config.jobs)])

        # PG18 specific: use swap for faster directory operations
        if self.config.use_swap:
            cmd.append("--swap")

        # Mode-specific options
        if mode == UpgradeMode.CHECK:
            cmd.append("--check")
        elif mode == UpgradeMode.LINK:
            cmd.append("--link")
        elif self.config.use_link:
            cmd.append("--link")

        return cmd

    def check(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> UpgradeResult:
        """
        Run pg_upgrade in check mode.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            UpgradeResult
        """
        return self._run(UpgradeMode.CHECK, progress_callback)

    def upgrade(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> UpgradeResult:
        """
        Run pg_upgrade to perform migration.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            UpgradeResult
        """
        return self._run(UpgradeMode.UPGRADE, progress_callback)

    def _run(
        self,
        mode: UpgradeMode,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> UpgradeResult:
        """
        Execute pg_upgrade command.
        
        Args:
            mode: Upgrade mode
            progress_callback: Optional callback for progress updates
            
        Returns:
            UpgradeResult
        """
        try:
            cmd = self.build_command(mode)

            if progress_callback:
                progress_callback(f"Running: {' '.join(cmd[:3])}...")

            # Run with subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.config.new_datadir.parent),
            )

            stdout_lines = []
            stderr_lines = []

            # Stream output
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    stdout_lines.append(line)
                    if progress_callback and line.strip():
                        progress_callback(line.strip())

            process.wait()

            # Read any remaining stderr
            stderr = ""
            if process.stderr:
                stderr = process.stderr.read()
                stderr_lines.append(stderr)

            return UpgradeResult(
                success=process.returncode == 0,
                return_code=process.returncode,
                stdout="".join(stdout_lines),
                stderr="".join(stderr_lines),
                logs_path=self.config.new_datadir.parent / "pg_upgrade_output.d",
            )

        except FileNotFoundError:
            return UpgradeResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="pg_upgrade not found. Please ensure PostgreSQL 18 is installed.",
            )
        except Exception as e:
            return UpgradeResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
            )

    def validate_paths(self) -> Tuple[bool, List[str]]:
        """
        Validate all required paths exist.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not self.config.old_bindir.exists():
            errors.append(f"Old bindir not found: {self.config.old_bindir}")

        if not self.config.new_bindir.exists():
            errors.append(f"New bindir not found: {self.config.new_bindir}")

        if not self.config.old_datadir.exists():
            errors.append(f"Old datadir not found: {self.config.old_datadir}")

        if not self.config.new_datadir.exists():
            errors.append(f"New datadir not found: {self.config.new_datadir}")

        if not self.find_pg_upgrade():
            errors.append("pg_upgrade binary not found")

        return len(errors) == 0, errors


class DumpRestoreMigrator:
    """
    Alternative migration method using pg_dump/pg_restore.
    Useful when pg_upgrade is not available or not suitable.
    """

    def __init__(
        self,
        source_dsn: str,
        target_dsn: str,
        pg_dump_path: Optional[Path] = None,
        pg_restore_path: Optional[Path] = None,
    ):
        """
        Initialize dump/restore migrator.
        
        Args:
            source_dsn: Source database connection string
            target_dsn: Target database connection string
            pg_dump_path: Path to pg_dump binary
            pg_restore_path: Path to pg_restore binary
        """
        self.source_dsn = source_dsn
        self.target_dsn = target_dsn
        self.pg_dump_path = pg_dump_path or Path(shutil.which("pg_dump") or "pg_dump")
        self.pg_restore_path = pg_restore_path or Path(shutil.which("pg_restore") or "pg_restore")

    def dump(
        self,
        output_path: Path,
        format: str = "custom",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Dump source database.
        
        Args:
            output_path: Path for dump file
            format: Dump format (custom, directory, tar, plain)
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (success, message)
        """
        cmd = [
            str(self.pg_dump_path),
            f"--dbname={self.source_dsn}",
            f"--format={format[0]}",  # c, d, t, or p
            f"--file={output_path}",
            "--verbose",
        ]

        if progress_callback:
            progress_callback("Starting database dump...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True, f"Dump completed: {output_path}"
            else:
                return False, result.stderr

        except Exception as e:
            return False, str(e)

    def restore(
        self,
        dump_path: Path,
        jobs: int = 4,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Restore to target database.
        
        Args:
            dump_path: Path to dump file
            jobs: Number of parallel restore jobs
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (success, message)
        """
        cmd = [
            str(self.pg_restore_path),
            f"--dbname={self.target_dsn}",
            f"--jobs={jobs}",
            "--verbose",
            str(dump_path),
        ]

        if progress_callback:
            progress_callback("Starting database restore...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            # pg_restore may return non-zero on warnings
            if result.returncode == 0 or "error" not in result.stderr.lower():
                return True, "Restore completed successfully"
            else:
                return False, result.stderr

        except Exception as e:
            return False, str(e)
