"""
Reusable UI components for the PostgreSQL Migrator.
Premium, animated Rich components with neon dark aesthetic.
"""

import time
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.box import DOUBLE, HEAVY, ROUNDED, SIMPLE
from rich.columns import Columns
from rich.console import Console, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .theme import (
    BANNER_ART,
    BANNER_COMPACT,
    BOX_CHARS,
    COLORS,
    PROGRESS_CHARS,
    SEPARATOR_GLOW,
    SPINNERS,
    VERSION_FLOW,
    get_theme,
)


# ──────────────────────────────────────────────────────────
# Console Factory
# ──────────────────────────────────────────────────────────
def create_console() -> Console:
    """Create a themed Rich console."""
    return Console(theme=get_theme(), force_terminal=True)


# ──────────────────────────────────────────────────────────
# Header & Banner Components
# ──────────────────────────────────────────────────────────
def create_header(title: str = "PG Migrator", subtitle: str = "PostgreSQL Migration Tool") -> Panel:
    """
    Create the main header with pyfiglet banner and neon gradient.

    Args:
        title: Main title text
        subtitle: Subtitle text

    Returns:
        Rich Panel containing the header
    """
    import pyfiglet

    content = Text()

    # Generate banner using pyfiglet with neon gradient
    banner_text = pyfiglet.figlet_format("PG MIGRATOR", font="slant")
    lines = banner_text.strip().split("\n")
    gradient_colors = ["#22d3ee", "#2dd4bf", "#818cf8", "#a78bfa", "#c084fc", "#e879f9"]

    for i, line in enumerate(lines):
        color = gradient_colors[i % len(gradient_colors)]
        content.append(line, style=f"bold {color}")
        content.append("\n")

    content.append("\n")
    content.append(f"    {subtitle}", style="#94a3b8")
    content.append("  ")
    content.append("v1.0", style="bold #a78bfa")
    content.append("\n\n")

    # Version flow with neon colors
    content.append("        ")
    content.append(" 14 ", style="bold #fb7185")
    content.append(" >> ", style="#334155")
    content.append(" 15 ", style="bold #fbbf24")
    content.append(" >> ", style="#334155")
    content.append(" 16 ", style="bold #a3e635")
    content.append(" >> ", style="#334155")
    content.append(" 17 ", style="bold #34d399")
    content.append(" >> ", style="#334155")
    content.append(" 18 ", style="bold #22d3ee")

    return Panel(
        Align.center(content),
        border_style="#334155",
        box=ROUNDED,
        padding=(1, 2),
    )


def create_compact_header() -> Panel:
    """Create a compact header for smaller terminals."""
    return Panel(
        Text.from_markup(BANNER_COMPACT),
        border_style="#334155",
        box=ROUNDED,
        padding=(0, 1),
    )


# ──────────────────────────────────────────────────────────
# Panel Components
# ──────────────────────────────────────────────────────────
def create_panel(
    content: RenderableType,
    title: str,
    subtitle: Optional[str] = None,
    border_color: str = "border_subtle",
    expand: bool = True,
) -> Panel:
    """
    Create a styled glass-effect panel.

    Args:
        content: Panel content
        title: Panel title
        subtitle: Optional subtitle
        border_color: Border color from COLORS dict
        expand: Whether panel should expand to fill space

    Returns:
        Styled Rich Panel
    """
    color = COLORS.get(border_color, border_color)
    return Panel(
        content,
        title=f"[bold #22d3ee] {title} [/bold #22d3ee]",
        subtitle=f"[#64748b]{subtitle}[/#64748b]" if subtitle else None,
        border_style=color,
        box=ROUNDED,
        expand=expand,
        padding=(1, 2),
    )


def create_glass_panel(
    content: RenderableType,
    title: str,
    accent_color: str = "#22d3ee",
) -> Panel:
    """Create a premium glass-morphism style panel with accent strip."""
    title_text = Text()
    title_text.append(f" {BOX_CHARS['diamond']} ", style=f"bold {accent_color}")
    title_text.append(title, style=f"bold {accent_color}")
    title_text.append(f" {BOX_CHARS['diamond']} ", style=f"bold {accent_color}")

    return Panel(
        content,
        title=title_text,
        border_style="#334155",
        box=ROUNDED,
        expand=True,
        padding=(1, 3),
    )


# ──────────────────────────────────────────────────────────
# Status Indicators
# ──────────────────────────────────────────────────────────
def create_status_indicator(
    status: str,
    message: str,
    details: Optional[str] = None,
) -> Text:
    """
    Create a modern status indicator with neon icon.

    Args:
        status: One of 'success', 'warning', 'error', 'info', 'pending', 'running', 'check'
        message: Status message
        details: Optional additional details

    Returns:
        Styled Text object
    """
    icons = {
        "success": "●",
        "warning": "▲",
        "error": "✗",
        "info": "◆",
        "pending": "○",
        "running": "◉",
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

    icon = icons.get(status, "●")
    style = styles.get(status, "default")

    text = Text()
    text.append(f" {icon} ", style=style)
    text.append(message, style=style)

    if details:
        text.append(f"\n     {details}", style="dim")

    return text


# ──────────────────────────────────────────────────────────
# Progress Bars
# ──────────────────────────────────────────────────────────
def create_progress_bar(
    description: str = "Processing...",
    show_speed: bool = False,
) -> Progress:
    """
    Create a modern neon progress bar.

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
            style="#334155",
            complete_style="#22d3ee",
            finished_style="#34d399",
            pulse_style="#a78bfa",
        ),
        TaskProgressColumn(),
        TextColumn("[#64748b]|[/#64748b]"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ]

    return Progress(*columns, expand=True)


# ──────────────────────────────────────────────────────────
# Tables
# ──────────────────────────────────────────────────────────
def create_database_table(
    source_info: Dict[str, Any],
    target_info: Optional[Dict[str, Any]] = None,
) -> Table:
    """
    Create a modern table showing database connection details.

    Args:
        source_info: Source database information
        target_info: Target database information (optional)

    Returns:
        Rich Table
    """
    table = Table(
        show_header=True,
        header_style="bold #22d3ee",
        box=ROUNDED,
        border_style="#334155",
        expand=True,
        row_styles=["", "#1e293b"],
        pad_edge=True,
        padding=(0, 1),
    )

    table.add_column("", style="#64748b", width=3, justify="center")
    table.add_column("Property", style="#94a3b8", width=15)
    table.add_column("Source DB", style="#f1f5f9")
    if target_info:
        table.add_column("Target DB", style="#f1f5f9")

    properties = [
        ("●", "Host"), ("●", "Port"), ("●", "Database"),
        ("●", "User"), ("●", "Version"), ("●", "Status"),
    ]

    for icon, prop in properties:
        key = prop.lower()
        source_val = source_info.get(key, "---")
        if target_info:
            target_val = target_info.get(key, "---")
            table.add_row(f"[#334155]{icon}[/]", prop, str(source_val), str(target_val))
        else:
            table.add_row(f"[#334155]{icon}[/]", prop, str(source_val))

    return table


def create_compatibility_table(issues: List[Dict[str, Any]]) -> Table:
    """
    Create a modern table showing compatibility issues.

    Args:
        issues: List of compatibility issues

    Returns:
        Rich Table
    """
    table = Table(
        show_header=True,
        header_style="bold #22d3ee",
        box=ROUNDED,
        border_style="#334155",
        expand=True,
        title="[bold #a78bfa] Compatibility Analysis [/bold #a78bfa]",
        title_style="bold",
        row_styles=["", "#1e293b"],
        pad_edge=True,
        padding=(0, 1),
    )

    table.add_column("", width=5, justify="center")
    table.add_column("Category", width=15, style="#94a3b8")
    table.add_column("Issue", width=40, style="#f1f5f9")
    table.add_column("Recommendation", width=35, style="#64748b")

    severity_styles = {
        "critical": ("✗", "#fb7185"),
        "warning": ("▲", "#fbbf24"),
        "info": ("◆", "#60a5fa"),
    }

    for issue in issues:
        severity = issue.get("severity", "info")
        icon, color = severity_styles.get(severity, ("●", "#94a3b8"))

        table.add_row(
            f"[bold {color}]{icon}[/]",
            issue.get("category", "---"),
            issue.get("message", "---"),
            issue.get("recommendation", "---"),
        )

    return table


# ──────────────────────────────────────────────────────────
# Step Indicators
# ──────────────────────────────────────────────────────────
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
    content.append("\n")

    for i, step in enumerate(steps):
        is_current = i == current_step
        is_completed = i < current_step

        if is_completed:
            icon = "✓"
            color = "#34d399"
            bar = f"[#334155]{'━' * 30}[/]"
        elif is_current:
            icon = "◉"
            color = "#22d3ee"
            bar = f"[{color}]{'━' * 15}[/][#334155]{'╌' * 15}[/]"
        else:
            icon = "○"
            color = "#334155"
            bar = f"[#1e293b]{'╌' * 30}[/]"

        step_text = f"  [{color}]{icon}[/]  "
        if is_current:
            step_text += f"[bold {color}]Step {i + 1}: {step['name']}[/]"
        else:
            step_text += f"[{color}]Step {i + 1}: {step['name']}[/]"

        content.append_text(Text.from_markup(step_text))
        content.append("\n")

    content.append("\n")

    return create_glass_panel(content, "Migration Progress", accent_color="#22d3ee")


# ──────────────────────────────────────────────────────────
# Summary Panel
# ──────────────────────────────────────────────────────────
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
    content = Text()

    if success:
        icon = "✓"
        title = "Migration Completed Successfully"
        accent = "#34d399"
    else:
        icon = "✗"
        title = "Migration Failed"
        accent = "#fb7185"

    content.append(f"\n  {icon} ", style=f"bold {accent}")
    content.append(title, style=f"bold {accent}")
    content.append("\n\n")

    for key, value in stats.items():
        content.append(f"    {BOX_CHARS['arrow']} ", style="#334155")
        content.append(f"{key}: ", style="#94a3b8")
        content.append(f"{value}\n", style="#f1f5f9")

    content.append(f"\n    Duration: {duration}\n", style="#64748b")

    return create_glass_panel(content, "Summary", accent_color=accent)


# ──────────────────────────────────────────────────────────
# Input Components
# ──────────────────────────────────────────────────────────
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
    prompt_parts = [f"[bold #22d3ee]{BOX_CHARS['arrow']}[/bold #22d3ee] [#f1f5f9]{label}[/#f1f5f9]"]

    if hint:
        prompt_parts.append(f" [#64748b]({hint})[/#64748b]")

    if default and not password:
        prompt_parts.append(f" [#334155]\\[{default}][/#334155]")

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
    content.append("\n")

    for i, option in enumerate(options):
        is_selected = i == selected

        key = option.get("key", str(i + 1))
        label = option.get("label", "Option")
        desc = option.get("description", "")

        if is_selected:
            content.append(f"  [bold #22d3ee]{BOX_CHARS['arrow']}[/] ")
            content.append(f"[{key}] {label}", style="bold #22d3ee")
        else:
            content.append(f"  [#334155]{BOX_CHARS['circle']}[/] ")
            content.append(f"[{key}] {label}", style="#94a3b8")

        if desc:
            content.append(f"  {desc}", style="#64748b")

        content.append("\n")

    content.append("\n")

    return create_glass_panel(content, title)


def create_divider(text: Optional[str] = None) -> Rule:
    """
    Create a styled divider/rule.

    Args:
        text: Optional centered text

    Returns:
        Rich Rule
    """
    if text:
        rule_text = Text(text, style="bold #a78bfa")
        return Rule(rule_text, style="#334155")
    return Rule(style="#334155")


# ──────────────────────────────────────────────────────────
# Live Migration Tracker (Premium Animated)
# ──────────────────────────────────────────────────────────
class LiveMigrationTracker:
    """
    Animated migration progress tracker with live updates.
    Shows animated spinners, neon progress bars, and real-time stats.
    """

    STEPS = [
        ("connect", "Connecting to Databases", "connect"),
        ("detect", "Detecting Versions", "detect"),
        ("analyze", "Analyzing Compatibility", "analyze"),
        ("prepare", "Preparing Target", "prepare"),
        ("backup", "Creating Backup", "backup"),
        ("migrate", "Migrating Data", "migrate"),
        ("validate", "Validating Migration", "validate"),
    ]

    def __init__(self, console: Console):
        self.console = console
        self.current_step = 0
        self.current_progress = 0
        self.status_message = ""
        self.step_statuses = ["pending"] * len(self.STEPS)
        self.start_time: Optional[float] = None
        self.stats = {
            "tables": 0,
            "rows": 0,
            "schemas": 0,
        }

    def _generate_display(self) -> Panel:
        """Generate the current progress display with neon aesthetic."""
        content = Text()

        # Header with elapsed time
        elapsed = ""
        if self.start_time:
            elapsed_sec = time.time() - self.start_time
            minutes = int(elapsed_sec // 60)
            secs = int(elapsed_sec % 60)
            elapsed = f" [{minutes:02d}:{secs:02d}]"

        content.append(f"\n  Migration in Progress{elapsed}\n\n", style="bold #22d3ee")

        # Step progress with neon bars
        spinner_chars = SPINNERS["dots"]

        for i, (step_id, step_name, _) in enumerate(self.STEPS):
            status = self.step_statuses[i]

            if status == "completed":
                icon = "✓"
                color = "#34d399"
                pct = "100%"
                bar_filled = 20
                bar_empty = 0
            elif status == "running":
                spinner_idx = int(time.time() * 8) % len(spinner_chars)
                icon = spinner_chars[spinner_idx]
                color = "#22d3ee"
                pct = f"{self.current_progress:3d}%"
                bar_filled = max(0, int(self.current_progress / 5))
                bar_empty = 20 - bar_filled
            elif status == "skipped":
                icon = "─"
                color = "#64748b"
                pct = "skip"
                bar_filled = 0
                bar_empty = 20
            elif status == "failed":
                icon = "✗"
                color = "#fb7185"
                pct = "fail"
                bar_filled = 0
                bar_empty = 20
            else:  # pending
                icon = "○"
                color = "#334155"
                pct = "  0%"
                bar_filled = 0
                bar_empty = 20

            # Build the bar
            if status == "running":
                bar = f"[{color}]{'━' * bar_filled}[/][#334155]{'╌' * bar_empty}[/]"
            elif status == "completed":
                bar = f"[{color}]{'━' * bar_filled}[/]"
            else:
                bar = f"[#1e293b]{'╌' * 20}[/]"

            line = f"  [{color}]{icon}[/]  [{color}]{step_name:<25}[/] {bar} [{color}]{pct}[/]\n"
            content.append_text(Text.from_markup(line))

        # Status message
        if self.status_message:
            content.append(f"\n  {BOX_CHARS['arrow']} ", style="#334155")
            content.append(f"{self.status_message}\n", style="#94a3b8")

        # Stats
        if self.stats["tables"] > 0 or self.stats["rows"] > 0:
            content.append_text(Text.from_markup(
                f"\n  [#334155]{'─' * 50}[/]\n"
            ))
            stats_line = (
                f"  [#64748b]Tables:[/] [#f1f5f9]{self.stats['tables']}[/]"
                f"  [#334155]|[/]  "
                f"[#64748b]Rows:[/] [#f1f5f9]{self.stats['rows']:,}[/]"
                f"  [#334155]|[/]  "
                f"[#64748b]Schemas:[/] [#f1f5f9]{self.stats['schemas']}[/]\n"
            )
            content.append_text(Text.from_markup(stats_line))

        content.append("\n")

        return Panel(
            content,
            title="[bold #a78bfa] Live Migration [/bold #a78bfa]",
            border_style="#334155",
            box=ROUNDED,
            padding=(0, 1),
        )

    def start(self):
        """Mark migration as started."""
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


# ──────────────────────────────────────────────────────────
# Premium Animations
# ──────────────────────────────────────────────────────────
def create_animated_banner(console: Console):
    """Display animated startup banner with smooth typing effect."""
    blue = "#334155"
    cyan = "#22d3ee"
    purple = "#a78bfa"

    gradient_colors = ["#22d3ee", "#2dd4bf", "#818cf8", "#a78bfa", "#c084fc", "#e879f9"]

    # Top border
    console.print(f"  [bold {blue}]{'─' * 66}[/]")
    time.sleep(0.02)

    # Banner lines with gradient
    import pyfiglet
    banner_text = pyfiglet.figlet_format("PG MIGRATOR", font="slant")
    lines = banner_text.strip().split("\n")

    for i, line in enumerate(lines):
        color = gradient_colors[i % len(gradient_colors)]
        console.print(f"  [bold {color}]{line}[/]")
        time.sleep(0.03)

    console.print()
    console.print(f"  [#94a3b8]PostgreSQL Migration Wizard[/]  [{purple}]v1.0[/]")
    time.sleep(0.02)

    # Version flow with reveal
    console.print()
    versions = [
        (" 14 ", "#fb7185"), (" 15 ", "#fbbf24"), (" 16 ", "#a3e635"),
        (" 17 ", "#34d399"), (" 18 ", "#22d3ee"),
    ]

    flow = Text("  ")
    for j, (ver, color) in enumerate(versions):
        flow.append(ver, style=f"bold {color}")
        if j < len(versions) - 1:
            flow.append(" >> ", style="#334155")
        console.print(flow, end="\r")
        time.sleep(0.08)
    console.print(flow)

    console.print(f"\n  [bold {blue}]{'─' * 66}[/]")
    console.print()


def create_loading_animation(console: Console, message: str = "Loading", duration: float = 1.0):
    """Display a modern loading animation with braille spinner."""
    spinners = SPINNERS["dots"]

    start = time.time()
    spinner_idx = 0

    with Live(console=console, refresh_per_second=12) as live:
        while time.time() - start < duration:
            spinner = spinners[spinner_idx % len(spinners)]
            text = Text()
            text.append(f"  {spinner} ", style="#22d3ee")
            text.append(message, style="#94a3b8")
            text.append("...", style="#334155")
            live.update(text)
            spinner_idx += 1
            time.sleep(0.08)


def create_success_animation(console: Console):
    """Display success animation with neon glow effect."""
    frames = [
        ("○", "#334155"),
        ("◎", "#334155"),
        ("◉", "#2dd4bf"),
        ("●", "#34d399"),
        ("✓", "#34d399"),
        ("✓ Done", "#34d399"),
    ]

    for icon, color in frames:
        console.print(f"  [bold {color}]{icon}[/]", end="\r")
        time.sleep(0.08)
    console.print(f"  [bold #34d399]✓ Done[/]")


def create_wave_animation(console: Console, message: str = "Processing", duration: float = 1.5):
    """Display a modern wave progress animation."""
    wave_chars = SPINNERS["wave"]
    bar_width = 30

    start = time.time()
    frame = 0

    with Live(console=console, refresh_per_second=15) as live:
        while time.time() - start < duration:
            text = Text()
            text.append("  ", style="#334155")

            # Build wave bar
            for i in range(bar_width):
                char_idx = (frame + i) % len(wave_chars)
                # Color gradient across the bar
                if i < bar_width // 3:
                    color = "#22d3ee"
                elif i < 2 * bar_width // 3:
                    color = "#818cf8"
                else:
                    color = "#a78bfa"
                text.append(wave_chars[char_idx], style=color)

            text.append(f"  {message}", style="#94a3b8")
            live.update(text)
            frame += 1
            time.sleep(0.06)


def create_progress_animation(
    console: Console,
    total: int,
    description: str = "Processing",
) -> Progress:
    """Create a fancy animated progress bar with neon aesthetic."""
    return Progress(
        SpinnerColumn(spinner_name="dots12", style="#22d3ee"),
        TextColumn("[bold #f1f5f9]{task.description}[/]"),
        BarColumn(
            bar_width=50,
            style="#334155",
            complete_style="#22d3ee",
            finished_style="#34d399",
            pulse_style="#a78bfa",
        ),
        TextColumn("[bold #2dd4bf]{task.percentage:>3.0f}%[/]"),
        TextColumn("[#334155]|[/]"),
        TimeElapsedColumn(),
        TextColumn("[#334155]|[/]"),
        TimeRemainingColumn(),
        console=console,
        expand=True,
        transient=False,
    )
