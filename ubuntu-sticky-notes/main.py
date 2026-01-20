#!/usr/bin/env python3
"""Main application module for Ubuntu Sticky Notes.

This module serves as the entry point for the Ubuntu Sticky Notes application.
It initializes GTK4/Libadwaita, configures the display backend (Wayland/X11),
manages the application lifecycle, and handles system tray integration.

The module must configure the GDK_BACKEND environment variable before importing
GTK libraries to ensure proper display server selection.
"""

import sys
import os
from datetime import datetime

# Ensure the current directory is in Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Backend configuration must occur before GTK import
try:
    from config.config_manager import ConfigManager

    config = ConfigManager.load()

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
    """Main application class extending Adw.Application.
    
    Manages the core application logic including database operations,
    window lifecycle, system tray integration, and inter-process
    communication with the tray subprocess.
    
    Attributes:
        APP_INFO: Application metadata loaded from app_info.json
        config: User configuration dictionary from ConfigManager
        db: Database controller instance (NotesDB)
        win: Main application window instance (MainWindow)
        tray_process: System tray subprocess handle
        monitor_thread: Daemon thread monitoring tray commands
    """
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
        """Load and apply the custom CSS stylesheet.
        
        Loads resources/style.css and applies it to the default display
        with APPLICATION priority level for custom styling of sticky notes,
        buttons, and other UI elements. Errors are logged but do not prevent
        application startup.
        """
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
        """Apply user-defined UI scaling to the interface.
        
        Reads the ui_scale setting from configuration (default 1.0) and applies
        it to GTK DPI settings and custom CSS. This affects icon sizes, font
        sizes, and overall UI element dimensions. Scale values outside the
        0.5-2.0 range are clamped to 1.0.
        """
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
        """Apply custom CSS with dynamic scaling.
        
        Generates and applies CSS rules with sizes calculated from the
        provided scale factor for runtime scaling adjustments.
        
        Args:
            scale: Scale multiplier for UI elements.
        """
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
        """Activate the application and create the main window.
        
        This GTK application activation callback performs initialization:
        reloads configuration, applies UI scaling, detects the active backend,
        sets up the icon theme, loads CSS, creates the main window, starts
        the tray subprocess, and presents the window.
        
        This method is called by GTK when the application is activated.
        """
        self.config = ConfigManager.load()
        self.apply_ui_scale()

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
        """Handle window close request by minimizing to tray.
        
        Hides the window instead of terminating the application, keeping
        it running in the system tray for quick restoration.
        
        Args:
            window: The window requesting to close.
        
        Returns:
            True to prevent the default close behavior.
        """
        window.set_visible(False)
        return True

    def start_tray_subprocess(self):
        """Start the system tray icon as a separate process.
        
        Launches tray.py as an independent subprocess using GTK3 to avoid
        conflicts with the main GTK4 application. The tray process communicates
        via stdout with command strings monitored by a dedicated thread.
        
        Note:
            GTK3 and GTK4 cannot coexist in the same process. The GDK_BACKEND
            environment variable is removed to allow the tray to choose its
            own backend.
        """
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
        """Monitor and process commands from the tray subprocess.
        
        Runs in a daemon thread to continuously read stdout from the tray
        process. Commands are dispatched to appropriate handlers using
        GLib.idle_add for thread-safe GTK operations.
        
        Supported commands:
            quit: Terminate the application
            show_main: Show and focus the main window
            open_all: Open all sticky notes from database
            about: Display the about dialog
        
        Note:
            Runs in a daemon thread and terminates with the main process.
        """
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
        """Show and present the main application window.
        
        Makes the main window visible and brings it to focus. Typically
        called from the tray icon menu via GLib.idle_add.
        """
        if self.win:
            self.win.set_visible(True)
            self.win.present()

    def open_all_stickers(self):
        """Open all sticky notes from the database.
        
        Retrieves all non-deleted notes and opens each in its own window.
        Useful for quickly restoring the user's workspace. Called from the
        tray menu 'Open All Notes' option.
        """
        notes = self.db.all_notes(full=False)
        for note in notes:
            self.win.open_note(note['id'])

    def show_about_dialog(self):
        """Display the About dialog with application information.
        
        Creates and presents an Adw.AboutWindow containing metadata from
        app_info.json including name, version, author, license, website,
        and description. The dialog is transient to the main window if
        visible, and the copyright year is dynamically generated.
        """
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
            comments=info.get("description"),
            application_icon="app"
        )

        # Set developers list (replaces debug info for contact)
        author = info.get("author")
        email = info.get("email")
        if email:
            dialog.set_developers([f"{author} <{email}>"])
        else:
            dialog.set_developers([author])
        dialog.set_copyright(f"© {datetime.now().year} {author}")
        dialog.present()

    def quit_app(self):
        """Safely shut down the application and all subprocesses.
        
        Performs clean shutdown: terminates the tray subprocess, closes all
        open sticky note windows (with auto-save), destroys the main window,
        and quits the GTK application. Called from the tray 'Quit' menu.
        """
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