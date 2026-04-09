"""
Interactive UI Screens for PostgreSQL Migrator.
Premium, animated screens with neon dark aesthetic.
"""

import time
from typing import Any, Callable, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from .components import (
    create_compatibility_table,
    create_console,
    create_divider,
    create_glass_panel,
    create_header,
    create_loading_animation,
    create_panel,
    create_progress_bar,
    create_status_indicator,
    create_step_indicator,
    create_success_animation,
    create_summary_panel,
    create_wave_animation,
)
from .theme import (
    BOX_CHARS,
    COLORS,
    SPINNERS,
)


# ──────────────────────────────────────────────────────────
# Utility: Animated text typing effect
# ──────────────────────────────────────────────────────────
def _type_text(console: Console, text: str, style: str = "", delay: float = 0.01):
    """Print text with a typing animation effect."""
    for char in text:
        console.print(char, end="", style=style, highlight=False)
        time.sleep(delay)
    console.print()


def _fade_in_panel(console: Console, panel: Panel, steps: int = 3):
    """Simulate a fade-in effect for a panel by printing with brief delay."""
    time.sleep(0.05)
    console.print(panel)
    time.sleep(0.05)


# ──────────────────────────────────────────────────────────
# Welcome Screen
# ──────────────────────────────────────────────────────────
class WelcomeScreen:
    """Welcome screen with animated neon banner."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()

    def show(self) -> bool:
        """
        Display welcome screen with animations.

        Returns:
            True if user wants to continue, False to exit
        """
        import pyfiglet

        self.console.clear()
        self.console.print()

        # Animated gradient banner
        banner_text = pyfiglet.figlet_format("PG MIGRATOR", font="slant")
        lines = banner_text.strip().split("\n")
        gradient = ["#22d3ee", "#2dd4bf", "#818cf8", "#a78bfa", "#c084fc", "#e879f9"]

        for i, line in enumerate(lines):
            color = gradient[i % len(gradient)]
            self.console.print(f"[bold {color}]{line}[/]")
            time.sleep(0.04)

        self.console.print()
        time.sleep(0.1)

        # Subtitle with typing effect
        _type_text(self.console, "    PostgreSQL Migration Wizard", style="#94a3b8", delay=0.02)
        time.sleep(0.1)

        # Version flow with sequential reveal
        self.console.print()
        versions = [
            (" 14 ", "#fb7185"), (" 15 ", "#fbbf24"), (" 16 ", "#a3e635"),
            (" 17 ", "#34d399"), (" 18 ", "#22d3ee"),
        ]
        flow = Text("        ")
        for j, (ver, color) in enumerate(versions):
            flow.append(ver, style=f"bold {color}")
            if j < len(versions) - 1:
                flow.append(" >> ", style="#334155")
        self.console.print(flow)
        self.console.print()
        time.sleep(0.1)

        # Feature panel with glass effect
        features = Text()
        features.append("\n")
        feature_list = [
            (f" {BOX_CHARS['check']} ", "#34d399", "Auto-detect PostgreSQL versions (14-18)"),
            (f" {BOX_CHARS['check']} ", "#22d3ee", "Pre-migration stats & compatibility analysis"),
            (f" {BOX_CHARS['check']} ", "#a78bfa", "Live animated progress tracking"),
            (f" {BOX_CHARS['check']} ", "#fbbf24", "Same-version & cross-version migrations"),
            (f" {BOX_CHARS['check']} ", "#f472b6", "Pure Python migration (no pg_dump dependency)"),
            (f" {BOX_CHARS['check']} ", "#a3e635", "Detailed logging & JSON reports"),
        ]

        for icon, color, desc in feature_list:
            features.append(f"  [{color}]{icon}[/]", style=color)
            features.append(f"  {desc}\n", style="#94a3b8")

        features.append("\n")

        panel = create_glass_panel(features, "Features", accent_color="#a78bfa")
        _fade_in_panel(self.console, panel)
        self.console.print()

        # Continue prompt
        return Confirm.ask(
            f"[bold #22d3ee]{BOX_CHARS['arrow']} Ready to begin?[/bold #22d3ee]",
            default=True,
            console=self.console,
        )


# ──────────────────────────────────────────────────────────
# Connection Screen
# ──────────────────────────────────────────────────────────
class ConnectionScreen:
    """Screen for database connection configuration with modern styling."""

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

        if db_type == "source":
            title = "Source Database"
            accent = "#fb7185"
        else:
            title = "Target Database"
            accent = "#22d3ee"

        default_port = defaults.get("port", 5432 if db_type == "source" else 5433)
        default_host = defaults.get("host", "localhost")
        default_db = defaults.get("database", "postgres")
        default_user = defaults.get("user", "postgres")
        default_password = defaults.get("password", "")

        self.console.print()
        self.console.print(create_divider(f"{title} Connection"))
        self.console.print()

        prompt_style = f"bold {accent}"

        host = Prompt.ask(
            f"[{prompt_style}]{BOX_CHARS['arrow']}[/] [#f1f5f9]Host[/]",
            default=default_host,
            console=self.console,
        )

        port = IntPrompt.ask(
            f"[{prompt_style}]{BOX_CHARS['arrow']}[/] [#f1f5f9]Port[/]",
            default=default_port,
            console=self.console,
        )

        database = Prompt.ask(
            f"[{prompt_style}]{BOX_CHARS['arrow']}[/] [#f1f5f9]Database[/]",
            default=default_db,
            console=self.console,
        )

        user = Prompt.ask(
            f"[{prompt_style}]{BOX_CHARS['arrow']}[/] [#f1f5f9]Username[/]",
            default=default_user,
            console=self.console,
        )

        if default_password:
            use_default = Confirm.ask(
                f"[{prompt_style}]{BOX_CHARS['arrow']}[/] [#f1f5f9]Use saved password?[/]",
                default=True,
                console=self.console,
            )
            if use_default:
                password = default_password
            else:
                password = Prompt.ask(
                    f"[{prompt_style}]{BOX_CHARS['arrow']}[/] [#f1f5f9]Password[/]",
                    password=True,
                    console=self.console,
                )
        else:
            password = Prompt.ask(
                f"[{prompt_style}]{BOX_CHARS['arrow']}[/] [#f1f5f9]Password[/]",
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
        """Display connection test results with modern table."""
        self.console.print()

        table = Table(
            show_header=True,
            header_style="bold #22d3ee",
            box=box.ROUNDED,
            border_style="#334155",
            title="[bold #a78bfa] Connection Status [/]",
            row_styles=["", "#1e293b"],
            pad_edge=True,
            padding=(0, 1),
        )

        table.add_column("", width=3, justify="center")
        table.add_column("Database", style="#94a3b8", width=15)
        table.add_column("Host", style="#f1f5f9")
        table.add_column("Port", style="#f1f5f9")
        table.add_column("Status", justify="center")

        s_icon = "[bold #34d399]●[/]" if source_connected else "[bold #fb7185]●[/]"
        t_icon = "[bold #34d399]●[/]" if target_connected else "[bold #fb7185]●[/]"
        s_status = "[#34d399]Connected[/]" if source_connected else "[#fb7185]Failed[/]"
        t_status = "[#34d399]Connected[/]" if target_connected else "[#fb7185]Failed[/]"

        table.add_row(s_icon, "Source", source_info.get("host", "---"), str(source_info.get("port", "---")), s_status)
        table.add_row(t_icon, "Target", target_info.get("host", "---"), str(target_info.get("port", "---")), t_status)

        self.console.print(table)


# ──────────────────────────────────────────────────────────
# Version Screen
# ──────────────────────────────────────────────────────────
class VersionScreen:
    """Screen for displaying detected versions with visual flow."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()

    def show_detection(
        self,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None,
    ):
        """Display detected versions with animated visual flow."""
        self.console.print()
        self.console.print(create_divider("Version Detection"))
        self.console.print()

        content = Text()
        content.append("\n")

        if source_version:
            major = source_version.split(".")[0] if source_version else "?"
            ver_color = f"version.{major}" if major.isdigit() else "pg.primary"
            content.append(f"  {BOX_CHARS['diamond']} ", style="#fb7185")
            content.append("Source  ", style="#64748b")
            content.append(f"PostgreSQL {source_version}", style=ver_color)
            content.append("\n")

        content.append("       |\n", style="#334155")
        content.append("       |  ", style="#334155")
        content.append("migration path\n", style="#64748b")
        content.append("       |\n", style="#334155")

        if target_version:
            content.append(f"  {BOX_CHARS['diamond']} ", style="#22d3ee")
            content.append("Target  ", style="#64748b")
            content.append(f"PostgreSQL {target_version}", style="version.18")

        content.append("\n")

        panel = create_glass_panel(content, "Version Information", accent_color="#818cf8")
        _fade_in_panel(self.console, panel)


# ──────────────────────────────────────────────────────────
# Analysis Screen
# ──────────────────────────────────────────────────────────
class AnalysisScreen:
    """Screen for displaying compatibility analysis results."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()

    def show_analysis(self, analysis_result: Dict[str, Any]):
        """Display compatibility analysis results with modern layout."""
        self.console.print()
        self.console.print(create_divider("Compatibility Analysis"))
        self.console.print()

        summary = analysis_result.get("summary", {})

        # Stats card
        stats_content = Text()
        stats_content.append("\n")
        stats_content.append(f"  {BOX_CHARS['arrow']} Schemas Analyzed: ", style="#64748b")
        stats_content.append(f"{summary.get('schemas', 0)}\n", style="#f1f5f9")
        stats_content.append(f"  {BOX_CHARS['arrow']} Tables Analyzed:  ", style="#64748b")
        stats_content.append(f"{summary.get('tables', 0)}\n", style="#f1f5f9")
        stats_content.append("\n")

        critical = summary.get("critical", 0)
        warnings = summary.get("warnings", 0)
        info = summary.get("info", 0)
        opportunities = summary.get("opportunities", 0)

        if critical > 0:
            stats_content.append(f"  {BOX_CHARS['cross']} Critical:      {critical}\n", style="#fb7185")
        if warnings > 0:
            stats_content.append(f"  {BOX_CHARS['diamond']} Warnings:      {warnings}\n", style="#fbbf24")
        if info > 0:
            stats_content.append(f"  {BOX_CHARS['circle']} Info:          {info}\n", style="#60a5fa")
        if opportunities > 0:
            stats_content.append(f"  {BOX_CHARS['star']} Opportunities: {opportunities}\n", style="#a78bfa")

        stats_content.append("\n")

        panel = create_glass_panel(stats_content, "Analysis Summary", accent_color="#818cf8")
        _fade_in_panel(self.console, panel)

        # Issues table
        issues = analysis_result.get("issues", [])
        if issues:
            self.console.print()
            table = create_compatibility_table(issues)
            self.console.print(table)

        # Verdict
        can_proceed = summary.get("can_proceed", True)
        self.console.print()

        if can_proceed:
            self.console.print(create_status_indicator(
                "success",
                "No blocking issues found. Ready to migrate.",
            ))
        else:
            self.console.print(create_status_indicator(
                "error",
                "Critical issues must be resolved before migration.",
            ))

        return can_proceed


# ──────────────────────────────────────────────────────────
# Migration Screen
# ──────────────────────────────────────────────────────────
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
        steps_panel = create_step_indicator(steps, current_step)

        status_text = Text()
        status_text.append(f"  {BOX_CHARS['arrow']} ", style="#334155")
        status_text.append(status_message, style="#94a3b8")

        status_panel = create_panel(
            status_text,
            "Current Status",
            border_color="#334155",
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
            task = progress.add_task(f"[#22d3ee]{task_name}[/]", total=total)

            result = None

            def update_progress(current: int):
                progress.update(task, completed=current)

            try:
                result = task_func(update_progress)
                progress.update(task, completed=total)
            except Exception:
                progress.update(task, description=f"[#fb7185]{task_name} - Failed[/]")
                raise

            return result


# ──────────────────────────────────────────────────────────
# Migration Preview Screen
# ──────────────────────────────────────────────────────────
class MigrationPreviewScreen:
    """Screen for showing pre-migration stats and getting user confirmation."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()

    def show_stats(self, stats: Any, source_version: str, target_version: str) -> bool:
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
        self.console.print(create_divider("Pre-Migration Analysis"))
        self.console.print()

        # Migration plan header
        plan_content = Text()
        plan_content.append("\n")
        plan_content.append(f"  {BOX_CHARS['diamond']} ", style="#fb7185")
        plan_content.append(f"Source: PostgreSQL {source_version}\n", style="#fb7185")
        plan_content.append(f"  {BOX_CHARS['diamond']} ", style="#22d3ee")
        plan_content.append(f"Target: PostgreSQL {target_version}\n", style="#22d3ee")
        plan_content.append("\n")

        plan_panel = create_glass_panel(plan_content, "Migration Plan", accent_color="#818cf8")
        _fade_in_panel(self.console, plan_panel)
        self.console.print()

        # Database Stats Table
        stats_table = Table(
            title="[bold #a78bfa] Database Statistics [/]",
            show_header=True,
            header_style="bold #22d3ee",
            border_style="#334155",
            box=box.ROUNDED,
            row_styles=["", "#1e293b"],
            pad_edge=True,
            padding=(0, 1),
        )

        stats_table.add_column("", width=3, justify="center", style="#334155")
        stats_table.add_column("Metric", style="#94a3b8", width=20)
        stats_table.add_column("Count", justify="right", style="bold #f1f5f9")
        stats_table.add_column("Details", style="#64748b")

        stats_table.add_row(BOX_CHARS["arrow"], "Schemas", str(stats.total_schemas), "")
        stats_table.add_row(BOX_CHARS["arrow"], "Tables", str(stats.total_tables), "")
        stats_table.add_row(BOX_CHARS["arrow"], "Total Rows", f"{stats.total_rows:,}", "Approximate")
        stats_table.add_row(BOX_CHARS["arrow"], "Total Size", stats.total_size_formatted, "Including indexes")
        stats_table.add_row(BOX_CHARS["arrow"], "Indexes", str(stats.total_indexes), "")
        stats_table.add_row(BOX_CHARS["arrow"], "Views", str(stats.total_views), "")
        stats_table.add_row(BOX_CHARS["arrow"], "Functions", str(stats.total_functions), "")
        stats_table.add_row(BOX_CHARS["arrow"], "Sequences", str(stats.total_sequences), "")
        stats_table.add_row(BOX_CHARS["arrow"], "Triggers", str(stats.total_triggers), "")

        if stats.extensions:
            stats_table.add_row(BOX_CHARS["arrow"], "Extensions", str(len(stats.extensions)), ", ".join(stats.extensions[:5]))

        self.console.print(stats_table)
        self.console.print()

        # Top tables
        if stats.tables:
            top_tables = sorted(stats.tables, key=lambda t: t.row_count, reverse=True)[:10]

            tables_table = Table(
                title="[bold #a78bfa] Top Tables by Row Count [/]",
                show_header=True,
                header_style="bold #22d3ee",
                border_style="#334155",
                box=box.ROUNDED,
                row_styles=["", "#1e293b"],
                pad_edge=True,
                padding=(0, 1),
            )

            tables_table.add_column("Table", style="#22d3ee")
            tables_table.add_column("Rows", justify="right", style="bold #f1f5f9")
            tables_table.add_column("Size", justify="right", style="#94a3b8")
            tables_table.add_column("Columns", justify="center", style="#64748b")

            for table in top_tables:
                tables_table.add_row(
                    table.full_name,
                    f"{table.row_count:,}",
                    table.size_formatted,
                    str(table.column_count),
                )

            self.console.print(tables_table)
            self.console.print()

        # Complexity indicator
        steps = stats.get_migration_steps()
        total_weight = stats.get_total_weight()

        complexity_content = Text()
        complexity_content.append("\n")
        complexity_content.append(f"  {BOX_CHARS['arrow']} Total Steps:  ", style="#64748b")
        complexity_content.append(f"{len(steps)}\n", style="#f1f5f9")
        complexity_content.append(f"  {BOX_CHARS['arrow']} Complexity:   ", style="#64748b")

        if total_weight < 50:
            complexity_content.append("Low", style="bold #34d399")
        elif total_weight < 150:
            complexity_content.append("Medium", style="bold #fbbf24")
        else:
            complexity_content.append("High", style="bold #fb7185")

        complexity_content.append(f"  [#334155](weight: {total_weight})[/]\n\n", style="#64748b")

        panel = create_glass_panel(complexity_content, "Migration Steps", accent_color="#818cf8")
        self.console.print(panel)
        self.console.print()

        # Warning
        self.console.print(f"  [bold #fbbf24]{BOX_CHARS['diamond']}[/] [#fbbf24]The migration will start after confirmation.[/]")
        self.console.print(f"  [#64748b]  A backup of your data is recommended before proceeding.[/]")
        self.console.print()

        return Confirm.ask(
            f"[bold #22d3ee]{BOX_CHARS['arrow']} Proceed with migration?[/bold #22d3ee]",
            default=False,
            console=self.console,
        )

    def run_animated_migration(
        self,
        stats: Any,
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
        from rich.progress import TaskProgressColumn, TimeElapsedColumn

        self.console.print()
        self.console.print(create_divider("Migration in Progress"))
        self.console.print()

        total_weight = stats.get_total_weight()
        steps = stats.get_migration_steps()

        with Progress(
            SpinnerColumn(spinner_name="dots12", style="#22d3ee"),
            TextColumn("[bold]{task.description}[/bold]"),
            BarColumn(bar_width=40, style="#334155", complete_style="#22d3ee", finished_style="#34d399"),
            TaskProgressColumn(),
            TextColumn("[#334155]|[/]"),
            TimeElapsedColumn(),
            console=self.console,
            expand=True,
        ) as progress:

            main_task = progress.add_task("[#22d3ee]Overall Progress[/]", total=100)
            current_task = progress.add_task("[#64748b]Initializing...[/]", total=100)

            current_weight = 0

            def update_progress(step_name: str, step_pct: int):
                nonlocal current_weight

                progress.update(current_task, description=f"[#94a3b8]{step_name}[/]", completed=step_pct)

                if step_pct == 100:
                    for step in steps:
                        if step["name"] == step_name:
                            current_weight += step["weight"]
                            break

                overall_pct = min(100, int((current_weight / total_weight) * 100))
                progress.update(main_task, completed=overall_pct)

            try:
                success = migration_callback(update_progress)

                progress.update(main_task, completed=100)
                progress.update(current_task, description="[#34d399]Completed[/]", completed=100)

                return success

            except Exception as e:
                progress.update(current_task, description=f"[#fb7185]Error: {str(e)[:30]}[/]")
                return False


# ──────────────────────────────────────────────────────────
# Summary Screen
# ──────────────────────────────────────────────────────────
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
        """Display final migration summary with animations."""
        self.console.print()
        self.console.print(create_divider("Migration Summary"))
        self.console.print()

        if success:
            create_success_animation(self.console)
            time.sleep(0.2)

        panel = create_summary_panel(success, stats, duration)
        _fade_in_panel(self.console, panel)

        if success:
            next_steps = Text()
            next_steps.append("\n")
            next_steps.append("  [bold #34d399]Migration completed successfully.[/]\n\n")
            next_steps.append("  [#64748b]Next steps:[/]\n")
            tips = [
                ("Review the migration logs", "#22d3ee"),
                ("Run your application test suite", "#a78bfa"),
                ("Monitor database performance", "#fbbf24"),
                ("Consider enabling PG18 features (AIO, UUIDv7)", "#34d399"),
            ]
            for tip, color in tips:
                next_steps.append(f"    [{color}]{BOX_CHARS['arrow']}[/] [{color}]{tip}[/]\n")
            next_steps.append("\n")
            self.console.print(next_steps)
        else:
            troubleshoot = Text()
            troubleshoot.append("\n")
            troubleshoot.append("  [bold #fb7185]Migration encountered issues.[/]\n\n")
            troubleshoot.append("  [#64748b]Troubleshooting:[/]\n")
            tips = [
                ("Check the error messages above", "#fb7185"),
                ("Review the migration logs", "#fbbf24"),
                ("Your backup is available for restoration", "#22d3ee"),
                ("Consult PostgreSQL 18 release notes", "#a78bfa"),
            ]
            for tip, color in tips:
                troubleshoot.append(f"    [{color}]{BOX_CHARS['arrow']}[/] [{color}]{tip}[/]\n")
            troubleshoot.append("\n")
            self.console.print(troubleshoot)


# ──────────────────────────────────────────────────────────
# Migration Wizard (Orchestrator)
# ──────────────────────────────────────────────────────────
class MigrationWizard:
    """Main wizard that orchestrates all screens."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or create_console()

        self.welcome = WelcomeScreen(self.console)
        self.connection = ConnectionScreen(self.console)
        self.version = VersionScreen(self.console)
        self.analysis = AnalysisScreen(self.console)
        self.migration = MigrationScreen(self.console)
        self.summary = SummaryScreen(self.console)

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
                self.console.print(f"\n  [#64748b]Migration cancelled.[/]")
                return False

            # Get connection details
            self.console.clear()
            self.console.print(create_header())

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

            from ..analyzer import analyze_compatibility
            from ..detector import VersionDetector
            from ..logger import get_logger
            from ..migrator import MigrationContext, MigrationEngine, MigrationMethod

            logger = get_logger()

            # Test connections
            self.console.print()
            self.console.print(create_divider("Testing Connections"))

            source_version = None
            target_version = None

            # Loading animation
            create_loading_animation(self.console, "Connecting to source", duration=0.5)

            try:
                with VersionDetector(source_dsn) as detector:
                    source_version = detector.detect_version()
                    if source_version:
                        self.console.print(create_status_indicator("success", f"Source: PostgreSQL {source_version}"))
                    else:
                        self.console.print(create_status_indicator("error", "Cannot connect to source database"))
                        return False
            except Exception as e:
                self.console.print(create_status_indicator("error", f"Source connection error: {e}"))
                return False

            create_loading_animation(self.console, "Connecting to target", duration=0.5)

            try:
                with VersionDetector(target_dsn) as detector:
                    target_version = detector.detect_version()
                    if target_version:
                        self.console.print(create_status_indicator("success", f"Target: PostgreSQL {target_version}"))
            except Exception:
                self.console.print(create_status_indicator("warning", "Target database may not exist, attempting to create..."))

                from ..db_manager import DatabaseManager

                try:
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
                        self.console.print(create_status_indicator("success", f"Created target database: {target_conn['database']}"))

                        with VersionDetector(target_dsn) as detector:
                            target_version = detector.detect_version()
                            if target_version:
                                self.console.print(create_status_indicator("success", f"Target: PostgreSQL {target_version}"))
                            else:
                                self.console.print(create_status_indicator("error", "Cannot connect to newly created database"))
                                return False
                    else:
                        self.console.print(create_status_indicator("error", f"Failed to create target database: {msg}"))
                        return False
                except Exception as create_error:
                    self.console.print(create_status_indicator("error", f"Cannot create target database: {create_error}"))
                    return False

            # Show version detection
            self.version.show_detection(str(source_version), str(target_version))

            # Analyze compatibility
            self.console.print()
            create_loading_animation(self.console, "Analyzing compatibility", duration=0.5)

            try:
                result = analyze_compatibility(source_dsn, source_version.major)
                summary = result.get_summary()

                self.analysis.show_analysis({
                    "summary": summary,
                    "issues": [i.to_dict() for i in result.issues],
                })

                can_proceed = summary.get("can_proceed", True)
            except Exception as e:
                self.console.print(create_status_indicator("error", f"Analysis error: {e}"))
                can_proceed = True

            # Ask to proceed
            self.console.print()
            proceed = Confirm.ask(
                f"[bold #22d3ee]{BOX_CHARS['arrow']} Proceed with migration?[/bold #22d3ee]",
                default=can_proceed,
                console=self.console,
            )

            if not proceed:
                self.console.print(f"\n  [#64748b]Migration cancelled by user.[/]")
                return False

            # Run migration
            self.console.print()
            self.console.print(create_divider("Performing Migration"))
            self.console.print()

            context = MigrationContext(
                source_dsn=source_dsn,
                target_dsn=target_dsn,
                method=MigrationMethod.PYTHON,
                dry_run=False,
            )

            engine = MigrationEngine(context)
            success = engine.run()

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
            self.console.print(f"\n\n  [#fbbf24]Migration interrupted by user.[/]")
            return False
        except Exception as e:
            self.console.print(f"\n  [#fb7185]Error: {e}[/]")
            return False
