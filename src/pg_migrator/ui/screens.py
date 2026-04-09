"""
Interactive UI Screens for PostgreSQL Migrator.
Stunning, animated screens for the migration wizard.
"""

import sys
import time
from typing import Optional, Callable, Dict, Any, List

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box

from .theme import (
    get_theme,
    COLORS,
    BANNER_ART,
    VERSION_FLOW,
)
from .components import (
    create_console,
    create_header,
    create_panel,
    create_status_indicator,
    create_progress_bar,
    create_database_table,
    create_compatibility_table,
    create_step_indicator,
    create_summary_panel,
    create_divider,
    create_menu,
    LiveMigrationTracker,
    create_animated_banner,
    create_loading_animation,
    create_success_animation,
)


class WelcomeScreen:
    """Welcome screen with pyfiglet banner."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
    
    def show(self) -> bool:
        """
        Display welcome screen.
        
        Returns:
            True if user wants to continue, False to exit
        """
        import pyfiglet
        
        self.console.clear()
        self.console.print()
        
        # Generate banner using pyfiglet
        banner_text = pyfiglet.figlet_format("PG MIGRATOR", font="slant")
        
        # Display banner with color gradient
        lines = banner_text.strip().split('\n')
        colors = ["#38b2ac", "#319795", "#2c7a7b", "#285e61", "#234e52", "#1d4044"]
        
        for i, line in enumerate(lines):
            color = colors[i % len(colors)]
            self.console.print(f"[bold {color}]{line}[/]")
        
        self.console.print()
        self.console.print("[bold #4299e1]    PostgreSQL Migration Wizard  v1.0[/]")
        self.console.print()
        
        # Version flow with colored numbers
        version_line = Text()
        version_line.append("        ")
        version_line.append("14", style="bold #e53e3e")
        version_line.append(" → ", style="dim")
        version_line.append("15", style="bold #ed8936")
        version_line.append(" → ", style="dim")
        version_line.append("16", style="bold #ecc94b")
        version_line.append(" → ", style="dim")
        version_line.append("17", style="bold #48bb78")
        version_line.append(" → ", style="dim")
        version_line.append("18", style="bold #4299e1")
        self.console.print(version_line)
        self.console.print()
        
        # Welcome panel
        welcome_text = Text()
        welcome_text.append("Welcome to PG Migrator!\n\n", style="bold #4299e1")
        welcome_text.append("This wizard will guide you through migrating your PostgreSQL database.\n\n")
        welcome_text.append("Features:\n", style="dim")
        welcome_text.append("  • 🔍 Auto-detect PostgreSQL versions\n")
        welcome_text.append("  • 📊 Pre-migration stats analysis\n")
        welcome_text.append("  • ⚠️  Compatibility analysis with recommendations\n")
        welcome_text.append("  • 🚀 Live animated progress tracking\n")
        welcome_text.append("  • 🔄 Same-version and cross-version migrations\n")
        welcome_text.append("  • 📝 Detailed logging\n")
        
        welcome_panel = Panel(
            welcome_text,
            title="[bold]🐘 PostgreSQL Migration Wizard[/bold]",
            border_style="#336791",
            padding=(1, 2),
        )
        self.console.print(welcome_panel)
        self.console.print()
        
        # Continue prompt
        return Confirm.ask(
            "[bold #4299e1]Ready to begin?[/bold #4299e1]",
            default=True,
            console=self.console,
        )


class ConnectionScreen:
    """Screen for database connection configuration."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
    
    def get_connection_details(
        self,
        db_type: str = "source",
        defaults: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prompt user for database connection details.
        
        Args:
            db_type: Either "source" or "target"
            defaults: Optional dictionary with default values from .env
            
        Returns:
            Dictionary with connection parameters
        """
        defaults = defaults or {}
        
        title = "Source Database" if db_type == "source" else "Target Database (PG 18)"
        icon = "📤" if db_type == "source" else "📥"
        default_port = defaults.get("port", 5432 if db_type == "source" else 5433)
        default_host = defaults.get("host", "localhost")
        default_db = defaults.get("database", "postgres")
        default_user = defaults.get("user", "postgres")
        default_password = defaults.get("password", "")
        
        self.console.print()
        self.console.print(create_divider(f"{icon} {title} Connection"))
        self.console.print()
        
        host = Prompt.ask(
            "[input.label]Host[/input.label]",
            default=default_host,
            console=self.console,
        )
        
        port = IntPrompt.ask(
            "[input.label]Port[/input.label]",
            default=default_port,
            console=self.console,
        )
        
        database = Prompt.ask(
            "[input.label]Database[/input.label]",
            default=default_db,
            console=self.console,
        )
        
        user = Prompt.ask(
            "[input.label]Username[/input.label]",
            default=default_user,
            console=self.console,
        )
        
        # Only prompt for password if not already set
        if default_password:
            use_default = Confirm.ask(
                "[input.label]Use saved password?[/input.label]",
                default=True,
                console=self.console,
            )
            if use_default:
                password = default_password
            else:
                password = Prompt.ask(
                    "[input.label]Password[/input.label]",
                    password=True,
                    console=self.console,
                )
        else:
            password = Prompt.ask(
                "[input.label]Password[/input.label]",
                password=True,
                console=self.console,
            )
        
        return {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
    
    def show_connection_test(
        self,
        source_info: Dict[str, Any],
        target_info: Dict[str, Any],
        source_connected: bool,
        target_connected: bool,
    ):
        """Display connection test results."""
        self.console.print()
        
        table = Table(
            show_header=True,
            header_style="table.header",
            box=box.ROUNDED,
            border_style=COLORS["pg_blue"],
            title="[bold]Connection Status[/bold]",
        )
        
        table.add_column("Database", style="pg.accent")
        table.add_column("Host", style="text_primary")
        table.add_column("Port", style="text_primary")
        table.add_column("Status", justify="center")
        
        source_status = "[status.success]✓ Connected[/status.success]" if source_connected else "[status.error]✗ Failed[/status.error]"
        target_status = "[status.success]✓ Connected[/status.success]" if target_connected else "[status.error]✗ Failed[/status.error]"
        
        table.add_row(
            "Source",
            source_info.get("host", "—"),
            str(source_info.get("port", "—")),
            source_status,
        )
        table.add_row(
            "Target (PG18)",
            target_info.get("host", "—"),
            str(target_info.get("port", "—")),
            target_status,
        )
        
        self.console.print(table)


class VersionScreen:
    """Screen for displaying detected versions."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
    
    def show_detection(
        self,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None,
    ):
        """Display detected versions with visual flow."""
        self.console.print()
        self.console.print(create_divider("🔍 Version Detection"))
        self.console.print()
        
        # Version flow visualization
        flow_text = Text()
        
        if source_version:
            major = source_version.split(".")[0] if source_version else "?"
            flow_text.append("  Source: ", style="dim")
            flow_text.append(f"PostgreSQL {source_version}", style=f"version.{major}" if major.isdigit() else "pg.primary")
            flow_text.append("\n")
        
        flow_text.append("     ↓\n", style="pg.accent")
        flow_text.append("  Migration Path\n", style="dim")
        flow_text.append("     ↓\n", style="pg.accent")
        
        if target_version:
            flow_text.append("  Target: ", style="dim")
            flow_text.append(f"PostgreSQL {target_version}", style="version.18")
        
        panel = create_panel(flow_text, "Version Information", border_color="pg_blue_light")
        self.console.print(panel)


class AnalysisScreen:
    """Screen for displaying compatibility analysis results."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
    
    def show_analysis(self, analysis_result: Dict[str, Any]):
        """Display compatibility analysis results."""
        self.console.print()
        self.console.print(create_divider("📊 Compatibility Analysis"))
        self.console.print()
        
        # Summary stats
        summary = analysis_result.get("summary", {})
        
        stats_text = Text()
        stats_text.append("  Schemas Analyzed: ", style="pg.accent")
        stats_text.append(f"{summary.get('schemas', 0)}\n", style="text_primary")
        stats_text.append("  Tables Analyzed: ", style="pg.accent")
        stats_text.append(f"{summary.get('tables', 0)}\n", style="text_primary")
        stats_text.append("\n")
        
        critical = summary.get("critical", 0)
        warnings = summary.get("warnings", 0)
        info = summary.get("info", 0)
        opportunities = summary.get("opportunities", 0)
        
        if critical > 0:
            stats_text.append(f"  ❌ Critical Issues: {critical}\n", style="status.error")
        if warnings > 0:
            stats_text.append(f"  ⚠️  Warnings: {warnings}\n", style="status.warning")
        if info > 0:
            stats_text.append(f"  ℹ️  Info: {info}\n", style="status.info")
        if opportunities > 0:
            stats_text.append(f"  ✨ Opportunities: {opportunities}\n", style="pg.highlight")
        
        panel = create_panel(stats_text, "Analysis Summary", border_color="pg_blue")
        self.console.print(panel)
        
        # Issues table
        issues = analysis_result.get("issues", [])
        if issues:
            self.console.print()
            table = create_compatibility_table(issues)
            self.console.print(table)
        
        # Can proceed check
        can_proceed = summary.get("can_proceed", True)
        self.console.print()
        
        if can_proceed:
            self.console.print(create_status_indicator(
                "success",
                "No blocking issues found. Ready to migrate!",
            ))
        else:
            self.console.print(create_status_indicator(
                "error",
                "Critical issues must be resolved before migration.",
            ))
        
        return can_proceed


class MigrationScreen:
    """Screen for displaying migration progress."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
    
    def show_progress(
        self,
        steps: List[Dict[str, str]],
        current_step: int,
        status_message: str = "",
    ):
        """Display migration progress with step indicator."""
        layout = Layout()
        
        # Steps panel
        steps_panel = create_step_indicator(steps, current_step)
        
        # Status panel
        status_text = Text()
        status_text.append("  ", style="dim")
        status_text.append(status_message, style="pg.accent")
        
        status_panel = create_panel(
            status_text,
            "Current Status",
            border_color="pg_cyan",
        )
        
        self.console.print(steps_panel)
        self.console.print(status_panel)
    
    def run_with_progress(
        self,
        task_name: str,
        task_func: Callable,
        total: int = 100,
    ) -> Any:
        """Run a task with animated progress bar."""
        with create_progress_bar() as progress:
            task = progress.add_task(f"[pg.accent]{task_name}[/pg.accent]", total=total)
            
            result = None
            
            def update_progress(current: int):
                progress.update(task, completed=current)
            
            try:
                result = task_func(update_progress)
                progress.update(task, completed=total)
            except Exception as e:
                progress.update(task, description=f"[status.error]{task_name} - Failed[/status.error]")
                raise
            
            return result


class MigrationPreviewScreen:
    """Screen for showing pre-migration stats and getting user confirmation."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
    
    def show_stats(self, stats: 'DatabaseStats', source_version: str, target_version: str) -> bool:
        """
        Display database statistics and ask for migration confirmation.
        
        Args:
            stats: DatabaseStats object with collected statistics
            source_version: Source PostgreSQL version
            target_version: Target PostgreSQL version
            
        Returns:
            True if user confirms migration, False otherwise
        """
        self.console.print()
        self.console.print(create_divider("📊 Pre-Migration Analysis"))
        self.console.print()
        
        # Migration plan header
        plan_text = Text()
        plan_text.append("Migration Plan\n\n", style="bold #4299e1")
        plan_text.append(f"  Source: PostgreSQL {source_version}\n", style="#e53e3e")
        plan_text.append(f"  Target: PostgreSQL {target_version}\n", style="#48bb78")
        
        self.console.print(Panel(plan_text, border_style="#336791", padding=(0, 2)))
        self.console.print()
        
        # Database Stats Table
        stats_table = Table(
            title="[bold]Database Statistics[/bold]",
            show_header=True,
            header_style="bold #4299e1",
            border_style="#336791",
            box=box.ROUNDED,
        )
        
        stats_table.add_column("Metric", style="#38b2ac", width=25)
        stats_table.add_column("Count", justify="right", style="bold")
        stats_table.add_column("Details", style="dim")
        
        stats_table.add_row("📁 Schemas", str(stats.total_schemas), "")
        stats_table.add_row("📋 Tables", str(stats.total_tables), "")
        stats_table.add_row("📊 Total Rows", f"{stats.total_rows:,}", "Approximate")
        stats_table.add_row("💾 Total Size", stats.total_size_formatted, "Including indexes")
        stats_table.add_row("🔍 Indexes", str(stats.total_indexes), "")
        stats_table.add_row("👁️ Views", str(stats.total_views), "")
        stats_table.add_row("⚡ Functions", str(stats.total_functions), "")
        stats_table.add_row("🔢 Sequences", str(stats.total_sequences), "")
        stats_table.add_row("🎯 Triggers", str(stats.total_triggers), "")
        
        if stats.extensions:
            stats_table.add_row("🧩 Extensions", str(len(stats.extensions)), ", ".join(stats.extensions[:5]))
        
        self.console.print(stats_table)
        self.console.print()
        
        # Top tables by size
        if stats.tables:
            top_tables = sorted(stats.tables, key=lambda t: t.row_count, reverse=True)[:10]
            
            tables_table = Table(
                title="[bold]Top Tables by Row Count[/bold]",
                show_header=True,
                header_style="bold #4299e1",
                border_style="#336791",
                box=box.ROUNDED,
            )
            
            tables_table.add_column("Table", style="#38b2ac")
            tables_table.add_column("Rows", justify="right", style="bold")
            tables_table.add_column("Size", justify="right")
            tables_table.add_column("Columns", justify="center")
            
            for table in top_tables:
                tables_table.add_row(
                    table.full_name,
                    f"{table.row_count:,}",
                    table.size_formatted,
                    str(table.column_count),
                )
            
            self.console.print(tables_table)
            self.console.print()
        
        # Migration steps preview
        steps = stats.get_migration_steps()
        total_weight = stats.get_total_weight()
        
        steps_text = Text()
        steps_text.append("Migration Steps\n\n", style="bold #4299e1")
        steps_text.append(f"  Total steps: {len(steps)}\n", style="dim")
        steps_text.append(f"  Estimated complexity: ", style="dim")
        
        if total_weight < 50:
            steps_text.append("Low", style="bold #48bb78")
        elif total_weight < 150:
            steps_text.append("Medium", style="bold #ed8936")
        else:
            steps_text.append("High", style="bold #e53e3e")
        
        steps_text.append(f" (weight: {total_weight})\n", style="dim")
        
        self.console.print(Panel(steps_text, border_style="#336791", padding=(0, 2)))
        self.console.print()
        
        # Confirmation prompt
        self.console.print("[bold #ed8936]⚠️  The migration will start after confirmation.[/]")
        self.console.print("[dim]   A backup of your data is recommended before proceeding.[/]")
        self.console.print()
        
        return Confirm.ask(
            "[bold #4299e1]Proceed with migration?[/bold #4299e1]",
            default=False,
            console=self.console,
        )
    
    def run_animated_migration(
        self,
        stats: 'DatabaseStats',
        migration_callback: Callable[[Callable[[str, int], None]], bool],
    ) -> bool:
        """
        Run migration with animated progress based on stats.
        
        Args:
            stats: DatabaseStats for progress calculation
            migration_callback: Function that runs migration and accepts progress callback
            
        Returns:
            True if migration succeeded, False otherwise
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
        
        self.console.print()
        self.console.print(create_divider("🚀 Migration in Progress"))
        self.console.print()
        
        total_weight = stats.get_total_weight()
        steps = stats.get_migration_steps()
        
        with Progress(
            SpinnerColumn(spinner_name="dots12", style="#38b2ac"),
            TextColumn("[bold]{task.description}[/bold]"),
            BarColumn(bar_width=40, style="#336791", complete_style="#38b2ac", finished_style="#48bb78"),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=self.console,
            expand=True,
        ) as progress:
            
            main_task = progress.add_task("[#4299e1]Overall Progress[/]", total=100)
            current_task = progress.add_task("[dim]Initializing...[/]", total=100)
            
            current_weight = 0
            
            def update_progress(step_name: str, step_pct: int):
                nonlocal current_weight
                
                # Update current step display
                progress.update(current_task, description=f"[dim]{step_name}[/]", completed=step_pct)
                
                # Calculate overall progress based on weights
                if step_pct == 100:
                    # Find the weight of completed step
                    for step in steps:
                        if step["name"] == step_name:
                            current_weight += step["weight"]
                            break
                
                overall_pct = min(100, int((current_weight / total_weight) * 100))
                progress.update(main_task, completed=overall_pct)
            
            try:
                success = migration_callback(update_progress)
                
                # Complete progress
                progress.update(main_task, completed=100)
                progress.update(current_task, description="[#48bb78]Completed![/]", completed=100)
                
                return success
                
            except Exception as e:
                progress.update(current_task, description=f"[#e53e3e]Error: {str(e)[:30]}...[/]")
                return False


class SummaryScreen:
    """Screen for displaying migration summary."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
    
    def show_summary(
        self,
        success: bool,
        stats: Dict[str, Any],
        duration: str,
    ):
        """Display final migration summary."""
        self.console.print()
        self.console.print(create_divider("📋 Migration Summary"))
        self.console.print()
        
        panel = create_summary_panel(success, stats, duration)
        self.console.print(panel)
        
        if success:
            self.console.print()
            self.console.print(Text.from_markup(
                "\n[pg.highlight]🎊 Congratulations![/pg.highlight] "
                "Your database has been successfully migrated to PostgreSQL 18.\n\n"
                "[dim]Next steps:[/dim]\n"
                "  • Review the migration logs\n"
                "  • Run your application test suite\n"
                "  • Monitor database performance\n"
                "  • Consider enabling new PG18 features (AIO, UUIDv7, etc.)\n"
            ))
        else:
            self.console.print()
            self.console.print(Text.from_markup(
                "\n[status.error]Migration encountered issues.[/status.error]\n\n"
                "[dim]Troubleshooting:[/dim]\n"
                "  • Check the error messages above\n"
                "  • Review the migration logs\n"
                "  • Your backup is available for restoration\n"
                "  • Consult PostgreSQL 18 release notes\n"
            ))


class MigrationWizard:
    """Main wizard that orchestrates all screens."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()
        
        # Initialize screens
        self.welcome = WelcomeScreen(self.console)
        self.connection = ConnectionScreen(self.console)
        self.version = VersionScreen(self.console)
        self.analysis = AnalysisScreen(self.console)
        self.migration = MigrationScreen(self.console)
        self.summary = SummaryScreen(self.console)
        
        # Defaults from .env (set by main.py)
        self.env_defaults: Optional[Dict[str, Any]] = None
    
    def run(self) -> bool:
        """
        Run the complete migration wizard.
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Welcome screen
            if not self.welcome.show():
                self.console.print("\n[dim]Migration cancelled.[/dim]")
                return False
            
            # Get connection details
            self.console.clear()
            self.console.print(create_header())
            
            # Pass env defaults to connection prompts
            source_defaults = self.env_defaults.get("source", {}) if self.env_defaults else {}
            target_defaults = self.env_defaults.get("target", {}) if self.env_defaults else {}
            
            source_conn = self.connection.get_connection_details("source", source_defaults)
            target_conn = self.connection.get_connection_details("target", target_defaults)
            
            # Build DSNs
            source_dsn = (
                f"host={source_conn['host']} "
                f"port={source_conn['port']} "
                f"dbname={source_conn['database']} "
                f"user={source_conn['user']} "
                f"password={source_conn['password']}"
            )
            
            target_dsn = (
                f"host={target_conn['host']} "
                f"port={target_conn['port']} "
                f"dbname={target_conn['database']} "
                f"user={target_conn['user']} "
                f"password={target_conn['password']}"
            )
            
            # Import migration dependencies
            from ..detector import VersionDetector
            from ..analyzer import analyze_compatibility
            from ..migrator import MigrationEngine, MigrationContext, MigrationMethod
            from ..logger import get_logger
            
            logger = get_logger()
            
            # Step 1: Test connections and detect versions
            self.console.print()
            self.console.print(create_divider("🔌 Testing Connections"))
            
            source_version = None
            target_version = None
            
            try:
                with VersionDetector(source_dsn) as detector:
                    source_version = detector.detect_version()
                    if source_version:
                        self.console.print(f"[status.success]✓ Source: PostgreSQL {source_version}[/status.success]")
                    else:
                        self.console.print("[status.error]✗ Cannot connect to source database[/status.error]")
                        return False
            except Exception as e:
                self.console.print(f"[status.error]✗ Source connection error: {e}[/status.error]")
                return False
            
            # Try to connect to target - if database doesn't exist, create it
            try:
                with VersionDetector(target_dsn) as detector:
                    target_version = detector.detect_version()
                    if target_version:
                        self.console.print(f"[status.success]✓ Target: PostgreSQL {target_version}[/status.success]")
            except Exception as e:
                # Database might not exist - try to create it
                self.console.print(f"[status.warning]⚠ Target database may not exist, attempting to create...[/status.warning]")
                
                from ..db_manager import DatabaseManager
                
                try:
                    # Connect to postgres database to create target
                    manager = DatabaseManager(
                        host=target_conn["host"],
                        port=target_conn["port"],
                        user=target_conn["user"],
                        password=target_conn["password"],
                    )
                    
                    success, msg = manager.prepare_target_database(
                        dbname=target_conn["database"],
                        drop_if_exists=True,
                        owner=target_conn["user"],
                    )
                    
                    if success:
                        self.console.print(f"[status.success]✓ Created target database: {target_conn['database']}[/status.success]")
                        
                        # Now try to detect version again
                        with VersionDetector(target_dsn) as detector:
                            target_version = detector.detect_version()
                            if target_version:
                                self.console.print(f"[status.success]✓ Target: PostgreSQL {target_version}[/status.success]")
                            else:
                                self.console.print("[status.error]✗ Cannot connect to newly created database[/status.error]")
                                return False
                    else:
                        self.console.print(f"[status.error]✗ Failed to create target database: {msg}[/status.error]")
                        return False
                except Exception as create_error:
                    self.console.print(f"[status.error]✗ Cannot create target database: {create_error}[/status.error]")
                    return False
            
            # Show version detection
            self.version.show_detection(str(source_version), str(target_version))
            
            # Step 2: Analyze compatibility
            self.console.print()
            self.console.print(create_divider("📊 Analyzing Compatibility"))
            
            try:
                result = analyze_compatibility(source_dsn, source_version.major)
                summary = result.get_summary()
                
                self.analysis.show_analysis({
                    "summary": summary,
                    "issues": [i.to_dict() for i in result.issues],
                })
                
                can_proceed = summary.get("can_proceed", True)
            except Exception as e:
                self.console.print(f"[status.error]Analysis error: {e}[/status.error]")
                can_proceed = True  # Allow to proceed with warning
            
            # Ask to proceed
            self.console.print()
            proceed = Confirm.ask(
                "[pg.accent]Would you like to proceed with migration?[/pg.accent]",
                default=can_proceed,
                console=self.console,
            )
            
            if not proceed:
                self.console.print("\n[dim]Migration cancelled by user.[/dim]")
                return False
            
            # Step 3: Run the actual migration
            self.console.print()
            self.console.print(create_divider("🚀 Performing Migration"))
            self.console.print()
            
            # Create migration context (use PYTHON method - no pg_dump dependency)
            context = MigrationContext(
                source_dsn=source_dsn,
                target_dsn=target_dsn,
                method=MigrationMethod.PYTHON,
                dry_run=False,
            )
            
            # Create and run engine
            engine = MigrationEngine(context)
            success = engine.run()
            
            # Show summary with actual data
            migration_summary = engine.get_summary()
            
            self.summary.show_summary(
                success=success,
                stats={
                    "Source Version": str(source_version),
                    "Target Version": str(target_version),
                    "Tables Analyzed": summary.get("tables", 0),
                    "Schemas Analyzed": summary.get("schemas", 0),
                    "Method": context.method.value,
                },
                duration=migration_summary.get("duration", "N/A"),
            )
            
            return success
            
        except KeyboardInterrupt:
            self.console.print("\n\n[status.warning]Migration interrupted by user.[/status.warning]")
            return False
        except Exception as e:
            self.console.print(f"\n[status.error]Error: {e}[/status.error]")
            return False
