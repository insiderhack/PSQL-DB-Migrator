"""
Rich Theme and Color Definitions for PostgreSQL Migrator.
A stunning, PostgreSQL-inspired color palette with gradient effects.
"""

from rich.theme import Theme
from rich.style import Style

# PostgreSQL-inspired color palette
COLORS = {
    # Primary PostgreSQL Blue Gradient
    "pg_blue_darkest": "#1a365d",
    "pg_blue_dark": "#2a4365",
    "pg_blue": "#336791",        # Official PostgreSQL Blue
    "pg_blue_light": "#4299e1",
    "pg_blue_lightest": "#90cdf4",
    
    # Secondary Accent Colors
    "pg_cyan": "#38b2ac",
    "pg_teal": "#319795",
    "pg_purple": "#805ad5",
    "pg_indigo": "#667eea",
    
    # Status Colors
    "success": "#48bb78",
    "success_light": "#9ae6b4",
    "warning": "#ed8936",
    "warning_light": "#fbd38d",
    "error": "#f56565",
    "error_light": "#feb2b2",
    "info": "#4299e1",
    
    # Neutral Colors
    "bg_dark": "#1a202c",
    "bg_medium": "#2d3748",
    "bg_light": "#4a5568",
    "text_primary": "#f7fafc",
    "text_secondary": "#a0aec0",
    "text_muted": "#718096",
    
    # Gradient Effect Colors (for ASCII art)
    "gradient_1": "#667eea",
    "gradient_2": "#764ba2",
    "gradient_3": "#f093fb",
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
        "pg.accent": Style(color=COLORS["pg_blue_light"]),
        "pg.highlight": Style(color=COLORS["pg_cyan"], bold=True),
        "pg.version": Style(color=COLORS["pg_indigo"], bold=True),
        
        # Status styles
        "status.success": Style(color=COLORS["success"], bold=True),
        "status.warning": Style(color=COLORS["warning"], bold=True),
        "status.error": Style(color=COLORS["error"], bold=True),
        "status.info": Style(color=COLORS["info"]),
        "status.pending": Style(color=COLORS["text_muted"], italic=True),
        
        # UI element styles
        "panel.border": Style(color=COLORS["pg_blue"]),
        "panel.title": Style(color=COLORS["pg_blue_light"], bold=True),
        "header": Style(color=COLORS["text_primary"], bold=True, bgcolor=COLORS["pg_blue_dark"]),
        "footer": Style(color=COLORS["text_secondary"]),
        
        # Table styles
        "table.header": Style(color=COLORS["pg_blue_light"], bold=True),
        "table.row": Style(color=COLORS["text_primary"]),
        "table.row.alt": Style(color=COLORS["text_secondary"]),
        
        # Progress styles
        "progress.description": Style(color=COLORS["text_primary"]),
        "progress.percentage": Style(color=COLORS["pg_cyan"], bold=True),
        "progress.elapsed": Style(color=COLORS["text_muted"]),
        "progress.remaining": Style(color=COLORS["text_secondary"]),
        
        # Input styles
        "input.label": Style(color=COLORS["pg_blue_light"]),
        "input.prompt": Style(color=COLORS["pg_cyan"]),
        "input.error": Style(color=COLORS["error"]),
        
        # Gradient styles for ASCII art
        "gradient.1": Style(color=COLORS["gradient_1"], bold=True),
        "gradient.2": Style(color=COLORS["gradient_2"], bold=True),
        "gradient.3": Style(color=COLORS["gradient_3"], bold=True),
        
        # Version badge styles
        "version.14": Style(color="#e53e3e", bold=True),  # Red
        "version.15": Style(color="#ed8936", bold=True),  # Orange
        "version.16": Style(color="#ecc94b", bold=True),  # Yellow
        "version.17": Style(color="#48bb78", bold=True),  # Green
        "version.18": Style(color="#4299e1", bold=True),  # Blue (target)
    })


# ASCII Art Banner with gradient coloring (using direct hex colors)
BANNER_ART = """
[bold #38b2ac]██████╗  ██████╗ [/][bold #667eea]   ███╗   ███╗██╗ ██████╗ ██████╗  █████╗ ████████╗ ██████╗ ██████╗[/]
[bold #38b2ac]██╔══██╗██╔════╝ [/][bold #667eea]   ████╗ ████║██║██╔════╝ ██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗[/]
[bold #38b2ac]██████╔╝██║  ███╗[/][bold #764ba2]   ██╔████╔██║██║██║  ███╗██████╔╝███████║   ██║   ██║   ██║██████╔╝[/]
[bold #38b2ac]██╔═══╝ ██║   ██║[/][bold #764ba2]   ██║╚██╔╝██║██║██║   ██║██╔══██╗██╔══██║   ██║   ██║   ██║██╔══██╗[/]
[bold #667eea]██║     ╚██████╔╝[/][bold #38b2ac]   ██║ ╚═╝ ██║██║╚██████╔╝██║  ██║██║  ██║   ██║   ╚██████╔╝██║  ██║[/]
[bold #667eea]╚═╝      ╚═════╝ [/][bold #38b2ac]   ╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝[/]
"""

# Compact banner for smaller terminals
BANNER_COMPACT = """
[bold #336791]╔═══════════════════════════════════════════════════════════════╗[/]
[bold #336791]║[/] [bold #4299e1]🐘 PG MIGRATOR[/] [dim]──────────────[/] [bold #38b2ac]PostgreSQL Migration Tool[/] [bold #336791]║[/]
[bold #336791]╚═══════════════════════════════════════════════════════════════╝[/]
"""

# Version flow display
VERSION_FLOW = """
[bold #e53e3e]  14  [/][dim]━━━▶[/][bold #ed8936]  15  [/][dim]━━━▶[/][bold #ecc94b]  16  [/][dim]━━━▶[/][bold #48bb78]  17  [/][dim]━━━▶[/][bold #4299e1]  18  [/]
[dim] old                                                    target[/]
"""

