"""
PostgreSQL version detection module.
Auto-detects PostgreSQL versions 14, 15, 16, 17 and validates for migration to 18.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extensions import connection


class PostgreSQLVersion(Enum):
    """Supported PostgreSQL versions."""
    PG14 = 14
    PG15 = 15
    PG16 = 16
    PG17 = 17
    PG18 = 18

    @classmethod
    def from_major(cls, major: int) -> Optional["PostgreSQLVersion"]:
        """Get version enum from major version number."""
        for version in cls:
            if version.value == major:
                return version
        return None

    @classmethod
    def supported_versions(cls) -> list:
        """Get list of all supported major versions."""
        return [v.value for v in cls]

    @classmethod
    def min_version(cls) -> int:
        """Get minimum supported version."""
        return min(v.value for v in cls)

    @classmethod
    def max_version(cls) -> int:
        """Get maximum supported version (latest)."""
        return max(v.value for v in cls)

    def is_source_supported(self) -> bool:
        """Check if this version is supported as a migration source."""
        # Any version except the latest can be a source
        return self.value < PostgreSQLVersion.max_version()

    def can_upgrade_to(self, target_version: "PostgreSQLVersion") -> bool:
        """Check if this version can upgrade to the target version."""
        return self.value < target_version.value


@dataclass
class VersionInfo:
    """Detailed PostgreSQL version information."""
    major: int
    minor: int
    patch: int
    full_version_string: str
    server_encoding: str
    is_superuser: bool
    data_directory: Optional[str] = None

    @property
    def version_tuple(self) -> Tuple[int, int, int]:
        """Get version as tuple for comparison."""
        return (self.major, self.minor, self.patch)

    @property
    def enum_version(self) -> Optional[PostgreSQLVersion]:
        """Get corresponding version enum."""
        return PostgreSQLVersion.from_major(self.major)

    def can_upgrade_to(self, target: "VersionInfo") -> bool:
        """Check if this version can upgrade to target version."""
        return self.major < target.major

    def __str__(self) -> str:
        return f"PostgreSQL {self.major}.{self.minor}.{self.patch}"


class VersionDetector:
    """Detects PostgreSQL version from a database connection."""

    # Regex to parse PostgreSQL version string
    # Examples: "PostgreSQL 16.1", "PostgreSQL 17.0 (Ubuntu 17.0-1.pgdg22.04+1)"
    VERSION_PATTERN = re.compile(
        r"PostgreSQL\s+(\d+)\.(\d+)(?:\.(\d+))?",
        re.IGNORECASE
    )

    def __init__(self, dsn: str):
        """
        Initialize detector with database connection string.
        
        Args:
            dsn: PostgreSQL connection string
        """
        self.dsn = dsn
        self._connection: Optional[connection] = None

    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self._connection = psycopg2.connect(self.dsn)
            return True
        except OperationalError:
            return False

    def disconnect(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def detect_version(self) -> Optional[VersionInfo]:
        """
        Detect PostgreSQL version from connected server.
        
        Returns:
            VersionInfo object if successful, None otherwise.
        """
        if not self._connection:
            if not self.connect() or not self._connection:
                return None

        try:
            with self._connection.cursor() as cursor:
                # Get version string
                cursor.execute("SELECT version()")
                res_ver = cursor.fetchone()
                if not res_ver:
                    return None
                version_string = res_ver[0]

                # Parse version
                match = self.VERSION_PATTERN.search(version_string)
                if not match:
                    return None

                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3)) if match.group(3) else 0

                # Get server encoding
                cursor.execute("SHOW server_encoding")
                res_enc = cursor.fetchone()
                encoding = res_enc[0] if res_enc else "UTF8"

                # Check if superuser
                cursor.execute("SELECT current_setting('is_superuser')")
                res_sup = cursor.fetchone()
                is_superuser = res_sup[0] == 'on' if res_sup else False

                # Try to get data directory (requires superuser)
                data_dir = None
                if is_superuser:
                    try:
                        cursor.execute("SHOW data_directory")
                        res_dir = cursor.fetchone()
                        data_dir = res_dir[0] if res_dir else None
                    except Exception:
                        pass

                return VersionInfo(
                    major=major,
                    minor=minor,
                    patch=patch,
                    full_version_string=version_string,
                    server_encoding=encoding,
                    is_superuser=is_superuser,
                    data_directory=data_dir
                )
        except Exception:
            return None

    def validate_source_version(self, version_info: VersionInfo) -> Tuple[bool, str]:
        """
        Validate if detected version is supported as migration source.
        
        Args:
            version_info: Detected version information
            
        Returns:
            Tuple of (is_valid, message)
        """
        min_ver = PostgreSQLVersion.min_version()
        max_ver = PostgreSQLVersion.max_version()

        if version_info.major < min_ver:
            return False, f"PostgreSQL {version_info.major} is too old. Minimum supported: {min_ver}"

        if version_info.major > max_ver:
            return False, f"PostgreSQL {version_info.major} is not yet supported"

        return True, f"PostgreSQL {version_info.major} is supported for migration"

    def validate_target_version(self, version_info: VersionInfo) -> Tuple[bool, str]:
        """
        Validate if detected version is valid as migration target.
        
        Args:
            version_info: Detected version information
            
        Returns:
            Tuple of (is_valid, message)
        """
        min_ver = PostgreSQLVersion.min_version()
        max_ver = PostgreSQLVersion.max_version()

        if version_info.major < min_ver:
            return False, f"Target PostgreSQL {version_info.major} is too old. Minimum: {min_ver}"

        if version_info.major > max_ver:
            return False, f"Target PostgreSQL {version_info.major} is not yet supported"

        return True, f"Target PostgreSQL {version_info.major} is valid"

    def validate_upgrade_path(
        self,
        source: VersionInfo,
        target: VersionInfo
    ) -> Tuple[bool, str]:
        """
        Validate the migration path from source to target.
        Supports upgrades (14→18), same major version (14.x→14.x), but not downgrades.
        
        Args:
            source: Source version info
            target: Target version info
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check for downgrade
        if source.major > target.major:
            return False, f"Cannot downgrade from PG {source.major} to PG {target.major}. Downgrades are not supported."

        # Same major version migration (e.g., 14.5 → 14.11)
        if source.major == target.major:
            if source.version_tuple > target.version_tuple:
                return False, f"Cannot downgrade from {source} to {target}. Target must be same or newer version."
            elif source.version_tuple == target.version_tuple:
                return True, f"Database copy: PostgreSQL {source} → {target} (same version)"
            else:
                return True, f"Minor upgrade: PostgreSQL {source} → {target}"

        # Major version upgrade
        version_jump = target.major - source.major
        return True, f"Major upgrade: PostgreSQL {source.major} → {target.major} (jump of {version_jump} major version(s))"

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


def detect_version_from_dsn(dsn: str) -> Optional[VersionInfo]:
    """
    Convenience function to detect PostgreSQL version from DSN.
    
    Args:
        dsn: PostgreSQL connection string
        
    Returns:
        VersionInfo if successful, None otherwise
    """
    with VersionDetector(dsn) as detector:
        result = detector.detect_version()
        return result
