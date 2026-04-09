"""
InsiderPSQL Universal Migrator – Premium GUI
A modern, neon-dark themed desktop application built with CustomTkinter.
Features glassmorphism cards, smooth animations, and a premium aesthetic.
"""

import math
import queue
import sys
import threading
import time
from tkinter import messagebox
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import customtkinter as ctk
import psycopg2
from PIL import Image, ImageDraw, ImageTk

from .logger import get_logger
from .migrator import MigrationContext, MigrationEngine, MigrationMethod

# ──────────────────────────────────────────────────────────
# Neon Dark Theme – matches CLI palette from theme.py
# ──────────────────────────────────────────────────────────
NEON = {
    # Backgrounds
    "bg_darkest": "#0a0e1a",
    "bg_dark": "#0f172a",
    "bg_medium": "#1e293b",
    "bg_card": "#162033",
    "bg_input": "#0f172a",
    "bg_sidebar": "#0c1222",

    # Borders
    "border": "#334155",
    "border_glow": "#22d3ee",

    # Primary accents
    "cyan": "#22d3ee",
    "teal": "#2dd4bf",
    "purple": "#a78bfa",
    "indigo": "#818cf8",
    "pink": "#f472b6",
    "lime": "#a3e635",

    # Status
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#fb7185",
    "info": "#60a5fa",

    # Text
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",

    # Version colors
    "v14": "#fb7185",
    "v15": "#fbbf24",
    "v16": "#a3e635",
    "v17": "#34d399",
    "v18": "#22d3ee",
}

# Override CustomTkinter defaults
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# ──────────────────────────────────────────────────────────
# Utility: Hex color math
# ──────────────────────────────────────────────────────────
def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"


def _lerp_color(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colors."""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


# ──────────────────────────────────────────────────────────
# Main Application
# ──────────────────────────────────────────────────────────
class MigratorApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("InsiderPSQL Universal Migrator v1")
        self.geometry("1050x700")
        self.minsize(960, 640)
        self.configure(fg_color=NEON["bg_dark"])

        self._set_app_icon()

        # ── Queues & logging ──
        self.log_queue: queue.Queue[Any] = queue.Queue()
        self.logger = get_logger()
        self.logger.add_gui_handler(self.log_queue)

        # ── Animation state ──
        self._pulse_phase: float = 0.0
        self._indicator_y: float = 0.0
        self._target_indicator_y: float = 0.0
        self._page_slide_offset: int = 60
        self._glow_phase: float = 0.0
        self._spinner_idx: Dict[str, int] = {"source": 0, "target": 0}
        self._spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._connection_status: Dict[str, Optional[str]] = {"source": None, "target": None}
        self._active_frame: Optional[ctk.CTkFrame] = None

        self.db_versions: Dict[str, Optional[int]] = {"source": None, "target": None}

        # ── Layout ──
        self.grid_rowconfigure(0, weight=0)  # accent bar
        self.grid_rowconfigure(1, weight=1)  # content
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # main

        # Top accent gradient bar
        self._create_accent_bar()

        # Sidebar
        self._create_sidebar()

        # Main content area
        self.main_container = ctk.CTkFrame(
            self, corner_radius=0, fg_color=NEON["bg_dark"]
        )
        self.main_container.grid(row=1, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Pages
        self.pages: Dict[str, ctk.CTkFrame] = {}
        self._create_connection_page()
        self._create_options_page()
        self._create_migration_page()

        # Kick off event loops
        self.after(100, self._poll_queue)
        self.after(40, self._tick_animations)

        # Default page
        self.select_page("Connections")

    # ================================================================
    # ACCENT BAR  – thin gradient strip at the very top
    # ================================================================
    def _create_accent_bar(self) -> None:
        """Create a 3px gradient accent bar spanning the full width."""
        bar = ctk.CTkFrame(self, height=3, corner_radius=0, fg_color=NEON["cyan"])
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")

    # ================================================================
    # APP ICON
    # ================================================================
    def _create_raw_logo(self) -> Image.Image:
        """Generate the base Pillow image for logos and icons."""
        size = 128
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        primary = NEON["cyan"]
        accent = NEON["indigo"]

        draw.ellipse([16, 72, 112, 112], fill=accent)
        draw.ellipse([16, 60, 112, 100], fill=primary, outline=NEON["bg_dark"], width=4)
        draw.ellipse([16, 44, 112, 84], fill=accent)
        draw.ellipse([16, 32, 112, 72], fill=primary, outline=NEON["bg_dark"], width=4)
        draw.ellipse([16, 16, 112, 56], fill=accent)
        draw.ellipse([16, 4, 112, 44], fill=primary, outline=NEON["bg_dark"], width=4)
        return img

    def _set_app_icon(self) -> None:
        raw_img = self._create_raw_logo()
        self._icon_photo = ImageTk.PhotoImage(raw_img)
        self.iconphoto(True, self._icon_photo)
        if sys.platform == "darwin":
            try:
                self.tk.call(
                    "::tk::mac::iconBitmap", str(self), 128, 128,
                    "-namedImage", str(self._icon_photo),
                )
            except Exception:
                pass

    def _generate_logo(self) -> ctk.CTkImage:
        img = self._create_raw_logo()
        return ctk.CTkImage(light_image=img, dark_image=img, size=(44, 44))

    # ================================================================
    # SIDEBAR
    # ================================================================
    def _create_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color=NEON["bg_sidebar"],
            border_width=0,
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(5, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Logo + title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=16, pady=(24, 8), sticky="ew")

        logo_img = self._generate_logo()
        ctk.CTkLabel(
            logo_frame, text="", image=logo_img, compound="left",
        ).pack(side="left", padx=(4, 10))

        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x")
        ctk.CTkLabel(
            title_frame, text="InsiderPSQL",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=NEON["text_primary"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame, text="Migrator v1",
            font=ctk.CTkFont(size=11),
            text_color=NEON["text_muted"],
        ).pack(anchor="w")

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=NEON["border"])
        sep.grid(row=1, column=0, sticky="ew", padx=20, pady=(12, 16))

        # Navigation
        self.nav_btns: Dict[str, ctk.CTkButton] = {}
        nav_icons = {"Connections": "  ⬡  ", "Options": "  ⚙  ", "Migration": "  ▶  "}
        nav_items = list(nav_icons.keys())

        for i, item in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar, corner_radius=8, height=42, border_spacing=10,
                text=f"{nav_icons[item]} {item}", fg_color="transparent",
                text_color=NEON["text_secondary"],
                hover_color=NEON["bg_medium"], anchor="w",
                font=ctk.CTkFont(size=14),
                command=lambda name=item: self.select_page(name),
            )
            btn.grid(row=i + 2, column=0, sticky="ew", padx=12, pady=2)
            self.nav_btns[item] = btn

        # Sliding indicator (left accent line)
        self.tab_indicator = ctk.CTkFrame(
            self.sidebar, width=3, height=36, corner_radius=2,
            fg_color=NEON["cyan"],
        )

        # Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.grid(row=6, column=0, padx=16, pady=(8, 16), sticky="sew")

        sep2 = ctk.CTkFrame(footer, height=1, fg_color=NEON["border"])
        sep2.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            footer, text="INSIDERTECH 2026",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=NEON["text_muted"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            footer, text="Muhammad Rizki Perdana Putra",
            font=ctk.CTkFont(size=9),
            text_color=NEON["border"],
        ).pack(anchor="w")

    # ================================================================
    # PAGE NAVIGATION  (with slide + indicator animations)
    # ================================================================
    def select_page(self, name: str) -> None:
        for btn_name, btn in self.nav_btns.items():
            if btn_name == name:
                btn.configure(
                    fg_color=NEON["bg_medium"],
                    text_color=NEON["cyan"],
                )
                btn.update_idletasks()
                self._target_indicator_y = float(btn.winfo_y() + 3)
                self._animate_indicator()
            else:
                btn.configure(fg_color="transparent", text_color=NEON["text_secondary"])

        for page_name, frame in self.pages.items():
            if page_name == name:
                self._page_slide_offset = 50
                frame.grid(row=0, column=0, sticky="nsew", padx=(self._page_slide_offset, 0))
                self._active_frame = frame
                self._animate_page_slide()
            else:
                frame.grid_forget()

    def _animate_indicator(self) -> None:
        diff = self._target_indicator_y - self._indicator_y
        if abs(diff) > 1:
            self._indicator_y += diff * 0.28
            self.tab_indicator.place(x=6, y=int(self._indicator_y))
            self.after(16, self._animate_indicator)
        else:
            self._indicator_y = self._target_indicator_y
            self.tab_indicator.place(x=6, y=int(self._indicator_y))

    def _animate_page_slide(self) -> None:
        if self._page_slide_offset > 1 and self._active_frame is not None:
            self._page_slide_offset = int(self._page_slide_offset * 0.55)
            self._active_frame.grid(padx=(self._page_slide_offset, 0))
            self.after(16, self._animate_page_slide)
        elif self._active_frame is not None:
            self._active_frame.grid(padx=0)

    # ================================================================
    # MASTER ANIMATION TICK  (drives pulse / glow / spinners)
    # ================================================================
    def _tick_animations(self) -> None:
        self._pulse_phase += 0.06
        self._glow_phase += 0.04

        # Button pulse (breathing neon glow)
        if hasattr(self, "btn_start") and self.btn_start.cget("state") == "normal":
            t = (math.sin(self._pulse_phase) + 1.0) / 2.0
            color = _lerp_color(NEON["cyan"], NEON["indigo"], t)
            self.btn_start.configure(fg_color=color)

        # Progress bar glow during migration
        if hasattr(self, "progress_bar"):
            try:
                val = self.progress_bar.get()
                if 0 < val < 1:
                    t = (math.sin(self._glow_phase * 2) + 1.0) / 2.0
                    bar_color = _lerp_color(NEON["cyan"], NEON["teal"], t)
                    self.progress_bar.configure(progress_color=bar_color)
            except Exception:
                pass

        self.after(40, self._tick_animations)

    # ================================================================
    # PAGE 1: CONNECTIONS
    # ================================================================
    def _create_connection_page(self) -> None:
        page = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        page.grid_columnconfigure((0, 1), weight=1)
        page.grid_rowconfigure(1, weight=1)
        self.pages["Connections"] = page

        # Section header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, padx=28, pady=(24, 4), sticky="ew")
        ctk.CTkLabel(
            header, text="Database Connections",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=NEON["text_primary"],
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="Configure source and target PostgreSQL instances",
            font=ctk.CTkFont(size=12),
            text_color=NEON["text_muted"],
        ).pack(side="left", padx=(16, 0))

        # Source card
        source_card = self._create_glass_card(page)
        source_card.grid(row=1, column=0, padx=(24, 10), pady=(8, 24), sticky="nsew")
        self._add_card_header(source_card, "Source Database", NEON["info"], "◀")
        self.source_entries = self._create_db_form(source_card, "source")

        btn_frame_src = ctk.CTkFrame(source_card, fg_color="transparent")
        btn_frame_src.pack(fill="x", padx=24, pady=(16, 4))

        self.btn_test_source = ctk.CTkButton(
            btn_frame_src, text="Test Connection", height=38, corner_radius=8,
            fg_color=NEON["bg_medium"], hover_color=NEON["border"],
            border_width=1, border_color=NEON["border"],
            text_color=NEON["text_primary"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.test_connection("source"),
        )
        self.btn_test_source.pack(fill="x")

        self.lbl_status_source = ctk.CTkLabel(
            source_card, text="", font=ctk.CTkFont(size=12),
            text_color=NEON["text_muted"],
        )
        self.lbl_status_source.pack(pady=(6, 16))

        # Target card
        target_card = self._create_glass_card(page)
        target_card.grid(row=1, column=1, padx=(10, 24), pady=(8, 24), sticky="nsew")
        self._add_card_header(target_card, "Target Database", NEON["cyan"], "▶")
        self.target_entries = self._create_db_form(target_card, "target")

        btn_frame_tgt = ctk.CTkFrame(target_card, fg_color="transparent")
        btn_frame_tgt.pack(fill="x", padx=24, pady=(16, 4))

        self.btn_test_target = ctk.CTkButton(
            btn_frame_tgt, text="Test Connection", height=38, corner_radius=8,
            fg_color=NEON["bg_medium"], hover_color=NEON["border"],
            border_width=1, border_color=NEON["border"],
            text_color=NEON["text_primary"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.test_connection("target"),
        )
        self.btn_test_target.pack(fill="x")

        self.lbl_status_target = ctk.CTkLabel(
            target_card, text="", font=ctk.CTkFont(size=12),
            text_color=NEON["text_muted"],
        )
        self.lbl_status_target.pack(pady=(6, 16))

    def _create_glass_card(self, parent: ctk.CTkBaseClass) -> ctk.CTkFrame:
        """Create a glassmorphism-style card with subtle border glow."""
        return ctk.CTkFrame(
            parent, corner_radius=14,
            fg_color=NEON["bg_card"],
            border_width=1,
            border_color=NEON["border"],
        )

    def _add_card_header(
        self, card: ctk.CTkFrame, title: str, accent: str, icon: str
    ) -> None:
        """Add a styled header strip to a card."""
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(
            hdr, text=f"  {icon}  {title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=accent,
        ).pack(side="left")

        # Accent dot
        ctk.CTkLabel(
            hdr, text="●", font=ctk.CTkFont(size=8),
            text_color=accent,
        ).pack(side="right", padx=(0, 4))

    def _create_db_form(
        self, parent: ctk.CTkFrame, prefix: str
    ) -> Dict[str, ctk.CTkEntry]:
        entries: Dict[str, ctk.CTkEntry] = {}
        fields = [
            ("Host", "localhost"),
            ("Port", "5432" if prefix == "source" else "5433"),
            ("Database", "postgres"),
            ("User", "postgres"),
            ("Password", ""),
        ]

        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=24)
        form.grid_columnconfigure(1, weight=1)

        for i, (label, default) in enumerate(fields):
            ctk.CTkLabel(
                form, text=f"{label}:", anchor="e",
                font=ctk.CTkFont(size=12),
                text_color=NEON["text_secondary"],
            ).grid(row=i, column=0, pady=5, sticky="e", padx=(0, 12))

            entry = ctk.CTkEntry(
                form, height=32, corner_radius=6,
                fg_color=NEON["bg_input"],
                border_color=NEON["border"],
                border_width=1,
                text_color=NEON["text_primary"],
                placeholder_text_color=NEON["text_muted"],
                font=ctk.CTkFont(size=12),
                show="●" if label == "Password" else "",
            )
            entry.insert(0, default)
            entry.grid(row=i, column=1, pady=5, sticky="ew")
            entries[label.lower()] = entry

        return entries

    def _build_dsn(self, prefix: str) -> Optional[str]:
        entries = self.source_entries if prefix == "source" else self.target_entries
        host = entries["host"].get()
        port = entries["port"].get()
        db = entries["database"].get()
        user = entries["user"].get()
        password = entries["password"].get()
        if not all([host, port, db, user, password]):
            return None
        # URL-encode user and password so special chars (@, :, /, #, %) don't break the URI
        return f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{db}"

    # ── Connection testing ──
    def test_connection(self, prefix: str) -> None:
        dsn = self._build_dsn(prefix)
        btn = self.btn_test_source if prefix == "source" else self.btn_test_target
        lbl = self.lbl_status_source if prefix == "source" else self.lbl_status_target

        if not dsn:
            lbl.configure(text="  ▲  Please fill all fields", text_color=NEON["warning"])
            return

        btn.configure(state="disabled", fg_color=NEON["bg_dark"], text_color=NEON["text_muted"])
        lbl.configure(text="  ◉  Connecting...", text_color=NEON["cyan"])
        self._spinner_idx[prefix] = 0
        self._animate_spinner(prefix)

        def worker() -> None:
            try:
                from .detector import detect_version_from_dsn
                version_info = detect_version_from_dsn(dsn)
                if version_info:
                    msg = f"Connected  ·  PostgreSQL {version_info.major}.{version_info.minor}"
                    self.log_queue.put(("test_result", prefix, True, msg, version_info.major))
                else:
                    conn = psycopg2.connect(dsn, connect_timeout=5)
                    conn.close()
                    self.log_queue.put(("test_result", prefix, True, "Connected  ·  Version unknown", None))
            except Exception as e:
                err_msg = str(e).split("\n")[0]
                self.log_queue.put(("test_result", prefix, False, f"Failed: {err_msg}", None))

        threading.Thread(target=worker, daemon=True).start()

    def _animate_spinner(self, prefix: str) -> None:
        btn = self.btn_test_source if prefix == "source" else self.btn_test_target
        if btn.cget("state") == "disabled":
            idx = self._spinner_idx[prefix]
            char = self._spinner_chars[idx % len(self._spinner_chars)]
            btn.configure(text=f"{char}  Testing...")
            self._spinner_idx[prefix] += 1
            self.after(100, lambda: self._animate_spinner(prefix))

    # ================================================================
    # PAGE 2: OPTIONS
    # ================================================================
    def _create_options_page(self) -> None:
        page = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        self.pages["Options"] = page

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, padx=28, pady=(24, 4), sticky="ew")
        ctk.CTkLabel(
            header, text="Migration Settings",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=NEON["text_primary"],
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="Configure how the migration will be performed",
            font=ctk.CTkFont(size=12),
            text_color=NEON["text_muted"],
        ).pack(side="left", padx=(16, 0))

        # Settings card
        card = self._create_glass_card(page)
        card.grid(row=1, column=0, padx=24, pady=(8, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=30)
        inner.grid_columnconfigure(1, weight=1)

        # ── Method ──
        ctk.CTkLabel(
            inner, text="Migration Method",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=NEON["cyan"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        ctk.CTkLabel(
            inner, text="Strategy used to transfer data between instances",
            font=ctk.CTkFont(size=11),
            text_color=NEON["text_muted"],
        ).grid(row=1, column=0, sticky="w", pady=(0, 12))

        self.method_var = ctk.StringVar(value="dump_restore")
        self.method_menu = ctk.CTkOptionMenu(
            inner, values=["dump_restore", "pg_upgrade", "python"],
            variable=self.method_var, width=240, height=36,
            corner_radius=8,
            fg_color=NEON["bg_input"],
            button_color=NEON["border"],
            button_hover_color=NEON["bg_medium"],
            dropdown_fg_color=NEON["bg_card"],
            dropdown_hover_color=NEON["bg_medium"],
            text_color=NEON["text_primary"],
            font=ctk.CTkFont(size=13),
        )
        self.method_menu.grid(row=0, column=1, rowspan=2, sticky="e", padx=(20, 0))

        # Divider
        ctk.CTkFrame(inner, height=1, fg_color=NEON["border"]).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=20,
        )

        # ── Dry run ──
        ctk.CTkLabel(
            inner, text="Dry Run Mode",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=NEON["cyan"],
        ).grid(row=3, column=0, sticky="w", pady=(0, 4))
        ctk.CTkLabel(
            inner, text="Perform analysis and checks without modifying data",
            font=ctk.CTkFont(size=11),
            text_color=NEON["text_muted"],
        ).grid(row=4, column=0, sticky="w", pady=(0, 4))

        self.dry_run_var = ctk.BooleanVar(value=False)
        self.dry_run_switch = ctk.CTkSwitch(
            inner, text="", variable=self.dry_run_var,
            onvalue=True, offvalue=False,
            progress_color=NEON["cyan"],
            button_color=NEON["text_secondary"],
            button_hover_color=NEON["text_primary"],
            fg_color=NEON["border"],
        )
        self.dry_run_switch.grid(row=3, column=1, rowspan=2, sticky="e", padx=(20, 0))

        # Divider
        ctk.CTkFrame(inner, height=1, fg_color=NEON["border"]).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=20,
        )

        # ── Info cards ──
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
        info_frame.grid_columnconfigure((0, 1, 2), weight=1)

        method_info = [
            ("dump_restore", "Most reliable. Uses pg_dump/pg_restore.", NEON["info"]),
            ("pg_upgrade", "Fast in-place upgrade between versions.", NEON["teal"]),
            ("python", "Pure Python row-level copy. Flexible.", NEON["purple"]),
        ]
        for i, (name, desc, color) in enumerate(method_info):
            info_card = ctk.CTkFrame(
                info_frame, corner_radius=10, fg_color=NEON["bg_dark"],
                border_width=1, border_color=NEON["border"],
            )
            info_card.grid(row=0, column=i, padx=(0 if i == 0 else 6, 0), sticky="nsew")
            ctk.CTkLabel(
                info_card, text=name, font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color,
            ).pack(padx=12, pady=(10, 4), anchor="w")
            ctk.CTkLabel(
                info_card, text=desc, font=ctk.CTkFont(size=10),
                text_color=NEON["text_muted"], wraplength=200, justify="left",
            ).pack(padx=12, pady=(0, 10), anchor="w")

    # ================================================================
    # PAGE 3: MIGRATION & LOGS
    # ================================================================
    def _create_migration_page(self) -> None:
        page = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        self.pages["Migration"] = page

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, padx=28, pady=(24, 12), sticky="ew")
        ctk.CTkLabel(
            header, text="Migration",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=NEON["text_primary"],
        ).pack(side="left")

        self.btn_start = ctk.CTkButton(
            header, text="  ▶  START MIGRATION",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, corner_radius=10,
            fg_color=NEON["cyan"],
            hover_color=NEON["teal"],
            text_color=NEON["bg_dark"],
            command=self.start_migration,
        )
        self.btn_start.pack(side="right")

        # Progress area
        progress_card = ctk.CTkFrame(
            page, corner_radius=10, fg_color=NEON["bg_card"],
            border_width=1, border_color=NEON["border"],
        )
        progress_card.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")

        progress_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        progress_inner.pack(fill="x", padx=20, pady=14)

        self.lbl_progress_status = ctk.CTkLabel(
            progress_inner, text="Ready",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=NEON["text_secondary"],
        )
        self.lbl_progress_status.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(
            progress_inner, height=8, corner_radius=4,
            fg_color=NEON["bg_dark"],
            progress_color=NEON["cyan"],
            border_width=0,
        )
        self.progress_bar.pack(fill="x", pady=(8, 4))
        self.progress_bar.set(0)

        self.lbl_progress_pct = ctk.CTkLabel(
            progress_inner, text="0%",
            font=ctk.CTkFont(size=11),
            text_color=NEON["text_muted"],
        )
        self.lbl_progress_pct.pack(anchor="e")

        # Log terminal
        log_card = ctk.CTkFrame(
            page, corner_radius=10, fg_color=NEON["bg_card"],
            border_width=1, border_color=NEON["border"],
        )
        log_card.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="nsew")
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        # Terminal header bar
        term_header = ctk.CTkFrame(log_card, height=32, fg_color=NEON["bg_medium"], corner_radius=0)
        term_header.grid(row=0, column=0, sticky="ew")
        term_header.grid_propagate(False)

        # Traffic light dots
        dot_frame = ctk.CTkFrame(term_header, fg_color="transparent")
        dot_frame.pack(side="left", padx=12)
        for color in [NEON["error"], NEON["warning"], NEON["success"]]:
            ctk.CTkLabel(
                dot_frame, text="●", font=ctk.CTkFont(size=9),
                text_color=color,
            ).pack(side="left", padx=2)

        ctk.CTkLabel(
            term_header, text="Migration Log",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=NEON["text_muted"],
        ).pack(side="left", padx=(12, 0))

        self.log_textbox = ctk.CTkTextbox(
            log_card, state="disabled",
            font=ctk.CTkFont(family="Menlo, Consolas, monospace", size=12),
            fg_color=NEON["bg_darkest"],
            text_color=NEON["text_secondary"],
            corner_radius=0,
            border_width=0,
        )
        self.log_textbox.grid(row=1, column=0, padx=2, pady=(0, 2), sticky="nsew")

    # ================================================================
    # LOG HELPERS
    # ================================================================
    def _append_log(self, text: str, level: str = "INFO") -> None:
        """Append a line to the log terminal with level-based coloring."""
        self.log_textbox.configure(state="normal")

        # Timestamp prefix
        ts = time.strftime("%H:%M:%S")
        prefix = f"[{ts}] "

        # Tag for color-coding (CustomTkinter textbox supports tags)
        tag = level.lower()

        # Configure tags if not done yet
        color_map = {
            "info": NEON["text_secondary"],
            "warning": NEON["warning"],
            "error": NEON["error"],
            "success": NEON["success"],
            "progress": NEON["cyan"],
        }
        tag_color = color_map.get(tag, NEON["text_secondary"])

        try:
            self.log_textbox._textbox.tag_configure(tag, foreground=tag_color)
        except Exception:
            pass

        self.log_textbox.insert("end", f"{prefix}{text}\n", tag)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    # ================================================================
    # QUEUE POLLING
    # ================================================================
    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "log":
                    _, level, text = msg
                    self._append_log(text, level)

                elif msg_type == "progress":
                    _, pct, text = msg
                    self.progress_bar.set(pct / 100.0)
                    self.lbl_progress_pct.configure(text=f"{pct:.1f}%")
                    self.lbl_progress_status.configure(
                        text=text, text_color=NEON["cyan"],
                    )
                    self._append_log(f"[{pct:.1f}%] {text}", "progress")

                elif msg_type == "done":
                    _, success = msg
                    self.btn_start.configure(
                        state="normal",
                        fg_color=NEON["cyan"],
                        text_color=NEON["bg_dark"],
                        text="  ▶  START MIGRATION",
                    )
                    if success:
                        self.progress_bar.configure(progress_color=NEON["success"])
                        self.progress_bar.set(1.0)
                        self.lbl_progress_pct.configure(text="100%")
                        self.lbl_progress_status.configure(
                            text="Migration completed successfully",
                            text_color=NEON["success"],
                        )
                        self._append_log("Migration completed successfully!", "success")
                        messagebox.showinfo("Migration Finished", "Migration has successfully completed.")
                    else:
                        self.progress_bar.configure(progress_color=NEON["error"])
                        self.lbl_progress_status.configure(
                            text="Migration failed",
                            text_color=NEON["error"],
                        )
                        self._append_log("Migration failed.", "error")
                        messagebox.showinfo("Migration Finished", "Migration has failed.")

                elif msg_type == "test_result":
                    _, prefix, success, message, major_version = msg
                    btn = self.btn_test_source if prefix == "source" else self.btn_test_target
                    lbl = self.lbl_status_source if prefix == "source" else self.lbl_status_target

                    btn.configure(state="normal", text="Test Connection")
                    if success:
                        btn.configure(
                            fg_color=NEON["success"],
                            text_color=NEON["bg_dark"],
                            hover_color=NEON["success"],
                        )
                        lbl.configure(
                            text=f"  ✓  {message}",
                            text_color=NEON["success"],
                        )
                        self.db_versions[prefix] = major_version
                        self._connection_status[prefix] = "success"
                    else:
                        btn.configure(
                            fg_color=NEON["error"],
                            text_color=NEON["bg_dark"],
                            hover_color=NEON["error"],
                        )
                        lbl.configure(
                            text=f"  ✗  {message}",
                            text_color=NEON["error"],
                        )
                        self.db_versions[prefix] = None
                        self._connection_status[prefix] = "error"

        except queue.Empty:
            pass
        finally:
            self.after(80, self._poll_queue)

    # ================================================================
    # MIGRATION EXECUTION
    # ================================================================
    def start_migration(self) -> None:
        source_dsn = self._build_dsn("source")
        target_dsn = self._build_dsn("target")

        if not source_dsn or not target_dsn:
            messagebox.showerror(
                "Error",
                "Please fill in all database connection fields on the Connections page.",
            )
            self.select_page("Connections")
            return

        # Version validation
        src_ver = self.db_versions.get("source")
        tgt_ver = self.db_versions.get("target")

        if src_ver is None or tgt_ver is None:
            try:
                from .detector import detect_version_from_dsn
                src_info = detect_version_from_dsn(source_dsn)
                tgt_info = detect_version_from_dsn(target_dsn)
                if not src_info or not tgt_info:
                    messagebox.showerror(
                        "Validation Error",
                        "Could not connect to databases to verify PostgreSQL versions.",
                    )
                    self.select_page("Connections")
                    return
                src_ver = src_info.major
                tgt_ver = tgt_info.major
                self.db_versions["source"] = src_ver
                self.db_versions["target"] = tgt_ver
            except Exception as e:
                messagebox.showerror(
                    "Validation Error",
                    f"Failed to verify PG versions: {e}",
                )
                self.select_page("Connections")
                return

        if src_ver > tgt_ver:
            messagebox.showerror(
                "Migration Blocked",
                f"Cannot migrate from PG {src_ver} to PG {tgt_ver} (higher to lower).",
            )
            self.select_page("Connections")
            return

        method = self.method_var.get()
        dry_run = self.dry_run_var.get()

        context = MigrationContext(
            source_dsn=source_dsn,
            target_dsn=target_dsn,
            method=MigrationMethod(method),
            dry_run=dry_run,
        )

        def progress_callback(text: str, pct: float) -> None:
            self.log_queue.put(("progress", pct, text))

        engine = MigrationEngine(context, progress_callback=progress_callback)

        # Reset UI
        self.btn_start.configure(
            state="disabled",
            fg_color=NEON["bg_medium"],
            text_color=NEON["text_muted"],
            text="  ◉  MIGRATING...",
        )
        self.progress_bar.configure(progress_color=NEON["cyan"])
        self.progress_bar.set(0)
        self.lbl_progress_pct.configure(text="0%")
        self.lbl_progress_status.configure(
            text="Starting migration...", text_color=NEON["cyan"],
        )
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self._append_log("Starting migration process...", "info")

        def run_worker() -> None:
            try:
                success = engine.run()
                self.log_queue.put(("done", success))
            except Exception as e:
                self.log_queue.put(("log", "ERROR", f"Unhandled exception: {e}"))
                self.log_queue.put(("done", False))

        threading.Thread(target=run_worker, daemon=True).start()


if __name__ == "__main__":
    app = MigratorApp()
    app.mainloop()
