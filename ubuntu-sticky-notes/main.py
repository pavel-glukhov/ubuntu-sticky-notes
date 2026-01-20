#!/usr/bin/env python3
"""Ubuntu Sticky Notes - Main Application Entry Point

This module serves as the main entry point for the Ubuntu Sticky Notes application.
It handles GTK4/Libadwaita initialization, backend configuration (Wayland/X11),
and manages the application lifecycle including system tray integration.

@module: main
@author: Pavel Glukhov
@version: 2.0.0-beta1
@license: MIT
"""

import sys
import os
from datetime import datetime

# Ensure the current directory is in Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ============================================================================
# Pre-initialization: Backend Configuration
# ============================================================================
# This section must run BEFORE importing GTK to set the correct display backend.
# The GDK_BACKEND environment variable determines whether the app uses Wayland
# or X11 for window management and positioning.
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

# ============================================================================
# GTK/Libadwaita Initialization
# ============================================================================
import threading
import subprocess
import gi

# Require specific GTK4 and Libadwaita versions
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, GLib
from db.db_controller import NotesDB
from config.config import get_app_paths, load_app_info
from views.main_view.main_view import MainWindow


class StickyApp(Adw.Application):
    """Main Application Class for Ubuntu Sticky Notes
    
    This class extends Adw.Application to provide the core application logic,
    including database management, window lifecycle, system tray integration,
    and inter-process communication.
    
    @extends: Adw.Application
    
    @property {dict} APP_INFO - Application metadata loaded from app_info.json
    @property {dict} config - User configuration loaded from ConfigManager
    @property {NotesDB} db - Database controller instance
    @property {MainWindow} win - Main application window instance
    @property {subprocess.Popen} tray_process - System tray subprocess handle
    @property {threading.Thread} monitor_thread - Thread monitoring tray commands
    
    @example:
        app = StickyApp()
        sys.exit(app.run(sys.argv))
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
        """Load and apply custom CSS stylesheet
        
        Loads the application's custom CSS file from resources/style.css and
        applies it to the default display with APPLICATION priority level.
        This allows for custom styling of sticky notes, buttons, and UI elements.
        
        @method
        @returns {void}
        @throws {Exception} - Logs error if CSS file cannot be loaded
        
        @see resources/style.css for styling definitions
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
        """Apply user-defined UI scaling to the interface
        
        Reads the ui_scale setting from configuration (default: 1.0) and applies
        it to both the GTK DPI settings and custom CSS. This affects icon sizes,
        font sizes, and overall UI element dimensions.
        
        @method
        @returns {void}
        
        @param {float} scale - Scale factor from config (0.5 to 2.0)
        
        @example:
            // Config: { "ui_scale": 1.25 }
            // Results in: 125% UI scaling, DPI = 122.88
        
        @note: Scale values outside 0.5-2.0 range are clamped to 1.0
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
        """Apply custom CSS with dynamic scaling
        
        Generates and applies CSS rules with dynamically calculated sizes based
        on the provided scale factor. This is used for runtime scaling adjustments.
        
        @method
        @param {float} scale - Scale multiplier for UI elements
        @returns {void}
        
        @example:
            self.apply_custom_scale_css(1.5)
            // Icon size: 24px, Font size: 15pt
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
        """Activate the application and create the main window
        
        This is the main GTK application activation callback. It performs the
        following initialization steps:
        1. Reload configuration
        2. Apply UI scaling
        3. Detect and log the active backend (Wayland/X11)
        4. Set up application icon theme
        5. Load custom CSS
        6. Create the main window (if not exists)
        7. Start the system tray subprocess
        8. Present the window to the user
        
        @override
        @method
        @returns {void}
        
        @note: This method is called by GTK when the application is activated
        @see Adw.Application.do_activate for more information
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
        """Handle window close request - minimize to tray
        
        Instead of terminating the application when the main window is closed,
        this handler hides the window and keeps the app running in the system tray.
        This allows users to quickly restore the window from the tray icon.
        
        @method
        @param {Gtk.Window} window - The window requesting to close
        @returns {boolean} - True to prevent default close behavior
        
        @note: Returns True to stop the close event propagation
        """
        window.set_visible(False)
        return True

    def start_tray_subprocess(self):
        """Start the system tray icon as a separate process
        
        Launches tray.py as an independent subprocess using GTK3 to avoid
        conflicts with the main GTK4 application. The tray process communicates
        with the main app via stdout, sending command strings that are monitored
        by a dedicated thread.
        
        @method
        @returns {void}
        
        @note: GTK3 and GTK4 cannot coexist in the same process
        @note: The GDK_BACKEND env variable is removed to let tray choose its backend
        
        @see monitor_tray_output for command handling
        @see tray.py for the tray implementation
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
        """Monitor and process commands from the tray subprocess
        
        Runs in a daemon thread to continuously read stdout from the tray process.
        When a command is received, it's dispatched to the appropriate handler
        using GLib.idle_add to ensure thread-safe GTK operations.
        
        @method
        @returns {void}
        
        @param {string} cmd - Command string from tray (quit, show_main, open_all, about)
        
        Supported commands:
        - "quit": Terminate the application
        - "show_main": Show and focus the main window
        - "open_all": Open all sticky notes from database
        - "about": Display the about dialog
        
        @note: Runs in a daemon thread, terminates with main process
        @throws {Exception} - Logged if tray process terminates unexpectedly
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
        """Show and present the main application window
        
        Makes the main window visible and brings it to focus. This is typically
        called from the tray icon menu when the user wants to restore the window.
        
        @method
        @returns {void}
        
        @note: Called via GLib.idle_add from the tray monitor thread
        """
        if self.win:
            self.win.set_visible(True)
            self.win.present()

    def open_all_stickers(self):
        """Open all sticky notes from the database
        
        Retrieves all non-deleted notes from the database and opens each one
        in its own sticky note window. This is useful for quickly restoring
        the user's workspace.
        
        @method
        @returns {void}
        
        @note: Only opens notes marked as non-deleted (deleted=0)
        @note: Called from tray menu "Open All Notes" option
        
        @see MainWindow.open_note for individual note opening logic
        """
        notes = self.db.all_notes(full=False)
        for note in notes:
            self.win.open_note(note['id'])

    def show_about_dialog(self):
        """Display the About dialog with application information
        
        Creates and presents an Adw.AboutWindow containing app metadata such as
        name, version, author, license, website, and description. The information
        is loaded from app_info.json.
        
        @method
        @returns {void}
        
        @note: Dialog is transient to main window if visible
        @note: Copyright year is dynamically generated
        
        @see app_info.json for metadata source
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
        """Safely shut down the application and all sub-processes
        
        Performs a clean shutdown sequence:
        1. Terminate the tray subprocess
        2. Close all open sticky note windows
        3. Destroy the main window
        4. Quit the GTK application
        
        @method
        @returns {void}
        
        @note: All sticky notes are saved before closing (auto-save)
        @note: Called from tray "Quit" menu or when quit command is received
        
        @see StickyWindow.close for individual note cleanup
        """
        if self.tray_process:
            self.tray_process.terminate()

        if self.win:
            for note_id in list(self.win.stickies.keys()):
                win = self.win.stickies.get(note_id)
                if win: win.close()
            self.win.destroy()

        self.quit()


# ============================================================================
# Application Entry Point
# ============================================================================
if __name__ == "__main__":
    # Load application metadata
    APP_INFO = load_app_info()
    
    # Set GLib application identifiers for proper desktop integration
    GLib.set_prgname(APP_INFO.get('service_name', 'com.ubuntu.sticky.notes'))
    GLib.set_application_name(APP_INFO.get('app_name'))
    
    # Create and run the application instance
    app = StickyApp()
    sys.exit(app.run(sys.argv))