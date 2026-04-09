"""
Utility functions for PostgreSQL Migrator.
"""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


def parse_dsn(dsn: str) -> Dict[str, str]:
    """
    Parse a PostgreSQL DSN string to dictionary.
    
    Args:
        dsn: Connection string like "host=localhost port=5432 dbname=mydb"
        
    Returns:
        Dictionary with connection parameters
    """
    result = {}
    pattern = re.compile(r"(\w+)=([^\s]+)")

    for match in pattern.finditer(dsn):
        key = match.group(1)
        value = match.group(2)
        result[key] = value

    return result


def build_dsn(
    host: str = "localhost",
    port: int = 5432,
    dbname: str = "postgres",
    user: str = "postgres",
    password: Optional[str] = None,
) -> str:
    """
    Build a PostgreSQL DSN string from components.
    
    Args:
        host: Database host
        port: Database port
        dbname: Database name
        user: Username
        password: Password (optional)
        
    Returns:
        DSN connection string
    """
    parts = [
        f"host={host}",
        f"port={port}",
        f"dbname={dbname}",
        f"user={user}",
    ]

    if password:
        parts.append(f"password={password}")

    return " ".join(parts)


def format_bytes(num_bytes: float) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        num_bytes: Number of bytes
        
    Returns:
        Formatted string like "1.5 GB"
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format seconds to human-readable duration.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        Formatted string like "2h 15m 30s"
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def estimate_migration_time(
    db_size_bytes: int,
    table_count: int,
    index_count: int = 0,
) -> Tuple[int, int]:
    """
    Estimate migration time range.
    
    Args:
        db_size_bytes: Database size in bytes
        table_count: Number of tables
        index_count: Number of indexes
        
    Returns:
        Tuple of (min_seconds, max_seconds)
    """
    # Base estimates (very rough)
    # Assume ~50 MB/s for pg_dump, ~30 MB/s for pg_restore
    size_gb = db_size_bytes / (1024 ** 3)

    # Base time for data
    min_data_time = int(size_gb * 20)  # 50 MB/s
    max_data_time = int(size_gb * 60)  # 17 MB/s

    # Add time for tables
    min_table_time = table_count * 1
    max_table_time = table_count * 5

    # Add time for indexes
    min_index_time = index_count * 2
    max_index_time = index_count * 10

    min_total = max(60, min_data_time + min_table_time + min_index_time)
    max_total = max(300, max_data_time + max_table_time + max_index_time)

    return (min_total, max_total)


class Timer:
    """Simple timer for tracking duration."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self):
        """Start the timer."""
        self.start_time = time.time()
        self.end_time = None

    def stop(self) -> float:
        """Stop the timer and return elapsed seconds."""
        self.end_time = time.time()
        return self.elapsed

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0

        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def formatted(self) -> str:
        """Get formatted elapsed time."""
        return format_duration(self.elapsed)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, creating if necessary.
    
    Args:
        path: Path to directory
        
    Returns:
        The path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_backup_name(prefix: str = "pg_backup") -> str:
    """
    Generate a timestamped backup name.
    
    Args:
        prefix: Backup name prefix
        
    Returns:
        Backup name like "pg_backup_20240128_143052"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def mask_password(dsn: str) -> str:
    """
    Mask password in DSN string for logging.
    
    Args:
        dsn: DSN with potential password
        
    Returns:
        DSN with password masked
    """
    return re.sub(r"password=\S+", "password=****", dsn)


def validate_connection_params(
    host: str,
    port: int,
    dbname: str,
    user: str,
) -> Tuple[bool, Optional[str]]:
    """
    Validate connection parameters.
    
    Args:
        host: Database host
        port: Database port
        dbname: Database name
        user: Username
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not host:
        return False, "Host is required"

    if not 1 <= port <= 65535:
        return False, "Port must be between 1 and 65535"

    if not dbname:
        return False, "Database name is required"

    if not user:
        return False, "Username is required"

    return True, None
