"""
UI Package – Rich-based Terminal User Interface
Provides themed components, animations, and screen layouts.
"""

from .components import (
    LiveMigrationTracker,
    create_animated_banner,
    create_compact_header,
    create_compatibility_table,
    create_database_table,
    create_divider,
    create_glass_panel,
    create_header,
    create_input_prompt,
    create_loading_animation,
    create_menu,
    create_panel,
    create_progress_animation,
    create_progress_bar,
    create_status_indicator,
    create_step_indicator,
    create_success_animation,
    create_summary_panel,
    create_wave_animation,
)
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

__all__ = [
    # Theme
    "get_theme",
    "COLORS",
    "BOX_CHARS",
    "SPINNERS",
    "PROGRESS_CHARS",
    "BANNER_ART",
    "BANNER_COMPACT",
    "VERSION_FLOW",
    "SEPARATOR_GLOW",
    # Components
    "create_header",
    "create_compact_header",
    "create_panel",
    "create_glass_panel",
    "create_progress_bar",
    "create_status_indicator",
    "create_database_table",
    "create_compatibility_table",
    "create_step_indicator",
    "create_summary_panel",
    "create_input_prompt",
    "create_menu",
    "create_divider",
    "LiveMigrationTracker",
    # Animations
    "create_animated_banner",
    "create_loading_animation",
    "create_success_animation",
    "create_wave_animation",
    "create_progress_animation",
]
