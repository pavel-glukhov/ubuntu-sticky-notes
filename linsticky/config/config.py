"""
Application-wide Constants and Path Definitions.

This module centralizes the definition of paths, metadata, and other constants
used throughout the application.
"""
import json
import os

# --- Path Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "../resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
STYLE_CSS = os.path.join(RESOURCES_DIR, "style.css")
LOCALE_DIR = os.path.join(BASE_DIR, "../locale")
APP_INFO_FILE = os.path.join(BASE_DIR, "../app_info.json")

# --- Language and Locale Mappings ---
# Maps language codes to their native display names for UI elements.
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

# Maps language codes to their full locale identifiers for system-level setup.
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

def get_supported_languages() -> dict:
    """
    Scans the locale directory to find available translations.

    Returns:
        A dictionary mapping language display names to their corresponding codes.
        Always includes English as a default.
    """
    languages = {"English": "en"}
    if not os.path.exists(LOCALE_DIR):
        return languages
        
    for entry in os.listdir(LOCALE_DIR):
        if os.path.isdir(os.path.join(LOCALE_DIR, entry, "LC_MESSAGES")):
            lang_code = entry
            display_name = LANGUAGE_NAMES.get(lang_code, lang_code)
            languages[display_name] = lang_code
    return languages

def load_app_info() -> dict:
    """
    Loads application metadata (version, author, etc.) from app_info.json.

    Returns:
        A dictionary containing the application's metadata.
    """
    with open(APP_INFO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_app_paths(user_config: dict) -> dict:
    """
    Resolves and returns a dictionary of essential application paths.

    This function ensures that the directory for the database exists, creating it
    if necessary. It includes a fallback to a temporary directory if the primary
    location is not writable, which is crucial for robustness in restricted
    environments like Snap.

    Args:
        user_config: The pre-loaded user configuration dictionary.

    Returns:
        A dictionary containing key application paths.
    """
    app_info = load_app_info()
    db_path = user_config.get("db_path")

    if not db_path:
        # Avoid circular import by importing ConfigManager only when needed.
        from .config_manager import ConfigManager
        defaults = ConfigManager.get_defaults()
        db_path = defaults.get("db_path")

    # Ensure the database directory exists.
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except OSError as e:
        print(f"CRITICAL: Failed to create database directory at {os.path.dirname(db_path)}: {e}")
        # Fallback to a temporary directory to prevent crashing.
        import tempfile
        fallback_dir = os.path.join(tempfile.gettempdir(), "linsticky_fallback")
        os.makedirs(fallback_dir, exist_ok=True)
        db_path = os.path.join(fallback_dir, "notes.db")
        print(f"SYSTEM: Using temporary fallback database at: {db_path}")

    return {
        "APP_INFO": app_info,
        "DATA_DIR": os.path.dirname(db_path),
        "DB_PATH": db_path,
        "ICONS_DIR": ICONS_DIR,
        "APP_ICON_PATH": os.path.join(ICONS_DIR, "app.png"),
        "STYLE_CSS": STYLE_CSS,
        "BACKEND": user_config.get("backend", "wayland")
    }
