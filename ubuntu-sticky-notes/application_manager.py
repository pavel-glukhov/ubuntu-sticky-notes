import os
import sys
import threading
import subprocess
from datetime import datetime

import builtins

from gi.repository import Gtk, Adw, Gdk, GLib, Gio

from config.config import get_app_paths, load_app_info
from config.config_manager import ConfigManager
from views.main_view.main_view import MainWindow

_ = builtins._

class ApplicationManager:
    """
    Manages the core application logic, UI setup, tray process, and inter-process communication.
    This class encapsulates responsibilities previously held by StickyApp to improve modularity.
    """
    def __init__(self, app_instance: Adw.Application, db_instance, config_instance):
        """
        Initializes the ApplicationManager.
        Args:
            app_instance (Adw.Application): The main Adw.Application instance.
            db_instance: The NotesDB database controller instance.
            config_instance (dict): The application's configuration dictionary.
        """
        self.app = app_instance
        self.db = db_instance
        self.config = config_instance
        self.main_window = None
        self.tray_process = None

    def setup_ui_settings(self):
        """
        Applies UI scaling, loads CSS, and sets up icon themes based on configuration.
        """
        try:
            raw_scale = self.config.get("ui_scale", 1.0)
            scale = float(str(raw_scale)[:4])
            if not (0.5 <= scale <= 2.0):
                scale = 1.0
        except (ValueError, TypeError):
            scale = 1.0
        
        self._apply_ui_scale(scale)
        self._load_css()

        display = Gdk.Display.get_default()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "resources", "icons")

        if os.path.exists(icons_dir):
            icon_theme = Gtk.IconTheme.get_for_display(display)
            icon_theme.add_search_path(icons_dir)
            Gtk.Window.set_default_icon_name("app")

    def _apply_ui_scale(self, scale: float):
        """
        Applies UI scaling by setting DPI and custom CSS.
        Args:
            scale (float): The scaling factor for the UI.
        """
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

    def _load_css(self):
        """Loads custom CSS styles from the application's resource directory."""
        paths = get_app_paths(user_config=self.config)
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
            except Exception as e:
                print(f"ERROR: CSS loading failed: {e}")

    def setup_main_window(self):
        """Initializes and presents the main application window."""
        if not self.main_window:
            self.main_window = MainWindow(self.db, application=self.app)
            self.main_window.connect("close-request", self.on_main_window_close_request)
        self.main_window.present()
        self.restore_open_stickers() # Restore previously open stickers

    def on_main_window_close_request(self, window: Gtk.Window):
        """
        Handles the close request for the main window, typically hiding it to the tray.
        Args:
            window (Gtk.Window): The main window instance.
        Returns:
            bool: True to indicate the close request has been handled.
        """
        window.set_visible(False)
        return True

    def start_tray_subprocess(self):
        """
        Starts the GTK3 tray icon as a separate process to avoid library conflicts.
        Communicates with the main application via stdout/stderr.
        """
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray.py")
        env = os.environ.copy()
        
        lang_code = self.config.get("language", "en")
        env['STICKY_NOTES_LANG'] = lang_code
        
        if "GDK_BACKEND" in os.environ:
            del env["GDK_BACKEND"]

        self.tray_process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

        threading.Thread(target=self._monitor_tray_output, args=(self.tray_process.stdout, "TRAY"), daemon=True).start()
        threading.Thread(target=self._monitor_tray_output, args=(self.tray_process.stderr, "TRAY_ERROR"), daemon=True).start()

    def _monitor_tray_output(self, pipe, prefix: str):
        """
        Monitors stdout/stderr from the tray process for commands or errors.
        Args:
            pipe: The pipe to read from (stdout or stderr).
            prefix (str): A prefix for log messages (e.g., "TRAY", "TRAY_ERROR").
        """
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
                    GLib.idle_add(self.app.quit_app)
                elif cmd == "show_main":
                    GLib.idle_add(self.show_main_window)
                elif cmd == "open_all":
                    GLib.idle_add(self.open_all_stickers)
                elif cmd == "about":
                    GLib.idle_add(self.show_about_dialog)
        except Exception as e:
            print(f"DEBUG: Tray monitor thread terminated: {e}")

    def show_main_window(self):
        """Makes the main application window visible and brings it to the foreground."""
        if self.main_window:
            self.main_window.set_visible(True)
            self.main_window.present()

    def open_all_stickers(self):
        """Opens all existing sticky notes from the database as individual windows."""
        notes = self.db.all_notes(full=False)
        for note in notes:
            self.main_window.open_note(note['id'])

    def restore_open_stickers(self):
        """Restores sticky notes that were open in the previous session."""
        open_note_ids = self.db.get_open_notes()
        for note_id in open_note_ids:
            self.main_window.open_note(note_id)

    def show_about_dialog(self):
        """Displays the application's 'About' dialog."""
        if not self.main_window: return

        paths = get_app_paths(user_config=self.config)
        info = paths.get("APP_INFO", {})
        
        author = info.get("author")
        email = info.get("email")
        developers = [f"{author} <{email}>"] if email else [author]
        copyright_text = _("© {year} {author}").format(year=datetime.now().year, author=author)

        dialog = Adw.AboutWindow(
            transient_for=self.main_window if self.main_window.get_visible() else None,
            application_name=info.get("app_name"),
            version=info.get("version"),
            developer_name=info.get("author"),
            license_type=Gtk.License.MIT_X11,
            website=info.get("website"),
            comments=_("A simple and fast sticky notes app for Ubuntu."),
            application_icon="app",
            developers=developers,
            copyright=copyright_text
        )

        dialog.present()

    def quit_app_manager(self):
        """
        Safely terminates the tray process and closes all open sticky note windows.
        """
        if self.tray_process:
            self.tray_process.terminate()
        
        if self.main_window:
            for note_id in list(self.main_window.stickies.keys()):
                win = self.main_window.stickies.get(note_id)
                if win: 
                    win.close()
            self.main_window.destroy()
