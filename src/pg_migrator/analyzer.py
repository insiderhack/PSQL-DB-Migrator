"""
Compatibility Analyzer for PostgreSQL Migration.
Detects breaking changes, deprecations, and migration opportunities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extensions import connection


class IssueSeverity(Enum):
    """Severity levels for compatibility issues."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(Enum):
    """Categories of compatibility issues."""
    AUTHENTICATION = "Authentication"
    SCHEMA = "Schema"
    EXTENSION = "Extension"
    CONFIGURATION = "Configuration"
    DEPRECATED = "Deprecated"
    OPPORTUNITY = "Opportunity"
    DATA_TYPE = "Data Type"
    FUNCTION = "Function"


@dataclass
class CompatibilityIssue:
    """Represents a single compatibility issue."""
    severity: IssueSeverity
    category: IssueCategory
    message: str
    recommendation: str
    details: Optional[str] = None
    auto_fixable: bool = False
    pg_version_affected: Optional[List[int]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI display."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "recommendation": self.recommendation,
            "details": self.details,
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class AnalysisResult:
    """Results of compatibility analysis."""
    source_version: int
    target_version: int = 18
    issues: List[CompatibilityIssue] = field(default_factory=list)
    opportunities: List[CompatibilityIssue] = field(default_factory=list)
    schemas_analyzed: int = 0
    tables_analyzed: int = 0
    extensions_analyzed: int = 0

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)

    @property
    def has_blockers(self) -> bool:
        return self.critical_count > 0

    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            "source_version": self.source_version,
            "target_version": self.target_version,
            "critical": self.critical_count,
            "warnings": self.warning_count,
            "info": self.info_count,
            "opportunities": len(self.opportunities),
            "schemas": self.schemas_analyzed,
            "tables": self.tables_analyzed,
            "can_proceed": not self.has_blockers,
        }

    def to_report_dict(self) -> Dict[str, Any]:
        """Convert result to a comprehensive report dictionary."""
        return {
            "summary": self.get_summary(),
            "issues": [i.to_dict() for i in self.issues],
            "opportunities": [i.to_dict() for i in self.opportunities],
        }


class CompatibilityAnalyzer:
    """Analyzes PostgreSQL databases for migration compatibility."""

    # Known deprecated features by version
    DEPRECATIONS = {
        18: [
            ("MD5 authentication", "Switch to SCRAM-SHA-256 authentication"),
        ]
    }

    # Breaking changes by source -> target version
    BREAKING_CHANGES = {
        (14, 18): [
            ("VACUUM/ANALYZE inheritance behavior changed", "Review VACUUM/ANALYZE scripts for inheritance tables"),
            ("Default password encryption now SCRAM-SHA-256", "Verify all connections use SCRAM-SHA-256"),
        ],
        (15, 18): [
            ("PUBLIC schema permissions changed", "Review public schema access permissions"),
        ],
        (16, 18): [
            ("pg_stat_io view changes", "Update monitoring queries using pg_stat_io"),
        ],
        (17, 18): [
            ("Time zone abbreviation handling changed", "Review timezone-related queries"),
        ],
    }

    # Extensions that may need attention
    EXTENSION_NOTES = {
        "postgis": "Ensure PostGIS is compatible with PG18",
        "pg_stat_statements": "Reset statistics after migration",
        "pgcrypto": "MD5-based functions deprecated, use SHA variants",
        "timescaledb": "Check TimescaleDB PG18 compatibility",
    }

    def __init__(self, dsn: str, source_version: int):
        """
        Initialize analyzer.
        
        Args:
            dsn: Database connection string
            source_version: Source PostgreSQL major version
        """
        self.dsn = dsn
        self.source_version = source_version
        self._connection: Optional[connection] = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self._connection = psycopg2.connect(self.dsn)
            return True
        except Exception:
            return False

    def disconnect(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def analyze(self) -> AnalysisResult:
        """
        Run full compatibility analysis.
        
        Returns:
            AnalysisResult with all findings
        """
        result = AnalysisResult(source_version=self.source_version)

        if not self._connection:
            if not self.connect() or not self._connection:
                result.issues.append(CompatibilityIssue(
                    severity=IssueSeverity.CRITICAL,
                    category=IssueCategory.CONFIGURATION,
                    message="Cannot connect to database",
                    recommendation="Verify connection parameters and database availability",
                ))
                return result

        # Run all checks
        self._check_authentication(result)
        self._check_breaking_changes(result)
        self._check_deprecations(result)
        self._check_extensions(result)
        self._check_schemas(result)
        self._check_data_types(result)
        self._check_opportunities(result)

        return result

    def _check_authentication(self, result: AnalysisResult):
        """Check for authentication-related issues."""
        if not self._connection:
            return

        try:
            with self._connection.cursor() as cursor:
                # Check for MD5 password users
                cursor.execute("""
                    SELECT count(*) FROM pg_catalog.pg_authid 
                    WHERE rolpassword LIKE 'md5%'
                """)
                res = cursor.fetchone()
                md5_count = res[0] if res else 0

                if md5_count > 0:
                    result.issues.append(CompatibilityIssue(
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.AUTHENTICATION,
                        message=f"Found {md5_count} users with MD5 password hashing",
                        recommendation="Migrate users to SCRAM-SHA-256 before upgrade",
                        details="MD5 authentication is deprecated in PostgreSQL 18",
                        auto_fixable=False,
                    ))
        except Exception:
            pass  # May not have permission to check

    def _check_breaking_changes(self, result: AnalysisResult):
        """Check for known breaking changes."""
        for (src, tgt), changes in self.BREAKING_CHANGES.items():
            if self.source_version <= src:
                for message, recommendation in changes:
                    result.issues.append(CompatibilityIssue(
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.CONFIGURATION,
                        message=message,
                        recommendation=recommendation,
                        pg_version_affected=[src],
                    ))

    def _check_deprecations(self, result: AnalysisResult):
        """Check for deprecated features."""
        for version, deprecations in self.DEPRECATIONS.items():
            if version > self.source_version:
                for feature, recommendation in deprecations:
                    result.issues.append(CompatibilityIssue(
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.DEPRECATED,
                        message=f"Deprecated: {feature}",
                        recommendation=recommendation,
                    ))

    def _check_extensions(self, result: AnalysisResult):
        """Check installed extensions."""
        if not self._connection:
            return
            
        try:
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    SELECT extname, extversion 
                    FROM pg_extension 
                    WHERE extname != 'plpgsql'
                """)
                extensions = cursor.fetchall()
                result.extensions_analyzed = len(extensions)

                for ext_name, ext_version in extensions:
                    if ext_name in self.EXTENSION_NOTES:
                        result.issues.append(CompatibilityIssue(
                            severity=IssueSeverity.INFO,
                            category=IssueCategory.EXTENSION,
                            message=f"Extension: {ext_name} v{ext_version}",
                            recommendation=self.EXTENSION_NOTES[ext_name],
                        ))
        except Exception:
            pass

    def _check_schemas(self, result: AnalysisResult):
        """Check schema structure."""
        if not self._connection:
            return

        try:
            with self._connection.cursor() as cursor:
                # Count schemas
                cursor.execute("""
                    SELECT count(*) FROM information_schema.schemata 
                    WHERE schema_name NOT LIKE 'pg_%' 
                    AND schema_name != 'information_schema'
                """)
                res_schemas = cursor.fetchone()
                result.schemas_analyzed = res_schemas[0] if res_schemas else 0

                # Count tables
                cursor.execute("""
                    SELECT count(*) FROM information_schema.tables 
                    WHERE table_schema NOT LIKE 'pg_%' 
                    AND table_schema != 'information_schema'
                    AND table_type = 'BASE TABLE'
                """)
                res_tables = cursor.fetchone()
                result.tables_analyzed = res_tables[0] if res_tables else 0
        except Exception:
            pass

    def _check_data_types(self, result: AnalysisResult):
        """Check for data type considerations."""
        if not self._connection:
            return

        try:
            with self._connection.cursor() as cursor:
                # Check for UUID columns (opportunity for UUIDv7)
                cursor.execute("""
                    SELECT count(*) FROM information_schema.columns 
                    WHERE data_type = 'uuid'
                    AND table_schema NOT LIKE 'pg_%'
                """)
                res_uuid = cursor.fetchone()
                uuid_count = res_uuid[0] if res_uuid else 0

                if uuid_count > 0:
                    result.opportunities.append(CompatibilityIssue(
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.OPPORTUNITY,
                        message=f"Found {uuid_count} UUID columns",
                        recommendation="Consider migrating to UUIDv7 for better performance",
                        details="PostgreSQL 18 supports UUIDv7 with native generation",
                    ))
        except Exception:
            pass

    def _check_opportunities(self, result: AnalysisResult):
        """Check for migration opportunities and optimizations."""
        # Always suggest these PG18 features
        result.opportunities.append(CompatibilityIssue(
            severity=IssueSeverity.INFO,
            category=IssueCategory.OPPORTUNITY,
            message="Async I/O subsystem available",
            recommendation="Enable AIO for 2-3x read performance improvement",
        ))

        result.opportunities.append(CompatibilityIssue(
            severity=IssueSeverity.INFO,
            category=IssueCategory.OPPORTUNITY,
            message="Planner statistics preserved during upgrade",
            recommendation="No post-upgrade ANALYZE needed with pg_upgrade",
        ))

        result.opportunities.append(CompatibilityIssue(
            severity=IssueSeverity.INFO,
            category=IssueCategory.OPPORTUNITY,
            message="Data checksums enabled by default",
            recommendation="Verify data integrity with built-in checksums",
        ))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


def analyze_compatibility(dsn: str, source_version: int) -> AnalysisResult:
    """
    Convenience function to run compatibility analysis.
    
    Args:
        dsn: Database connection string
        source_version: Source PostgreSQL major version
        
    Returns:
        AnalysisResult
    """
    with CompatibilityAnalyzer(dsn, source_version) as analyzer:
        res = analyzer.analyze()
        return res
