"""
Configuration management using Pydantic Settings.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database connection configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Source Database (PG 14-17)
    source_db_host: str = Field(default="localhost", alias="SOURCE_DB_HOST")
    source_db_port: int = Field(default=5432, alias="SOURCE_DB_PORT")
    source_db_name: str = Field(default="postgres", alias="SOURCE_DB_NAME")
    source_db_user: str = Field(default="postgres", alias="SOURCE_DB_USER")
    source_db_password: str = Field(default="", alias="SOURCE_DB_PASSWORD")
    
    # Target Database (PG 18)
    target_db_host: str = Field(default="localhost", alias="TARGET_DB_HOST")
    target_db_port: int = Field(default=5433, alias="TARGET_DB_PORT")
    target_db_name: str = Field(default="postgres", alias="TARGET_DB_NAME")
    target_db_user: str = Field(default="postgres", alias="TARGET_DB_USER")
    target_db_password: str = Field(default="", alias="TARGET_DB_PASSWORD")
    
    def get_source_dsn(self) -> str:
        """Get source database connection string."""
        return (
            f"host={self.source_db_host} "
            f"port={self.source_db_port} "
            f"dbname={self.source_db_name} "
            f"user={self.source_db_user} "
            f"password={self.source_db_password}"
        )
    
    def get_target_dsn(self) -> str:
        """Get target database connection string."""
        return (
            f"host={self.target_db_host} "
            f"port={self.target_db_port} "
            f"dbname={self.target_db_name} "
            f"user={self.target_db_user} "
            f"password={self.target_db_password}"
        )


class MigrationConfig(BaseSettings):
    """Migration options configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="MIGRATION_",
        case_sensitive=False,
        extra="ignore"
    )
    
    parallel_jobs: int = Field(default=4, description="Number of parallel jobs for pg_upgrade")
    preserve_stats: bool = Field(default=True, description="Preserve planner statistics")
    use_swap: bool = Field(default=True, description="Use --swap flag for pg_upgrade")
    create_backup: bool = Field(default=True, description="Create backup before migration")
    backup_dir: Path = Field(default=Path("./backups"), description="Backup directory")


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False,
        extra="ignore"
    )
    
    level: str = Field(default="INFO")
    file: Optional[Path] = Field(default=None)
    console_rich: bool = Field(default=True, description="Use Rich console for logging")


class AppConfig:
    """Application configuration aggregator."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.migration = MigrationConfig()
        self.logging = LoggingConfig()
    
    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "AppConfig":
        """Load configuration from environment file."""
        from dotenv import load_dotenv
        
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()  # Try default .env
        
        return cls()


# Singleton config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create the application configuration."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config
