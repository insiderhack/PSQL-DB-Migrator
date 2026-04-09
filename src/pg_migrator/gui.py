import customtkinter as ctk
import queue
import threading
import psycopg2
import sys
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk

from .migrator import MigrationEngine, MigrationContext
from .logger import get_logger

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MigratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Rename Application
        self.title("InsiderPSQL Universal Migrator v1")
        self.geometry("950x650")
        self.minsize(900, 600)

        # Set Custom App Icon
        self._set_app_icon()

        # UI Queues & Logs
        self.log_queue = queue.Queue()
        self.logger = get_logger()
        self.logger.add_gui_handler(self.log_queue)

        # Animation states
        self.pulse_state = 0
        self.pulse_direction = 1
        self.spinners = {"source": 0, "target": 0}
        self.spinner_chars = ["|", "/", "-", "\\"]

        # Slide animation states
        self.active_tab_y = 0
        self.indicator_y = 0
        self.page_slide_x = 50

        self.db_versions = {"source": None, "target": None}

        # Layout styling
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create main layout containers
        self._create_sidebar()

        # Container for main content (pages)
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Create Pages
        self.pages = {}
        self._create_connection_page()
        self._create_options_page()
        self._create_migration_page()

        # Start loops
        self.after(100, self._poll_queue)
        self.after(100, self._animate_pulse)

        # Default open page
        self.select_page("Connections")

    def _create_raw_logo(self):
        """Generates the base Pillow image used for logos and icons."""
        size = 128 # High-res for dock icon
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        primary = "#38b2ac"
        accent = "#667eea"

        # Scale coordinates to match size 128
        draw.ellipse([16, 72, 112, 112], fill=accent)
        draw.ellipse([16, 60, 112, 100], fill=primary, outline="#1a202c", width=4)

        draw.ellipse([16, 44, 112, 84], fill=accent)
        draw.ellipse([16, 32, 112, 72], fill=primary, outline="#1a202c", width=4)

        draw.ellipse([16, 16, 112, 56], fill=accent)
        draw.ellipse([16, 4, 112, 44], fill=primary, outline="#1a202c", width=4)

        return img

    def _set_app_icon(self):
        """Sets the window and OS Dock icon dynamically."""
        raw_img = self._create_raw_logo()
        # Must keep a reference to PhotoImage to prevent garbage collection
        self._icon_photo = ImageTk.PhotoImage(raw_img)

        # 1. Standard cross-platform window icon
        self.iconphoto(True, self._icon_photo)

        # 2. Specific trick for macOS Dock Icon
        if sys.platform == "darwin":
            try:
                # Use internal Tk Tcl command to set the dock icon specifically
                self.tk.call('::tk::mac::iconBitmap', str(self), 128, 128, '-namedImage', str(self._icon_photo))
            except Exception as e:
                self.logger.warning(f"Could not set macOS dock icon: {e}")

    def _generate_logo(self):
        """Generates the CTkImage for the sidebar."""
        img = self._create_raw_logo()
        return ctk.CTkImage(light_image=img, dark_image=img, size=(48, 48))

    def _create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        # Logo/Title
        logo_img = self._generate_logo()
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=" InsiderPSQL\n Migrator v1",
                                       image=logo_img, compound="left",
                                       font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Sliding Indicator Line
        self.tab_indicator = ctk.CTkFrame(self.sidebar_frame, width=4, height=40, corner_radius=0, fg_color="#38b2ac")

        # Navigation Buttons
        self.nav_btns = {}
        nav_items = ["Connections", "Options", "Migration"]
        for i, item in enumerate(nav_items):
            btn = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10,
                                text=item, fg_color="transparent", text_color=("gray10", "gray90"),
                                hover_color=("gray70", "gray30"), anchor="w",
                                command=lambda name=item: self.select_page(name))
            btn.grid(row=i+1, column=0, sticky="ew")
            self.nav_btns[item] = btn

        # Branding Footer
        self.footer_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="INSIDERTECH 2026\nMuhammad Rizki Perdana Putra",
            font=ctk.CTkFont(size=10), text_color="gray50"
        )
        self.footer_label.grid(row=5, column=0, pady=(10, 20), sticky="s")

    def select_page(self, name):
        # Update button colors & trigger animations
        for btn_name, btn in self.nav_btns.items():
            if btn_name == name:
                btn.configure(fg_color=("gray75", "gray25"))

                # Setup indicator animation target
                btn.update_idletasks() # Ensure widget coordinates are calculated
                self.active_tab_y = btn.winfo_y()
                self._animate_indicator()
            else:
                btn.configure(fg_color="transparent")

        # Bring frame to front with slide-in transition
        for page_name, frame in self.pages.items():
            if page_name == name:
                # Start slide animation
                self.page_slide_x = 50
                frame.grid(row=0, column=0, sticky="nsew", padx=(self.page_slide_x, 0))
                self.active_frame = frame
                self._animate_page_slide()
            else:
                frame.grid_forget()

    def _animate_indicator(self):
        """Smoothly slide the left blue indicator line to the active tab."""
        diff = self.active_tab_y - self.indicator_y

        if abs(diff) > 1:
            self.indicator_y += diff * 0.3 # Ease-out interpolation
            self.tab_indicator.place(x=0, y=self.indicator_y)
            self.after(20, self._animate_indicator)
        else:
            self.indicator_y = self.active_tab_y
            self.tab_indicator.place(x=0, y=self.indicator_y)

    def _animate_page_slide(self):
        """Smoothly slide the page content in from the right."""
        if self.page_slide_x > 0:
            self.page_slide_x = int(self.page_slide_x * 0.6) # Fast ease-out
            self.active_frame.grid(padx=(self.page_slide_x, 0))
            self.after(16, self._animate_page_slide)
        else:
            self.active_frame.grid(padx=0)

    # ==========================================
    # PAGE 1: CONNECTIONS
    # ==========================================
    def _create_connection_page(self):
        page = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        page.grid_columnconfigure((0, 1), weight=1)
        page.grid_rowconfigure(0, weight=1)
        self.pages["Connections"] = page

        # Source Card
        source_card = ctk.CTkFrame(page, corner_radius=15)
        source_card.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        ctk.CTkLabel(source_card, text="Source Database", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))

        self.source_entries = self._create_db_form(source_card, "source")

        self.btn_test_source = ctk.CTkButton(source_card, text="Test Connection",
                                            command=lambda: self.test_connection("source"))
        self.btn_test_source.pack(pady=20)
        self.lbl_status_source = ctk.CTkLabel(source_card, text="")
        self.lbl_status_source.pack()

        # Target Card
        target_card = ctk.CTkFrame(page, corner_radius=15)
        target_card.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        ctk.CTkLabel(target_card, text="Target Database", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))

        self.target_entries = self._create_db_form(target_card, "target")

        self.btn_test_target = ctk.CTkButton(target_card, text="Test Connection",
                                            command=lambda: self.test_connection("target"))
        self.btn_test_target.pack(pady=20)
        self.lbl_status_target = ctk.CTkLabel(target_card, text="")
        self.lbl_status_target.pack()

    def _create_db_form(self, parent, prefix):
        entries = {}
        fields = [("Host", "localhost"), ("Port", "5432" if prefix=="source" else "5433"),
                  ("Database", "postgres"), ("User", "postgres"), ("Password", "")]

        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.pack(fill="x", padx=20)
        form_frame.grid_columnconfigure(1, weight=1)

        for i, (label, default) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=label+":").grid(row=i, column=0, pady=8, sticky="e", padx=(0, 10))
            show_char = "*" if label == "Password" else ""
            entry = ctk.CTkEntry(form_frame, show=show_char)
            entry.insert(0, default)
            entry.grid(row=i, column=1, pady=8, sticky="ew")
            entries[label.lower()] = entry

        return entries

    def _build_dsn(self, prefix):
        entries = self.source_entries if prefix == "source" else self.target_entries
        host = entries["host"].get()
        port = entries["port"].get()
        db = entries["database"].get()
        user = entries["user"].get()
        password = entries["password"].get()

        if not all([host, port, db, user, password]):
            return None
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    # --- Connection Testing Logic & Animations ---
    def test_connection(self, prefix):
        dsn = self._build_dsn(prefix)
        btn = self.btn_test_source if prefix == "source" else self.btn_test_target
        status_lbl = self.lbl_status_source if prefix == "source" else self.lbl_status_target

        if not dsn:
            status_lbl.configure(text="Please fill all fields", text_color="orange")
            return

        # Start animation
        btn.configure(state="disabled", fg_color="gray")
        status_lbl.configure(text="Connecting...", text_color="white")
        self.spinners[prefix] = 0
        self._animate_spinner(prefix)

        # Run test in background
        def worker():
            try:
                from .detector import detect_version_from_dsn
                version_info = detect_version_from_dsn(dsn)

                if version_info:
                    msg = f"Connection Successful (PG {version_info.major}.{version_info.minor})"
                    self.log_queue.put(("test_result", prefix, True, msg, version_info.major))
                else:
                    # Fallback to pure connection test if version parsing failed
                    conn = psycopg2.connect(dsn, connect_timeout=5)
                    conn.close()
                    self.log_queue.put(("test_result", prefix, True, "Connection Successful (Unknown PG Version)", None))
            except Exception as e:
                err_msg = str(e).split('\n')[0]
                self.log_queue.put(("test_result", prefix, False, f"Failed: {err_msg}", None))

        threading.Thread(target=worker, daemon=True).start()

    def _animate_spinner(self, prefix):
        btn = self.btn_test_source if prefix == "source" else self.btn_test_target
        # Check if we are still disabled (testing is ongoing)
        if btn.cget("state") == "disabled":
            idx = self.spinners[prefix]
            char = self.spinner_chars[idx % len(self.spinner_chars)]
            btn.configure(text=f"Testing {char}")
            self.spinners[prefix] += 1
            self.after(150, lambda: self._animate_spinner(prefix))

    # ==========================================
    # PAGE 2: OPTIONS
    # ==========================================
    def _create_options_page(self):
        page = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        self.pages["Options"] = page

        card = ctk.CTkFrame(page, corner_radius=15)
        card.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Migration Settings", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)

        # Method Dropdown
        method_frame = ctk.CTkFrame(card, fg_color="transparent")
        method_frame.pack(pady=20, fill="x", padx=50)
        ctk.CTkLabel(method_frame, text="Migration Method: ", font=ctk.CTkFont(size=16)).pack(side="left")
        self.method_var = ctk.StringVar(value="dump_restore")
        self.method_menu = ctk.CTkOptionMenu(method_frame, values=["dump_restore", "pg_upgrade", "python"], variable=self.method_var, width=200)
        self.method_menu.pack(side="right")

        # Dry Run Checkbox
        self.dry_run_var = ctk.BooleanVar(value=False)
        self.dry_run_checkbox = ctk.CTkCheckBox(card, text="Dry Run (Perform checks only, do not migrate data)", variable=self.dry_run_var, font=ctk.CTkFont(size=16))
        self.dry_run_checkbox.pack(pady=30)


    # ==========================================
    # PAGE 3: MIGRATION & LOGS
    # ==========================================
    def _create_migration_page(self):
        page = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        self.pages["Migration"] = page

        # Top Control Area
        control_frame = ctk.CTkFrame(page, fg_color="transparent")
        control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.btn_start = ctk.CTkButton(control_frame, text="🚀 START MIGRATION", font=ctk.CTkFont(size=16, weight="bold"), height=50, command=self.start_migration)
        self.btn_start.pack(side="right")
        self.base_color = self.btn_start.cget("fg_color") # Store for pulsing

        self.progress_bar = ctk.CTkProgressBar(control_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 20))
        self.progress_bar.set(0)

        # Terminal/Logs Area
        log_frame = ctk.CTkFrame(page)
        log_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", font=ctk.CTkFont(family="monospace", size=13))
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _animate_pulse(self):
        # Only pulse the start button if it's not disabled
        if self.btn_start.cget("state") == "normal":
            # Simple color interpolation for a breathing effect
            # Assuming default blue theme base color is around #3B8ED0 (RGB: 59, 142, 208)
            # We will shift slightly brighter and darker
            r = 59 + int(15 * self.pulse_state)
            g = 142 + int(15 * self.pulse_state)
            b = 208 + int(15 * self.pulse_state)

            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            self.btn_start.configure(fg_color=hex_color)

            self.pulse_state += 0.05 * self.pulse_direction
            if self.pulse_state >= 1.0 or self.pulse_state <= 0.0:
                self.pulse_direction *= -1

        self.after(50, self._animate_pulse)

    # --- Core Execution Logic ---
    def _append_log(self, text, level="INFO"):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{text}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _poll_queue(self):
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
                    self._append_log(f"[Progress {pct:.1f}%] {text}")

                elif msg_type == "done":
                    _, success = msg
                    self.btn_start.configure(state="normal", fg_color=self.base_color, text="🚀 START MIGRATION")
                    status = "successfully completed" if success else "failed"
                    messagebox.showinfo("Migration Finished", f"Migration has {status}.")

                elif msg_type == "test_result":
                    _, prefix, success, message, major_version = msg
                    btn = self.btn_test_source if prefix == "source" else self.btn_test_target
                    status_lbl = self.lbl_status_source if prefix == "source" else self.lbl_status_target

                    btn.configure(state="normal", text="Test Connection")
                    if success:
                        btn.configure(fg_color="green")
                        status_lbl.configure(text=message, text_color="green")
                        self.db_versions[prefix] = major_version
                    else:
                        btn.configure(fg_color="red")
                        status_lbl.configure(text=message, text_color="red")
                        self.db_versions[prefix] = None

        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)

    def start_migration(self):
        source_dsn = self._build_dsn("source")
        target_dsn = self._build_dsn("target")

        if not source_dsn or not target_dsn:
            messagebox.showerror("Error", "Please fill in all database connection fields on the Connections page.")
            self.select_page("Connections")
            return

        # Pre-Migration Version Validation
        src_ver = self.db_versions.get("source")
        tgt_ver = self.db_versions.get("target")

        # Fallback to fetch version if they didn't click "Test Connection"
        if src_ver is None or tgt_ver is None:
            try:
                from .detector import detect_version_from_dsn
                src_info = detect_version_from_dsn(source_dsn)
                tgt_info = detect_version_from_dsn(target_dsn)

                if not src_info or not tgt_info:
                    messagebox.showerror("Validation Error", "Could not connect to databases to verify PostgreSQL versions.")
                    self.select_page("Connections")
                    return

                src_ver = src_info.major
                tgt_ver = tgt_info.major
                self.db_versions["source"] = src_ver
                self.db_versions["target"] = tgt_ver
            except Exception as e:
                messagebox.showerror("Validation Error", f"Failed to verify PG versions: {str(e)}")
                self.select_page("Connections")
                return

        if src_ver > tgt_ver:
            messagebox.showerror(
                "Migration Blocked",
                f"Cannot migrate from a higher PG version ({src_ver}) to a lower PG version ({tgt_ver})."
            )
            self.select_page("Connections")
            return

        method = self.method_var.get()
        dry_run = self.dry_run_var.get()

        context = MigrationContext(
            source_dsn=source_dsn,
            target_dsn=target_dsn,
            migration_method=method,
            dry_run=dry_run
        )

        def progress_callback(text: str, pct: float):
            self.log_queue.put(("progress", pct, text))

        engine = MigrationEngine(context, progress_callback=progress_callback)

        self.btn_start.configure(state="disabled", fg_color="gray", text="MIGRATING...")
        self.progress_bar.set(0)
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self._append_log("Starting migration process...")

        def run_worker():
            try:
                success = engine.run()
                self.log_queue.put(("done", success))
            except Exception as e:
                self.log_queue.put(("log", "ERROR", f"Unhandled exception: {str(e)}"))
                self.log_queue.put(("done", False))

        threading.Thread(target=run_worker, daemon=True).start()


if __name__ == "__main__":
    app = MigratorApp()
    app.mainloop()