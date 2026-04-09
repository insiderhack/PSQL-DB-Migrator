"""
PostgreSQL Migrator - Main CLI Entry Point
Interactive migration from PostgreSQL 14, 15, 16, 17 to PostgreSQL 18.
"""

import sys

import click

from . import __version__
from .analyzer import analyze_compatibility
from .detector import VersionDetector
from .logger import get_logger
from .migrator import MigrationContext, MigrationEngine, MigrationMethod
from .ui.components import create_console, create_header
from .ui.screens import MigrationWizard
from .utils import build_dsn


def get_version_string() -> str:
    """Get formatted version string."""
    return f"PG Migrator v{__version__}"


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx: click.Context, version: bool):
    """
    🐘 PG Migrator - PostgreSQL Migration Tool
    
    Migrate your PostgreSQL database from version 14, 15, 16, or 17 to PostgreSQL 18
    with an interactive, visual wizard.
    
    Run without arguments to start the interactive migration wizard.
    """
    if version:
        console = create_console()
        console.print(f"[pg.primary]{get_version_string()}[/pg.primary]")
        sys.exit(0)

    # If no subcommand, run the interactive wizard
    if ctx.invoked_subcommand is None:
        ctx.invoke(migrate)


@cli.command()
@click.option("--source-host", default=None, help="Source database host (from .env: SOURCE_DB_HOST)")
@click.option("--source-port", default=None, type=int, help="Source database port (from .env: SOURCE_DB_PORT)")
@click.option("--source-db", default=None, help="Source database name (from .env: SOURCE_DB_NAME)")
@click.option("--source-user", default=None, help="Source database user (from .env: SOURCE_DB_USER)")
@click.option("--source-password", default=None, help="Source database password (from .env: SOURCE_DB_PASSWORD)")
@click.option("--target-host", default=None, help="Target database host (from .env: TARGET_DB_HOST)")
@click.option("--target-port", default=None, type=int, help="Target database port (from .env: TARGET_DB_PORT)")
@click.option("--target-db", default=None, help="Target database name (from .env: TARGET_DB_NAME)")
@click.option("--target-user", default=None, help="Target database user (from .env: TARGET_DB_USER)")
@click.option("--target-password", default=None, help="Target database password (from .env: TARGET_DB_PASSWORD)")
@click.option("--non-interactive", "-n", is_flag=True, help="Run in non-interactive mode using .env settings")
@click.option("--dry-run", is_flag=True, help="Perform checks without actual migration")
def migrate(
    source_host: str,
    source_port: int,
    source_db: str,
    source_user: str,
    source_password: str,
    target_host: str,
    target_port: int,
    target_db: str,
    target_user: str,
    target_password: str,
    non_interactive: bool,
    dry_run: bool,
):
    """
    Start the migration wizard.
    
    By default, reads connection settings from .env file.
    You can override any setting with CLI flags.
    
    This command launches a visual wizard that guides you through:
    
    \b
    1. Database connection configuration
    2. PostgreSQL version detection
    3. Compatibility analysis
    4. Target database preparation
    5. Backup creation
    6. Migration execution
    7. Validation
    
    Examples:
    
    \b
    # Non-interactive mode using .env settings:
    $ ./run.sh migrate -n
    
    \b
    # Override specific settings:
    $ ./run.sh migrate -n --source-port 5432 --target-port 5433
    
    \b
    # Dry run (no actual migration):
    $ ./run.sh migrate -n --dry-run
    """
    import os

    from dotenv import load_dotenv

    # Load .env file
    load_dotenv()

    console = create_console()

    # Get values from .env or use CLI overrides
    source_host = source_host or os.getenv("SOURCE_DB_HOST", "localhost")
    source_port = source_port or int(os.getenv("SOURCE_DB_PORT", "5432"))
    source_db = source_db or os.getenv("SOURCE_DB_NAME", "postgres")
    source_user = source_user or os.getenv("SOURCE_DB_USER", "postgres")
    source_password = source_password if source_password is not None else os.getenv("SOURCE_DB_PASSWORD", "")

    target_host = target_host or os.getenv("TARGET_DB_HOST", "localhost")
    target_port = target_port or int(os.getenv("TARGET_DB_PORT", "5433"))
    target_db = target_db or os.getenv("TARGET_DB_NAME", "postgres")
    target_user = target_user or os.getenv("TARGET_DB_USER", "postgres")
    target_password = target_password if target_password is not None else os.getenv("TARGET_DB_PASSWORD", "")

    if non_interactive:
        # Non-interactive mode
        logger = get_logger()

        console.print(create_header())
        console.print()
        logger.info("Running in non-interactive mode")
        logger.info(f"Source: {source_host}:{source_port}/{source_db}")
        logger.info(f"Target: {target_host}:{target_port}/{target_db}")

        # Build DSNs
        source_dsn = build_dsn(source_host, source_port, source_db, source_user, source_password)
        target_dsn = build_dsn(target_host, target_port, target_db, target_user, target_password)
        
        from .utils import mask_password
        logger.info(f"Source: {mask_password(source_dsn)}")
        logger.info(f"Target: {mask_password(target_dsn)}")
        context = MigrationContext(
            source_dsn=source_dsn,
            target_dsn=target_dsn,
            method=MigrationMethod.DUMP_RESTORE,
            dry_run=dry_run,
        )

        # Create and run engine
        engine = MigrationEngine(context)
        success = engine.run()

        sys.exit(0 if success else 1)
    else:
        # Interactive wizard mode (pass env values as defaults)
        wizard = MigrationWizard(console)
        wizard.env_defaults = {
            "source": {
                "host": source_host,
                "port": source_port,
                "database": source_db,
                "user": source_user,
                "password": source_password,
            },
            "target": {
                "host": target_host,
                "port": target_port,
                "database": target_db,
                "user": target_user,
                "password": target_password,
            },
        }
        success = wizard.run()
        sys.exit(0 if success else 1)


@cli.command()
@click.option("--host", default=None, help="Database host (defaults to SOURCE_DB_HOST from .env)")
@click.option("--port", default=None, type=int, help="Database port (defaults to SOURCE_DB_PORT from .env)")
@click.option("--db", "database", default=None, help="Database name (defaults to SOURCE_DB_NAME from .env)")
@click.option("--user", default=None, help="Database user (defaults to SOURCE_DB_USER from .env)")
@click.option("--password", default=None, help="Database password (defaults to SOURCE_DB_PASSWORD from .env)")
@click.option("--target", is_flag=True, help="Check target database instead of source")
@click.option("--report", type=click.Path(), help="Save compatibility report to JSON file")
def check(host: str, port: int, database: str, user: str, password: str, target: bool, report: str):
    """
    Check PostgreSQL version and analyze compatibility.
    
    This command connects to a PostgreSQL database, detects its version,
    and performs a compatibility analysis for migration to PostgreSQL 18.
    
    By default, reads connection info from .env file (SOURCE_DB_* variables).
    Use --target flag to check the target database instead.
    
    Examples:
    
    \b
    $ pg-migrator check                    # Uses .env settings
    $ pg-migrator check --target           # Check target DB from .env
    $ pg-migrator check --port 5432        # Override specific options
    $ pg-migrator check --host db.example.com --user admin
    """
    import os
    import json
    from datetime import datetime

    from dotenv import load_dotenv

    # Load .env file
    load_dotenv()

    console = create_console()
    logger = get_logger()

    console.print(create_header())
    console.print()

    # Get values from .env or use CLI overrides
    if target:
        # Use target database settings
        host = host or os.getenv("TARGET_DB_HOST", "localhost")
        port = port or int(os.getenv("TARGET_DB_PORT", "5432"))
        database = database or os.getenv("TARGET_DB_NAME", "postgres")
        user = user or os.getenv("TARGET_DB_USER", "postgres")
        password = password if password is not None else os.getenv("TARGET_DB_PASSWORD", "")
        logger.info("Checking TARGET database...")
    else:
        # Use source database settings
        host = host or os.getenv("SOURCE_DB_HOST", "localhost")
        port = port or int(os.getenv("SOURCE_DB_PORT", "5432"))
        database = database or os.getenv("SOURCE_DB_NAME", "postgres")
        user = user or os.getenv("SOURCE_DB_USER", "postgres")
        password = password if password is not None else os.getenv("SOURCE_DB_PASSWORD", "")
        logger.info("Checking SOURCE database...")

    logger.info(f"Host: {host}:{port}, Database: {database}, User: {user}")

    # Build DSN
    dsn = build_dsn(host, port, database, user, password)

    # Detect version
    logger.section("Version Detection")

    with VersionDetector(dsn) as detector:
        version_info = detector.detect_version()

        if not version_info:
            logger.error("Could not detect PostgreSQL version")
            logger.error("Check connection parameters and try again")
            sys.exit(1)

        logger.success(f"Detected: {version_info}")

        is_valid, message = detector.validate_source_version(version_info)
        if is_valid:
            logger.success(message)
        else:
            logger.warning(message)

    # Run compatibility analysis
    logger.section("Compatibility Analysis")

    result = analyze_compatibility(dsn, version_info.major)
    summary = result.get_summary()

    logger.info(f"Schemas analyzed: {summary['schemas']}")
    logger.info(f"Tables analyzed: {summary['tables']}")

    if summary["critical"] > 0:
        logger.error(f"Critical issues: {summary['critical']}")
    if summary["warnings"] > 0:
        logger.warning(f"Warnings: {summary['warnings']}")
    if summary["info"] > 0:
        logger.info(f"Informational: {summary['info']}")
    if summary["opportunities"] > 0:
        logger.info(f"Opportunities: {summary['opportunities']}")

    # Save report if requested
    if report:
        report_data = result.to_report_dict()
        report_data["timestamp"] = datetime.now().isoformat()
        report_data["database"] = {
            "host": host,
            "port": port,
            "name": database,
            "user": user,
            "version": str(version_info)
        }
        
        with open(report, "w") as f:
            json.dump(report_data, f, indent=2)
        logger.success(f"Report saved to: {report}")

    # Show issues
    if result.issues:
        console.print()
        from .ui.components import create_compatibility_table
        table = create_compatibility_table([i.to_dict() for i in result.issues])
        console.print(table)

    # Summary
    console.print()
    if summary["can_proceed"]:
        logger.success("✓ Database is ready for migration to PostgreSQL 18")
    else:
        logger.error("✗ Critical issues must be resolved before migration")

    sys.exit(0 if summary["can_proceed"] else 1)


@cli.command()
def version():
    """Show version information."""
    console = create_console()

    console.print()
    console.print(f"[pg.primary]🐘 {get_version_string()}[/pg.primary]")
    console.print()
    console.print("[dim]PostgreSQL Migration Tool[/dim]")
    console.print("[dim]Migrate from PG 14, 15, 16, 17 to PostgreSQL 18[/dim]")
    console.print()


@cli.command(name="gui")
def run_gui():
    """
    Launch the graphical user interface.

    This command opens a desktop application wrapper around the migration tool,
    allowing you to configure and run migrations using a clean UI instead of the terminal.
    """
    try:
        from .gui import MigratorApp
        app = MigratorApp()
        app.mainloop()
    except ImportError as e:
        console = create_console()
        console.print(f"[status.error]Failed to launch GUI. Make sure customtkinter is installed: {e}[/status.error]")
        sys.exit(1)


@cli.command()
def demo():
    """
    Run a demonstration of the migration wizard.
    
    This shows the wizard UI without connecting to any databases.
    Useful for previewing the tool's features.
    """
    console = create_console()
    wizard = MigrationWizard(console)
    wizard.run()


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console = create_console()
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(130)
    except Exception as e:
        console = create_console()
        console.print(f"[status.error]Error: {e}[/status.error]")
        sys.exit(1)


if __name__ == "__main__":
    main()
