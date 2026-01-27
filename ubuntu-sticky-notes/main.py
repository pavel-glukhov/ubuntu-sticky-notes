import sys
import os
import gettext
import locale
import builtins
import gi
from config.config import load_app_info

# --- Basic Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# --- Translation Setup ---
APP_INFO = load_app_info()
APP_ID = 'ubuntu.sticky.notes' 
LOCALE_DIR = os.path.join(current_dir, 'locale')

# Map short language codes to full locale names
LOCALE_MAP = {
    "en": "en_US.UTF-8",
    "ru": "ru_RU.UTF-8",
    "es": "es_ES.UTF-8",
    "de": "de_DE.UTF-8",
    "fr": "fr_FR.UTF-8",
    "zh_CN": "zh_CN.UTF-8",
    "pt_BR": "pt_BR.UTF-8",
    "tr": "tr_TR.UTF-8",
    "kk": "kk_KZ.UTF-8"
}

try:
    from config.config_manager import ConfigManager
    config = ConfigManager.load()
    lang_code = config.get("language", "en")
    
    mo_path = os.path.join(LOCALE_DIR, lang_code, 'LC_MESSAGES', f'{APP_ID}.mo')
    if os.path.exists(mo_path):
        print(f"DEBUG: Found translation file at: {mo_path}")
    else:
        print(f"DEBUG: Translation file NOT found at: {mo_path}")

    # Set environment variables for gettext
    full_locale = LOCALE_MAP.get(lang_code, f"{lang_code}.UTF-8")
    os.environ["LANG"] = full_locale
    os.environ["LC_ALL"] = full_locale
    os.environ["LANGUAGE"] = lang_code 

    try:
        locale.setlocale(locale.LC_ALL, full_locale)
    except locale.Error:
        print(f"WARNING: Locale {full_locale} not supported by system. Falling back.")

    translation = gettext.translation(APP_ID, localedir=LOCALE_DIR, languages=[lang_code], fallback=True)
    translation.install()
    builtins._ = translation.gettext
    
    print(f"SYSTEM: Language set to '{lang_code}' (Locale: {full_locale})")

except FileNotFoundError:
    builtins._ = lambda s: s
    print("SYSTEM: No translation files found. Falling back to default language.")
except Exception as e:
    builtins._ = lambda s: s
    print(f"CRITICAL: Translation setup failed: {e}")

# --- Backend Selection ---
try:
    from config.config import get_app_paths
    app_paths = get_app_paths(user_config=config)
    if "--x11" in sys.argv or config.get("backend") == "x11":
        os.environ["GDK_BACKEND"] = "x11"
        print("SYSTEM: Environment forced to X11")
    else:
        os.environ["GDK_BACKEND"] = "wayland"
        print("SYSTEM: Environment set to Wayland")
except Exception as e:
    print(f"CRITICAL: Config pre-init error: {e}")

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, GLib
from db.db_controller import NotesDB
from application_manager import ApplicationManager


class StickyApp(Adw.Application):
    """Main application class for Ubuntu Sticky Notes."""
    APP_INFO = load_app_info()

    def __init__(self):
        """Initializes the application, database, and application manager."""
        super().__init__(application_id=self.APP_INFO.get('service_name'))
        self.config = ConfigManager.load()
        self.db = NotesDB(path=self.config.get("db_path"))
        self.app_manager = ApplicationManager(self, self.db, self.config)

    def do_activate(self):
        """
        Called when the application is activated.
        Sets up UI settings, the main window, and the tray icon process.
        """
        self.app_manager.setup_ui_settings()
        self.app_manager.setup_main_window()
        self.app_manager.start_tray_subprocess()

    def quit_app(self):
        """
        Safely shuts down all application components and closes the database connection.
        """
        self.app_manager.quit_app_manager()
        if self.db:
            self.db.close()
        self.quit()


if __name__ == "__main__":
    APP_INFO = load_app_info()
    GLib.set_prgname(APP_INFO.get('service_name'))
    GLib.set_application_name(APP_INFO.get('app_name'))
    app = StickyApp()
    sys.exit(app.run(sys.argv))