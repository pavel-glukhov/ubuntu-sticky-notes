import json
import os

# ========================
# Path Constants (System)
# ========================
# Path to the directory where config.py is located (project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Resource Paths
RESOURCES_DIR = os.path.join(BASE_DIR, "../resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
STYLE_CSS = os.path.join(RESOURCES_DIR, "style.css")
LOCALE_DIR = os.path.join(BASE_DIR, "../locale")

# Metadata
APP_INFO_FILE = os.path.join(BASE_DIR, "../app_info.json")

# Intervals and Settings
AUTOSAVE_INTERVAL_MS = 2000

# Language Display Names Mapping
LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Русский",
    "es": "Español",
    "de": "Deutsch",
    "fr": "Français",
    "zh_CN": "简体中文",
    "pt_BR": "Português (Brasil)",
    "tr": "Türkçe",
    "kk": "Қазақша"
}

def get_supported_languages() -> dict:
    """
    Scans the locale directory for available languages and returns a dictionary
    mapping display names to language codes.
    Always includes 'en' (English) as the default.
    Returns:
        dict: A dictionary where keys are display names and values are language codes.
    """
    languages = {"English": "en"}
    
    if os.path.exists(LOCALE_DIR):
        for entry in os.listdir(LOCALE_DIR):
            full_path = os.path.join(LOCALE_DIR, entry)
            if os.path.isdir(full_path):
                if os.path.exists(os.path.join(full_path, "LC_MESSAGES")):
                    lang_code = entry
                    display_name = LANGUAGE_NAMES.get(lang_code, lang_code)
                    languages[display_name] = lang_code
    
    return languages


def load_app_info(path: str = APP_INFO_FILE) -> dict:
    """
    Loads application metadata from a JSON file.
    Args:
        path (str, optional): Path to the app_info.json file. Defaults to APP_INFO_FILE.
    Returns:
        dict: The application metadata.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_app_paths(user_config: dict) -> dict:
    """
    Returns a dictionary of all essential application paths.
    DB_PATH is dynamically retrieved from the user configuration.
    Args:
        user_config (dict): Pre-loaded user configuration.
    Returns:
        dict: A dictionary containing paths and backend info.
    """
    app_info = load_app_info()
    
    db_path = user_config.get("db_path")

    if not db_path:
        # Import ConfigManager only if needed, to avoid circular dependency
        from config.config_manager import ConfigManager
        defaults = ConfigManager.get_defaults()
        db_path = defaults.get("db_path")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    return {
        "APP_INFO": app_info,
        "DATA_DIR": os.path.dirname(db_path),
        "DB_PATH": db_path,
        "ICONS_DIR": ICONS_DIR,
        "APP_ICON_PATH": os.path.join(ICONS_DIR, "app.png"),
        "STYLE_CSS": STYLE_CSS,
        "BACKEND": user_config.get("backend", "wayland")
    }