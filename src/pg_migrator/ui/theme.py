"""
Rich Theme and Color Definitions for PostgreSQL Migrator.
A premium, modern color palette with neon accents, glass effects, and smooth gradients.
"""

from rich.style import Style
from rich.theme import Theme

# ──────────────────────────────────────────────────────────
# Modern PostgreSQL-inspired color palette (Neon Dark theme)
# ──────────────────────────────────────────────────────────
COLORS = {
    # Primary PostgreSQL Blue Gradient
    "pg_blue_darkest": "#0f172a",
    "pg_blue_dark": "#1e293b",
    "pg_blue": "#336791",           # Official PostgreSQL Blue
    "pg_blue_light": "#60a5fa",
    "pg_blue_lightest": "#bfdbfe",

    # Neon Accent Colors
    "pg_cyan": "#22d3ee",
    "pg_teal": "#2dd4bf",
    "pg_purple": "#a78bfa",
    "pg_indigo": "#818cf8",
    "pg_pink": "#f472b6",
    "pg_lime": "#a3e635",

    # Status Colors (vibrant neon)
    "success": "#34d399",
    "success_light": "#6ee7b7",
    "success_glow": "#10b981",
    "warning": "#fbbf24",
    "warning_light": "#fde68a",
    "warning_glow": "#f59e0b",
    "error": "#fb7185",
    "error_light": "#fda4af",
    "error_glow": "#f43f5e",
    "info": "#60a5fa",

    # Neutral Colors (deeper, richer dark theme)
    "bg_dark": "#0f172a",
    "bg_medium": "#1e293b",
    "bg_light": "#334155",
    "bg_card": "#1e293b",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border_subtle": "#334155",

    # Gradient Effect Colors (for ASCII art & accents)
    "gradient_1": "#818cf8",
    "gradient_2": "#a78bfa",
    "gradient_3": "#c084fc",
    "gradient_4": "#e879f9",
    "gradient_5": "#f472b6",
}


def get_theme() -> Theme:
    """Create and return the custom Rich theme."""
    return Theme({
        # Base styles
        "default": Style(color=COLORS["text_primary"]),
        "muted": Style(color=COLORS["text_muted"]),
        "dim": Style(color=COLORS["text_secondary"]),

        # PostgreSQL brand styles
        "pg.primary": Style(color=COLORS["pg_blue"], bold=True),
        "pg.accent": Style(color=COLORS["pg_cyan"]),
        "pg.highlight": Style(color=COLORS["pg_teal"], bold=True),
        "pg.version": Style(color=COLORS["pg_indigo"], bold=True),
        "pg.glow": Style(color=COLORS["pg_purple"], bold=True),
        "pg.neon": Style(color=COLORS["pg_pink"], bold=True),

        # Status styles
        "status.success": Style(color=COLORS["success"], bold=True),
        "status.warning": Style(color=COLORS["warning"], bold=True),
        "status.error": Style(color=COLORS["error"], bold=True),
        "status.info": Style(color=COLORS["info"]),
        "status.pending": Style(color=COLORS["text_muted"], italic=True),

        # UI element styles
        "panel.border": Style(color=COLORS["border_subtle"]),
        "panel.title": Style(color=COLORS["pg_cyan"], bold=True),
        "header": Style(color=COLORS["text_primary"], bold=True),
        "footer": Style(color=COLORS["text_secondary"]),

        # Table styles
        "table.header": Style(color=COLORS["pg_cyan"], bold=True),
        "table.row": Style(color=COLORS["text_primary"]),
        "table.row.alt": Style(color=COLORS["text_secondary"]),

        # Progress styles
        "progress.description": Style(color=COLORS["text_primary"]),
        "progress.percentage": Style(color=COLORS["pg_teal"], bold=True),
        "progress.elapsed": Style(color=COLORS["text_muted"]),
        "progress.remaining": Style(color=COLORS["text_secondary"]),

        # Input styles
        "input.label": Style(color=COLORS["pg_cyan"]),
        "input.prompt": Style(color=COLORS["pg_teal"]),
        "input.error": Style(color=COLORS["error"]),

        # Gradient styles for ASCII art
        "gradient.1": Style(color=COLORS["gradient_1"], bold=True),
        "gradient.2": Style(color=COLORS["gradient_2"], bold=True),
        "gradient.3": Style(color=COLORS["gradient_3"], bold=True),
        "gradient.4": Style(color=COLORS["gradient_4"], bold=True),
        "gradient.5": Style(color=COLORS["gradient_5"], bold=True),

        # Version badge styles (neon rainbow)
        "version.14": Style(color="#fb7185", bold=True),   # Neon Rose
        "version.15": Style(color="#fbbf24", bold=True),   # Neon Amber
        "version.16": Style(color="#a3e635", bold=True),   # Neon Lime
        "version.17": Style(color="#34d399", bold=True),   # Neon Emerald
        "version.18": Style(color="#22d3ee", bold=True),   # Neon Cyan (target)
    })


# ──────────────────────────────────────────────────────────
# Animated Unicode Box Characters for premium look
# ──────────────────────────────────────────────────────────
BOX_CHARS = {
    "h": "─", "v": "│",
    "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
    "hd": "═", "vd": "║",
    "tld": "╔", "trd": "╗", "bld": "╚", "brd": "╝",
    "dot": "·", "bullet": "●", "circle": "○",
    "arrow": "▸", "check": "✓", "cross": "✗",
    "diamond": "◆", "star": "★", "sparkle": "✦",
}

# ──────────────────────────────────────────────────────────
# Spinner character sets for animations
# ──────────────────────────────────────────────────────────
SPINNERS = {
    "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    "circle": ["◐", "◓", "◑", "◒"],
    "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
    "pulse": ["░", "▒", "▓", "█", "▓", "▒"],
    "wave": ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"],
    "bounce": ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"],
    "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
    "neon": ["◉", "◎", "○", "◎"],
}

# ──────────────────────────────────────────────────────────
# Progress bar character sets
# ──────────────────────────────────────────────────────────
PROGRESS_CHARS = {
    "fill": "━",
    "empty": "╌",
    "head": "●",
    "block_fill": "█",
    "block_half": "▓",
    "block_light": "░",
    "glow": "▸",
}

# ──────────────────────────────────────────────────────────
# ASCII Art Banners
# ──────────────────────────────────────────────────────────
BANNER_ART = """
[bold #22d3ee]██████╗  ██████╗ [/][bold #818cf8]   ███╗   ███╗██╗ ██████╗ ██████╗  █████╗ ████████╗ ██████╗ ██████╗[/]
[bold #22d3ee]██╔══██╗██╔════╝ [/][bold #a78bfa]   ████╗ ████║██║██╔════╝ ██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗[/]
[bold #2dd4bf]██████╔╝██║  ███╗[/][bold #c084fc]   ██╔████╔██║██║██║  ███╗██████╔╝███████║   ██║   ██║   ██║██████╔╝[/]
[bold #2dd4bf]██╔═══╝ ██║   ██║[/][bold #e879f9]   ██║╚██╔╝██║██║██║   ██║██╔══██╗██╔══██║   ██║   ██║   ██║██╔══██╗[/]
[bold #818cf8]██║     ╚██████╔╝[/][bold #f472b6]   ██║ ╚═╝ ██║██║╚██████╔╝██║  ██║██║  ██║   ██║   ╚██████╔╝██║  ██║[/]
[bold #818cf8]╚═╝      ╚═════╝ [/][bold #f472b6]   ╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝[/]
"""

# Compact banner for smaller terminals
BANNER_COMPACT = """
[bold #334155]╭───────────────────────────────────────────────────────────────╮[/]
[bold #334155]│[/] [bold #22d3ee]  PG MIGRATOR[/] [#64748b]·····················[/] [bold #a78bfa]PostgreSQL Migration Tool[/] [bold #334155]│[/]
[bold #334155]╰───────────────────────────────────────────────────────────────╯[/]
"""

# Version flow display with neon styling
VERSION_FLOW = """
[bold #334155]  ╭──────────────────────────────────────────────────────────╮[/]
[bold #334155]  │[/]   [bold #fb7185] 14 [/] [#64748b]━━▸[/] [bold #fbbf24] 15 [/] [#64748b]━━▸[/] [bold #a3e635] 16 [/] [#64748b]━━▸[/] [bold #34d399] 17 [/] [#64748b]━━▸[/] [bold #22d3ee] 18 [/]  [bold #334155]│[/]
[bold #334155]  │[/]  [#64748b]source                                          target[/]  [bold #334155]│[/]
[bold #334155]  ╰──────────────────────────────────────────────────────────╯[/]
"""

# Decorative separator
SEPARATOR_GLOW = "[#334155]  " + "─" * 62 + "[/]"
