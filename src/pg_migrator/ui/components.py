"""
Reusable UI components for the PostgreSQL Migrator.
Beautiful, animated Rich components for terminal interface.
"""

from typing import Optional, List, Dict, Any
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.rule import Rule
from rich.box import ROUNDED, DOUBLE, HEAVY, MINIMAL

from .theme import COLORS, BANNER_ART, BANNER_COMPACT, VERSION_FLOW, get_theme


def create_console() -> Console:
    """Create a themed Rich console."""
    return Console(theme=get_theme(), force_terminal=True)


def create_header(title: str = "PG Migrator", subtitle: str = "PostgreSQL Migration Tool") -> Panel:
    """
    Create the main header with pyfiglet banner.
    
    Args:
        title: Main title text
        subtitle: Subtitle text
        
    Returns:
        Rich Panel containing the header
    """
    import pyfiglet
    
    content = Text()
    
    # Generate banner using pyfiglet
    banner_text = pyfiglet.figlet_format("PG MIGRATOR", font="slant")
    lines = banner_text.strip().split('\n')
    colors = ["#38b2ac", "#319795", "#2c7a7b", "#285e61", "#234e52", "#1d4044"]
    
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        content.append(line, style=f"bold {color}")
        content.append("\n")
    
    content.append("\n")
    content.append(f"    {subtitle}", style="#4299e1")
    content.append("\n\n")
    
    # Version flow with colors
    content.append("        ")
    content.append("14", style="bold #e53e3e")
    content.append(" → ", style="dim")
    content.append("15", style="bold #ed8936")
    content.append(" → ", style="dim")
    content.append("16", style="bold #ecc94b")
    content.append(" → ", style="dim")
    content.append("17", style="bold #48bb78")
    content.append(" → ", style="dim")
    content.append("18", style="bold #4299e1")
    
    return Panel(
        Align.center(content),
        border_style=COLORS["pg_blue"],
        box=DOUBLE,
        padding=(1, 2),
    )


def create_compact_header() -> Panel:
    """Create a compact header for smaller terminals."""
    return Panel(
        Text.from_markup(BANNER_COMPACT),
        border_style=COLORS["pg_blue"],
        box=ROUNDED,
        padding=(0, 1),
    )


def create_panel(
    content: RenderableType,
    title: str,
    subtitle: Optional[str] = None,
    border_color: str = "pg_blue",
    expand: bool = True,
) -> Panel:
    """
    Create a styled panel.
    
    Args:
        content: Panel content
        title: Panel title
        subtitle: Optional subtitle
        border_color: Border color from COLORS dict
        expand: Whether panel should expand to fill space
        
    Returns:
        Styled Rich Panel
    """
    return Panel(
        content,
        title=f"[bold]{title}[/bold]",
        subtitle=subtitle,
        border_style=COLORS.get(border_color, border_color),
        box=ROUNDED,
        expand=expand,
        padding=(1, 2),
    )


def create_status_indicator(
    status: str,
    message: str,
    details: Optional[str] = None,
) -> Text:
    """
    Create a status indicator with icon.
    
    Args:
        status: One of 'success', 'warning', 'error', 'info', 'pending'
        message: Status message
        details: Optional additional details
        
    Returns:
        Styled Text object
    """
    icons = {
        "success": "✅",
        "warning": "⚠️ ",
        "error": "❌",
        "info": "ℹ️ ",
        "pending": "⏳",
        "running": "🔄",
        "check": "✓",
    }
    
    styles = {
        "success": "status.success",
        "warning": "status.warning",
        "error": "status.error",
        "info": "status.info",
        "pending": "status.pending",
        "running": "pg.accent",
        "check": "status.success",
    }
    
    icon = icons.get(status, "•")
    style = styles.get(status, "default")
    
    text = Text()
    text.append(f"{icon} ", style=style)
    text.append(message, style=style)
    
    if details:
        text.append(f"\n   {details}", style="dim")
    
    return text


def create_progress_bar(
    description: str = "Processing...",
    show_speed: bool = False,
) -> Progress:
    """
    Create an animated progress bar.
    
    Args:
        description: Progress description
        show_speed: Whether to show speed
        
    Returns:
        Rich Progress object
    """
    columns = [
        SpinnerColumn(spinner_name="dots", style=COLORS["pg_cyan"]),
        TextColumn("[progress.description]{task.description}", style="bold"),
        BarColumn(
            bar_width=40,
            style=COLORS["pg_blue_dark"],
            complete_style=COLORS["pg_cyan"],
            finished_style=COLORS["success"],
        ),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ]
    
    return Progress(*columns, expand=True)


def create_database_table(
    source_info: Dict[str, Any],
    target_info: Optional[Dict[str, Any]] = None,
) -> Table:
    """
    Create a table showing database connection details.
    
    Args:
        source_info: Source database information
        target_info: Target database information (optional)
        
    Returns:
        Rich Table
    """
    table = Table(
        show_header=True,
        header_style="table.header",
        box=ROUNDED,
        border_style=COLORS["pg_blue"],
        expand=True,
    )
    
    table.add_column("Property", style="pg.accent", width=20)
    table.add_column("Source DB", style="text_primary")
    if target_info:
        table.add_column("Target DB", style="text_primary")
    
    properties = ["Host", "Port", "Database", "User", "Version", "Status"]
    
    for prop in properties:
        key = prop.lower()
        source_val = source_info.get(key, "—")
        
        if target_info:
            target_val = target_info.get(key, "—")
            table.add_row(prop, str(source_val), str(target_val))
        else:
            table.add_row(prop, str(source_val))
    
    return table


def create_compatibility_table(issues: List[Dict[str, Any]]) -> Table:
    """
    Create a table showing compatibility issues.
    
    Args:
        issues: List of compatibility issues
        
    Returns:
        Rich Table
    """
    table = Table(
        show_header=True,
        header_style="table.header",
        box=ROUNDED,
        border_style=COLORS["pg_blue"],
        expand=True,
        title="[bold]Compatibility Analysis[/bold]",
    )
    
    table.add_column("Severity", width=10, justify="center")
    table.add_column("Category", width=15)
    table.add_column("Issue", width=40)
    table.add_column("Recommendation", width=35)
    
    severity_styles = {
        "critical": ("❌", "error"),
        "warning": ("⚠️ ", "warning"),
        "info": ("ℹ️ ", "info"),
    }
    
    for issue in issues:
        severity = issue.get("severity", "info")
        icon, style = severity_styles.get(severity, ("•", "default"))
        
        table.add_row(
            f"[{style}]{icon}[/{style}]",
            issue.get("category", "—"),
            issue.get("message", "—"),
            issue.get("recommendation", "—"),
        )
    
    return table


def create_step_indicator(steps: List[Dict[str, str]], current_step: int) -> Panel:
    """
    Create a visual step indicator showing migration progress.
    
    Args:
        steps: List of step dictionaries with 'name' and 'status'
        current_step: Index of current step (0-based)
        
    Returns:
        Rich Panel with step indicator
    """
    content = Text()
    
    for i, step in enumerate(steps):
        is_current = i == current_step
        is_completed = i < current_step
        
        if is_completed:
            icon = "✅"
            style = "status.success"
        elif is_current:
            icon = "🔄"
            style = "pg.highlight"
        else:
            icon = "○ "
            style = "dim"
        
        step_text = f"  {icon} Step {i + 1}: {step['name']}"
        
        if is_current:
            step_text = f"[bold]{step_text}[/bold]"
        
        content.append(step_text + "\n", style=style)
    
    return create_panel(content, "Migration Progress", border_color="pg_blue_light")


def create_summary_panel(
    success: bool,
    stats: Dict[str, Any],
    duration: str,
) -> Panel:
    """
    Create a summary panel showing migration results.
    
    Args:
        success: Whether migration was successful
        stats: Dictionary of migration statistics
        duration: Total duration string
        
    Returns:
        Rich Panel with summary
    """
    if success:
        icon = "🎉"
        title = "Migration Completed Successfully!"
        border_color = "success"
    else:
        icon = "❌"
        title = "Migration Failed"
        border_color = "error"
    
    content = Text()
    content.append(f"\n{icon} {title}\n\n", style="bold")
    
    for key, value in stats.items():
        content.append(f"  • {key}: ", style="pg.accent")
        content.append(f"{value}\n", style="text_primary")
    
    content.append(f"\n  ⏱️  Total Duration: {duration}\n", style="dim")
    
    return create_panel(content, "Summary", border_color=border_color)


def create_input_prompt(
    label: str,
    default: Optional[str] = None,
    password: bool = False,
    hint: Optional[str] = None,
) -> str:
    """
    Create a styled input prompt string.
    
    Args:
        label: Input label
        default: Default value
        password: Whether this is a password field
        hint: Optional hint text
        
    Returns:
        Formatted prompt string
    """
    prompt_parts = [f"[input.label]{label}[/input.label]"]
    
    if hint:
        prompt_parts.append(f" [dim]({hint})[/dim]")
    
    if default and not password:
        prompt_parts.append(f" [dim]\\[{default}][/dim]")
    
    prompt_parts.append(": ")
    
    return "".join(prompt_parts)


def create_menu(
    title: str,
    options: List[Dict[str, str]],
    selected: int = 0,
) -> Panel:
    """
    Create an interactive menu display.
    
    Args:
        title: Menu title
        options: List of options with 'key', 'label', and optional 'description'
        selected: Currently selected option index
        
    Returns:
        Rich Panel with menu
    """
    content = Text()
    
    for i, option in enumerate(options):
        is_selected = i == selected
        
        key = option.get("key", str(i + 1))
        label = option.get("label", "Option")
        desc = option.get("description", "")
        
        if is_selected:
            content.append(f"  ▶ [{key}] {label}", style="pg.highlight")
        else:
            content.append(f"    [{key}] {label}", style="pg.accent")
        
        if desc:
            content.append(f"  {desc}", style="dim")
        
        content.append("\n")
    
    return create_panel(content, title, border_color="pg_blue")


def create_divider(text: Optional[str] = None) -> Rule:
    """
    Create a styled divider/rule.
    
    Args:
        text: Optional centered text
        
    Returns:
        Rich Rule
    """
    return Rule(text, style=COLORS["pg_blue"])


class LiveMigrationTracker:
    """
    Animated migration progress tracker with live updates.
    Shows animated spinners, progress bars, and real-time stats.
    """
    
    STEPS = [
        ("connect", "Connecting to Databases", "🔌"),
        ("detect", "Detecting Versions", "🔍"),
        ("analyze", "Analyzing Compatibility", "📊"),
        ("prepare", "Preparing Target", "🎯"),
        ("backup", "Creating Backup", "💾"),
        ("migrate", "Migrating Data", "🚀"),
        ("validate", "Validating Migration", "✅"),
    ]
    
    def __init__(self, console: Console):
        self.console = console
        self.current_step = 0
        self.current_progress = 0
        self.status_message = ""
        self.step_statuses = ["pending"] * len(self.STEPS)
        self.start_time = None
        self.stats = {
            "tables": 0,
            "rows": 0,
            "schemas": 0,
        }
    
    def _generate_display(self) -> Panel:
        """Generate the current progress display."""
        from datetime import datetime
        import time
        
        content = Text()
        
        # Header with animated dots
        elapsed = ""
        if self.start_time:
            elapsed_sec = time.time() - self.start_time
            elapsed = f" ({elapsed_sec:.1f}s)"
        
        content.append(f"\n  🚀 Migration in Progress{elapsed}\n\n", style="bold pg.highlight")
        
        # Step progress with icons
        for i, (step_id, step_name, icon) in enumerate(self.STEPS):
            status = self.step_statuses[i]
            
            if status == "completed":
                status_icon = "✅"
                style = "status.success"
                bar = "█" * 10
            elif status == "running":
                # Animated spinner effect using different characters
                spinners = ["◐", "◓", "◑", "◒"]
                import time
                spinner_idx = int(time.time() * 4) % 4
                status_icon = spinners[spinner_idx]
                style = "pg.highlight"
                # Animated progress bar
                filled = int(self.current_progress / 10)
                bar = "█" * filled + "▓" * (1 if filled < 10 else 0) + "░" * (9 - filled)
            elif status == "skipped":
                status_icon = "⏭️"
                style = "dim"
                bar = "─" * 10
            elif status == "failed":
                status_icon = "❌"
                style = "status.error"
                bar = "░" * 10
            else:  # pending
                status_icon = "○"
                style = "dim"
                bar = "░" * 10
            
            # Progress percentage for current step
            if status == "running":
                pct = f"{self.current_progress:3d}%"
            elif status == "completed":
                pct = "100%"
            else:
                pct = "  0%"
            
            line = f"  {status_icon} {icon} {step_name:<25} [{bar}] {pct}\n"
            content.append(line, style=style)
        
        # Status message
        if self.status_message:
            content.append(f"\n  📋 {self.status_message}\n", style="pg.accent")
        
        # Stats
        if self.stats["tables"] > 0 or self.stats["rows"] > 0:
            content.append("\n  ─────────────────────────────────────────\n", style="dim")
            stats_line = f"  📊 Tables: {self.stats['tables']}  |  Rows: {self.stats['rows']:,}  |  Schemas: {self.stats['schemas']}\n"
            content.append(stats_line, style="text_primary")
        
        content.append("\n")
        
        return Panel(
            content,
            title="[bold]🔄 Live Migration Progress[/bold]",
            border_style=COLORS["pg_cyan"],
            box=ROUNDED,
            padding=(0, 1),
        )
    
    def start(self):
        """Mark migration as started."""
        import time
        self.start_time = time.time()
    
    def set_step(self, step_index: int, status: str = "running"):
        """Set a step's status."""
        if 0 <= step_index < len(self.STEPS):
            self.step_statuses[step_index] = status
            self.current_step = step_index
            if status == "running":
                self.current_progress = 0
    
    def complete_step(self, step_index: int):
        """Mark a step as completed."""
        if 0 <= step_index < len(self.STEPS):
            self.step_statuses[step_index] = "completed"
            self.current_progress = 100
    
    def skip_step(self, step_index: int):
        """Mark a step as skipped."""
        if 0 <= step_index < len(self.STEPS):
            self.step_statuses[step_index] = "skipped"
    
    def fail_step(self, step_index: int):
        """Mark a step as failed."""
        if 0 <= step_index < len(self.STEPS):
            self.step_statuses[step_index] = "failed"
    
    def update_progress(self, percentage: int, message: str = ""):
        """Update current step progress."""
        self.current_progress = min(100, max(0, percentage))
        if message:
            self.status_message = message
    
    def update_stats(self, tables: int = 0, rows: int = 0, schemas: int = 0):
        """Update migration statistics."""
        self.stats["tables"] = tables
        self.stats["rows"] = rows
        self.stats["schemas"] = schemas
    
    def render(self) -> Panel:
        """Render the current state."""
        return self._generate_display()


def create_animated_banner(console: Console):
    """Display animated startup banner with typing effect."""
    import time
    
    # Use direct color codes for reliability
    blue = "#336791"
    cyan = "#38b2ac"
    
    lines = [
        "",
        f"  [bold {blue}]╔══════════════════════════════════════════════════════════════════╗[/]",
        f"  [bold {blue}]║                                                                  ║[/]",
        f"  [bold {cyan}]║    ██████╗  ██████╗   ███╗   ███╗██╗ ██████╗ ██████╗  █████╗    ║[/]",
        f"  [bold {cyan}]║    ██╔══██╗██╔════╝   ████╗ ████║██║██╔════╝ ██╔══██╗██╔══██╗   ║[/]",
        f"  [bold {cyan}]║    ██████╔╝██║  ███╗  ██╔████╔██║██║██║  ███╗██████╔╝███████║   ║[/]",
        f"  [bold {cyan}]║    ██╔═══╝ ██║   ██║  ██║╚██╔╝██║██║██║   ██║██╔══██╗██╔══██║   ║[/]",
        f"  [bold {cyan}]║    ██║     ╚██████╔╝  ██║ ╚═╝ ██║██║╚██████╔╝██║  ██║██║  ██║   ║[/]",
        f"  [bold {cyan}]║    ╚═╝      ╚═════╝   ╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ║[/]",
        f"  [bold {blue}]║                                                                  ║[/]",
        f"  [bold {blue}]║[/]        [bold #4299e1]PostgreSQL Migration Wizard  v1.0[/]                   [bold {blue}]║[/]",
        f"  [bold {blue}]║[/]           [#e53e3e]14[/] [dim]→[/] [#ed8936]15[/] [dim]→[/] [#ecc94b]16[/] [dim]→[/] [#48bb78]17[/] [dim]→[/] [#4299e1]18[/]                      [bold {blue}]║[/]",
        f"  [bold {blue}]║                                                                  ║[/]",
        f"  [bold {blue}]╚══════════════════════════════════════════════════════════════════╝[/]",
        "",
    ]
    
    for line in lines:
        console.print(line)
        time.sleep(0.015)


def create_loading_animation(console: Console, message: str = "Loading", duration: float = 1.0):
    """Display a loading animation with spinner."""
    import time
    from rich.live import Live
    
    spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    start = time.time()
    spinner_idx = 0
    
    with Live(console=console, refresh_per_second=10) as live:
        while time.time() - start < duration:
            spinner = spinners[spinner_idx % len(spinners)]
            text = Text()
            text.append(f"  {spinner} ", style="pg.cyan")
            text.append(message, style="pg.accent")
            text.append("...", style="dim")
            live.update(text)
            spinner_idx += 1
            time.sleep(0.1)


def create_success_animation(console: Console):
    """Display success animation."""
    import time
    
    frames = [
        "    ✓    ",
        "   ✓✓    ",
        "  ✓✓✓    ",
        "  ✓✓✓✓   ",
        "  ✓✓✓✓✓  ",
        " 🎉✓✓✓✓✓🎉",
    ]
    
    for frame in frames:
        console.print(f"[bold green]{frame}[/bold green]", end="\r")
        time.sleep(0.1)
    console.print()


def create_progress_animation(
    console: Console,
    total: int,
    description: str = "Processing",
) -> Progress:
    """Create a fancy animated progress bar."""
    return Progress(
        SpinnerColumn(spinner_name="dots12", style="pg.cyan"),
        TextColumn("[bold]{task.description}[/bold]"),
        BarColumn(
            bar_width=50,
            style="pg_blue_dark",
            complete_style="pg_cyan",
            finished_style="success",
            pulse_style="pg.highlight",
        ),
        TextColumn("[bold]{task.percentage:>3.0f}%[/bold]"),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
        expand=True,
        transient=False,
    )

