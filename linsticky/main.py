"""
Main entry point for the LinSticky application.

This script handles the complete application lifecycle, including:
- Setting up the Python path.
- Initializing internationalization (i18n) with gettext.
- Selecting the GDK backend (Wayland or X11).
- Defining and running the main Adw.Application class.
"""
import sys
import os
import gettext
import locale
import builtins
import signal
import gi

# Ensure the project's root directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config.config import load_app_info, LOCALE_MAP

# --- Internationalization (i18n) Setup ---
APP_INFO = load_app_info()
APP_ID = APP_INFO.get('service_name')
LOCALE_DIR = os.path.join(current_dir, 'locale')

try:
    from config.config_manager import ConfigManager
    config = ConfigManager.load()
    lang_code = config.get("language", "en")
    
    # Set environment variables for gettext to find the correct translation files.
    full_locale = LOCALE_MAP.get(lang_code, f"{lang_code}.UTF-8")
    os.environ["LANG"] = full_locale
    os.environ["LC_ALL"] = full_locale
    os.environ["LANGUAGE"] = lang_code 

    try:
        locale.setlocale(locale.LC_ALL, full_locale)
    except locale.Error:
        print(f"WARNING: Locale {full_locale} not supported by the system. Falling back.")

    # Install the translation for the chosen language.
    translation = gettext.translation(APP_ID, localedir=LOCALE_DIR, languages=[lang_code], fallback=True)
    translation.install() 
    builtins._ = translation.gettext
    
    print(f"SYSTEM: Language set to '{lang_code}' (Locale: {full_locale})")

except Exception as e:
    # If translation fails, provide a fallback `_` function that does nothing.
    builtins._ = lambda s: s
    print(f"WARNING: Translation setup failed: {e}. Using fallback language.")

# --- GDK Backend Selection ---
# Forcing a backend can be useful for debugging or ensuring compatibility.
# Wayland is preferred for modern systems, but X11 provides broader support.
try:
    if "--x11" in sys.argv or config.get("backend") == "x11":
        os.environ["GDK_BACKEND"] = "x11"
        print("SYSTEM: Environment forced to X11 backend.")
    else:
        os.environ["GDK_BACKEND"] = "wayland,x11"
        print("SYSTEM: Environment set to Wayland with X11 fallback.")
except Exception as e:
    print(f"CRITICAL: Backend selection failed: {e}")

# --- GTK and Adwaita Initialization ---
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, GLib
from db.db_controller import NotesDB
from application_manager import ApplicationManager


class StickyApp(Adw.Application):
    """
    The main application class for LinSticky.
    
    This class orchestrates the entire application, including database connections,
    window management, and handling system signals for graceful shutdown.
    It inherits from Adw.Application to ensure proper integration with the GNOME desktop.
    """
    APP_INFO = load_app_info()

    def __init__(self):
        """Initializes the application, database, and the core application manager."""
        super().__init__(application_id=self.APP_INFO.get('service_name'))
        self.config = ConfigManager.load()
        self.db = NotesDB(path=self.config.get("db_path"))
        self.app_manager = ApplicationManager(self, self.db, self.config)
        
        # Register signal handlers for graceful shutdown (e.g., from systemctl or kill).
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self._on_signal_quit, None)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self._on_signal_quit, None)

    def do_activate(self):
        """
        Called when the application is activated (e.g., launched for the first time).
        
        This method sets up the main UI components, including the main window and tray icon,
        and restores any previously opened notes.
        """
        self.app_manager.setup_ui_settings()
        self.app_manager.setup_main_window()
        self.app_manager.start_tray_subprocess()
        
        if hasattr(self.app_manager, 'restore_notes'):
            self.app_manager.restore_notes()

    def _on_signal_quit(self, *args):
        """
        Callback for UNIX signals (SIGTERM, SIGINT) to ensure a clean exit.
        """
        self.quit_app()
        return GLib.SOURCE_REMOVE

    def quit_app(self):
        """
        Safely shuts down all application components, saves data, and closes the database.
        """
        self.app_manager.quit_app_manager()
        if self.db:
            self.db.close()
        self.quit()


if __name__ == "__main__":
    # Set application metadata for the desktop environment.
    # GLib.set_prgname is crucial for window managers (especially on X11) to correctly
    # associate the .desktop file with the running process (using StartupWMClass).
    APP_INFO = load_app_info()
    GLib.set_prgname(APP_INFO.get('service_name'))
    GLib.set_application_name(APP_INFO.get('app_name'))
    
    app = StickyApp()
    sys.exit(app.run(sys.argv))
