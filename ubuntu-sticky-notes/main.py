import sys
import os
from datetime import datetime

# --- Basic Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# --- Translation Setup ---
import gettext
import locale
import builtins

APP_ID = 'ubuntu-sticky-notes'
LOCALE_DIR = os.path.join(current_dir, 'locale')

try:
    from config.config_manager import ConfigManager
    config = ConfigManager.load()
    lang_code = config.get("language", "en")

    # Set up gettext
    translation = gettext.translation(APP_ID, localedir=LOCALE_DIR, languages=[lang_code], fallback=True)
    builtins._ = translation.gettext
    print(f"SYSTEM: Language set to '{lang_code}'")

except FileNotFoundError:
    builtins._ = lambda s: s
    print("SYSTEM: No translation files found. Falling back to default language.")
except Exception as e:
    builtins._ = lambda s: s
    print(f"CRITICAL: Translation setup failed: {e}")


# --- Backend Selection ---
try:
    if "--x11" in sys.argv or config.get("backend") == "x11":
        os.environ["GDK_BACKEND"] = "x11"
        print("SYSTEM: Environment forced to X11")
    else:
        os.environ["GDK_BACKEND"] = "wayland"
        print("SYSTEM: Environment set to Wayland")
except Exception as e:
    print(f"CRITICAL: Config pre-init error: {e}")


import threading
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, GLib
from db.db_controller import NotesDB
from config.config import get_app_paths, load_app_info
from views.main_view.main_view import MainWindow


class StickyApp(Adw.Application):
    APP_INFO = load_app_info()
    def __init__(self):
        super().__init__(application_id=self.APP_INFO.get('service_name'))

        self.config = ConfigManager.load()
        db_path = self.config.get("db_path")

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

    def apply_ui_scale(self, scale):
        """Applies UI scaling by setting DPI and custom CSS."""
        try:
            new_dpi = int(96 * scale * 1024)
            settings = Gtk.Settings.get_default()
            if settings:
                settings.set_property("gtk-xft-dpi", new_dpi)
        except Exception as e:
            print(f"ERROR: Failed to set DPI: {e}")

        custom_css = f"""
        * {{
            -gtk-icon-size: {int(16 * scale)}px;
        }}
        .sticky-window {{
            font-size: {10 * scale}pt;
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

    def do_activate(self):
        """Инициализация главного окна приложения."""
        self.config = ConfigManager.load()
        
        try:
            raw_scale = self.config.get("ui_scale", 1.0)
            scale = float(str(raw_scale)[:4])
            if not (0.5 <= scale <= 2.0):
                scale = 1.0
        except (ValueError, TypeError):
            scale = 1.0
        
        self.apply_ui_scale(scale)

        display = Gdk.Display.get_default()
        print(f"DEBUG: Actual running backend: {display.__class__.__name__}")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "resources", "icons")

        if os.path.exists(icons_dir):
            icon_theme = Gtk.IconTheme.get_for_display(display)
            icon_theme.add_search_path(icons_dir)
            Gtk.Window.set_default_icon_name("app")

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
        
        # Pass language setting to tray process
        lang_code = self.config.get("language", "en")
        env['STICKY_NOTES_LANG'] = lang_code
        
        if "GDK_BACKEND" in os.environ:
            del env["GDK_BACKEND"]

        self.tray_process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Capture stderr for logging
            text=True,
            bufsize=1,
            env=env
        )

        # Monitor both stdout and stderr
        threading.Thread(target=self.monitor_tray_output, args=(self.tray_process.stdout, "TRAY"), daemon=True).start()
        threading.Thread(target=self.monitor_tray_output, args=(self.tray_process.stderr, "TRAY_ERROR"), daemon=True).start()


    def monitor_tray_output(self, pipe, prefix):
        """Monitors commands or errors from the tray process."""
        if not pipe:
            return
        try:
            for line in iter(pipe.readline, ''):
                cmd = line.strip()
                if not cmd: continue

                if prefix == "TRAY_ERROR":
                    print(f"{prefix}: {cmd}")
                    continue

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
            application_name=info.get("app_name"),
            version=info.get("version"),
            developer_name=info.get("author"),
            license_type=Gtk.License.MIT_X11,
            website=info.get("website"),
            comments=_("A simple and fast sticky notes app for Ubuntu."),
            application_icon="app"
        )

        author = info.get("author")
        email = info.get("email")
        if email:
            dialog.set_developers([f"{author} <{email}>"])
        else:
            dialog.set_developers([author])
        dialog.set_copyright(_("© {year} {author}").format(year=datetime.now().year, author=author))
        dialog.present()

    def quit_app(self):
        """Safely shuts down the tray process and the application."""
        # Close DB connection first
        if self.db:
            self.db.close()

        if self.tray_process:
            self.tray_process.terminate()

        if self.win:
            for note_id in list(self.win.stickies.keys()):
                win = self.win.stickies.get(note_id)
                if win: win.close()
            self.win.destroy()

        self.quit()


if __name__ == "__main__":
    APP_INFO = load_app_info()
    GLib.set_prgname(APP_INFO.get('service_name', 'com.ubuntu.sticky.notes'))
    GLib.set_application_name(APP_INFO.get('app_name'))
    app = StickyApp()
    sys.exit(app.run(sys.argv))