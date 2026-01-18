import sys
import os
from datetime import datetime

# 1. ESSENTIAL: Set environment variables BEFORE importing Gtk/Gdk
# We add the current directory to sys.path so modules like config_manager are found correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from config.config_manager import ConfigManager

    config = ConfigManager.load()

    # Check for CLI flags first, then config file
    if "--x11" in sys.argv or config.get("backend") == "x11":
        os.environ["GDK_BACKEND"] = "x11"
        print("SYSTEM: Environment forced to X11")
    else:
        os.environ["GDK_BACKEND"] = "wayland"
        print("SYSTEM: Environment set to Wayland")
except Exception as e:
    print(f"CRITICAL: Config pre-init error: {e}")

# 2. STANDARD IMPORTS
import threading
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, GLib
from db.db_controller import NotesDB
from config.config import get_app_paths
from views.main_view.main_view import MainWindow


class StickyApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.ubuntu_sticky_notes")

        # Load config to initialize the database
        self.config = ConfigManager.load()
        db_path = self.config.get("db_path")

        # Resolve default path if config is empty
        if not db_path:
            paths = get_app_paths()
            db_path = paths["DB_PATH"]

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = NotesDB(path=db_path)

        self.win = None
        self.tray_process = None

    def load_css(self):
        """Loads custom CSS styles."""
        paths = get_app_paths()
        css_path = paths.get("STYLE_CSS")

        if css_path and os.path.exists(css_path):
            css_provider = Gtk.CssProvider()
            try:
                css_provider.load_from_path(css_path)
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                print(f"DEBUG: CSS loaded from {css_path}")
            except Exception as e:
                print(f"ERROR: CSS loading failed: {e}")

    def apply_ui_scale(self):
        try:
            raw_scale = self.config.get("ui_scale", 1.0)
            scale = float(str(raw_scale)[:4])

            if not (0.5 <= scale <= 2.0): scale = 1.0
        except (ValueError, TypeError):
            scale = 1.0

        new_dpi = int(96 * scale * 1024)
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-xft-dpi", new_dpi)

        custom_css = f"""
        * {{ 
            -gtk-icon-size: {int(16 * scale)}px; 
        }}
        .sticky-text-edit {{
            font-size: {int(12 * scale)}pt;
        }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(custom_css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        print(f"SYSTEM: UI Scale applied: {scale}")

    def apply_custom_scale_css(self, scale):
        css = f"""
        * {{ 
            -gtk-icon-size: {int(16 * scale)}px;
        }}
        .sticky-window {{
            font-size: {10 * scale}pt;
        }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):
        """Инициализация главного окна приложения."""
        self.config = ConfigManager.load()
        self.apply_ui_scale()

        display = Gdk.Display.get_default()
        print(f"DEBUG: Actual running backend: {display.__class__.__name__}")

        self.load_css()

        if not self.win:
            self.win = MainWindow(self.db, application=self)
            self.win.connect("close-request", self.on_window_close_request)
            self.start_tray_subprocess()

        self.win.present()

    def on_window_close_request(self, window):
        """Hides the window instead of closing it (minimize to tray)."""
        window.set_visible(False)
        return True

    def start_tray_subprocess(self):
        """Starts the GTK3 tray icon as a separate process to avoid library conflicts."""
        script_path = os.path.join(os.path.dirname(__file__), "tray.py")
        env = os.environ.copy()
        # Ensure tray knows which display to use
        if "GDK_BACKEND" in os.environ:
            del env["GDK_BACKEND"]  # Let tray decide its own backend (usually X11)

        self.tray_process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env
        )

        self.monitor_thread = threading.Thread(target=self.monitor_tray_output, daemon=True)
        self.monitor_thread.start()

    def monitor_tray_output(self):
        """Monitors commands sent from the tray process via stdout."""
        if not self.tray_process or not self.tray_process.stdout:
            return

        try:
            for line in iter(self.tray_process.stdout.readline, ''):
                cmd = line.strip()
                if not cmd: continue

                if cmd == "quit":
                    GLib.idle_add(self.quit_app)
                elif cmd == "show_main":
                    GLib.idle_add(self.show_main_window)
                elif cmd == "open_all":
                    GLib.idle_add(self.open_all_stickers)
                elif cmd == "about":
                    GLib.idle_add(self.show_about_dialog)
        except Exception as e:
            print(f"DEBUG: Tray monitor thread terminated: {e}")

    def show_main_window(self):
        if self.win:
            self.win.set_visible(True)
            self.win.present()

    def open_all_stickers(self):
        """Opens all existing stickers from the database."""
        notes = self.db.all_notes(full=False)
        for note in notes:
            self.win.open_note(note['id'])

    def show_about_dialog(self):
        if not self.win: return

        paths = get_app_paths()
        info = paths.get("APP_INFO", {})

        dialog = Adw.AboutWindow(
            transient_for=self.win if self.win.get_visible() else None,
            application_name=info.get("app_name", "Sticky Notes"),
            version=info.get("version", "1.0.0"),
            developer_name=info.get("author", "Unknown"),
            license_type=Gtk.License.MIT_X11,
            website=info.get("website", ""),
            comments=info.get("description", ""),
            # Using service_name as the icon name
            application_icon=info.get("service_name", "accessories-text-editor")
        )

        # Set developers list (replaces debug info for contact)
        author = info.get("author", "Unknown")
        email = info.get("email", "")
        if email:
            dialog.set_developers([f"{author} <{email}>"])
        else:
            dialog.set_developers([author])

        # Add copyright string
        dialog.set_copyright(f"© {datetime.now().year} {author}")

        dialog.present()

    def quit_app(self):
        """Safely shuts down the tray process and the application."""
        if self.tray_process:
            self.tray_process.terminate()

        if self.win:
            # Close all active sticky windows
            for note_id in list(self.win.stickies.keys()):
                win = self.win.stickies.get(note_id)
                if win: win.close()
            self.win.destroy()

        self.quit()


if __name__ == "__main__":
    app = StickyApp()
    sys.exit(app.run(sys.argv))