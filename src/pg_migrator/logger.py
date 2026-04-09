"""
Rich-integrated logging for PostgreSQL Migrator.
Provides beautiful colored console output with file logging support.
"""

import logging
import queue
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from .ui.theme import get_theme


class GUILogHandler(logging.Handler):
    """Handler that strips Rich markup and sends clean text to a GUI queue."""
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            # Use rich Text to parse and strip markup safely
            clean_msg = Text.from_markup(msg).plain
            self.log_queue.put(("log", record.levelname, clean_msg))
        except Exception:
            self.handleError(record)


class MigrationLogger:
    """Custom logger with Rich integration."""

    def __init__(
        self,
        name: str = "pg_migrator",
        level: str = "INFO",
        log_file: Optional[Path] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize the migration logger.
        
        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for logging
            console: Optional Rich console instance
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers.clear()

        # Rich console handler
        self.console = console or Console(theme=get_theme())
        rich_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
        )
        rich_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(rich_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            self.logger.addHandler(file_handler)
            self.log_file: Optional[Path] = log_file
        else:
            self.log_file = None

    def add_gui_handler(self, log_queue: queue.Queue):
        """Attach a GUI queue handler to stream stripped logs."""
        gui_handler = GUILogHandler(log_queue)
        self.logger.addHandler(gui_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(f"[dim]{message}[/dim]", **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(f"[pg.accent]{message}[/pg.accent]", **kwargs)

    def success(self, message: str, **kwargs):
        """Log success message with green styling."""
        self.logger.info(f"[status.success]✓ {message}[/status.success]", **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(f"[status.warning]⚠ {message}[/status.warning]", **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(f"[status.error]✗ {message}[/status.error]", **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(f"[bold status.error]✗ CRITICAL: {message}[/bold status.error]", **kwargs)

    def step(self, step_num: int, total: int, message: str):
        """Log a migration step."""
        self.logger.info(
            f"[pg.highlight]Step {step_num}/{total}:[/pg.highlight] [pg.accent]{message}[/pg.accent]"
        )

    def section(self, title: str):
        """Log a section header."""
        self.console.rule(f"[bold pg.primary]{title}[/bold pg.primary]")

    def migration_start(self, source_version: int, target_version: int = 18):
        """Log migration start."""
        self.section("Migration Started")
        self.info(f"Source: PostgreSQL {source_version}")
        self.info(f"Target: PostgreSQL {target_version}")
        self.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def migration_complete(self, duration: str, success: bool):
        """Log migration completion."""
        if success:
            self.section("Migration Completed")
            self.success(f"Migration completed successfully in {duration}")
        else:
            self.section("Migration Failed")
            self.error(f"Migration failed after {duration}")


# Global logger instance
_logger: Optional[MigrationLogger] = None


def get_logger(
    name: str = "pg_migrator",
    level: str = "INFO",
    log_file: Optional[Path] = None,
) -> MigrationLogger:
    """
    Get or create the migration logger.
    
    Args:
        name: Logger name
        level: Log level
        log_file: Optional log file path
        
    Returns:
        MigrationLogger instance
    """
    global _logger
    if _logger is None:
        _logger = MigrationLogger(name, level, log_file)
    return _logger
