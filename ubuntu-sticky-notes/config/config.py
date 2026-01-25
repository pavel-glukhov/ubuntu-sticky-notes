import json
import os
from config.config_manager import ConfigManager

# ========================
# Path Constants (System)
# ========================
# Path to the directory where config.py is located (project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Resource Paths
RESOURCES_DIR = os.path.join(BASE_DIR, "../resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
STYLE_CSS = os.path.join(RESOURCES_DIR, "style.css")

# Metadata
APP_INFO_FILE = os.path.join(BASE_DIR, "../app_info.json")

# Intervals and Settings
AUTOSAVE_INTERVAL_MS = 2000
STICKY_COLORS = ['#FFF59D', '#F8BBD0', '#C8E6C9', '#B3E5FC']
TEXT_COLORS = ['#000000', '#424242', '#D32F2F', '#C2185B', '#7B1FA2', '#303F9F', '#1976D2', '#0288D1', '#0097A7', '#00796B', '#388E3C', '#689F38', '#AFB42B', '#FBC02D', '#FFA000', '#E64A19']
FONT_SIZES = [8, 10, 12, 14, 16, 18, 20, 24, 32, 48, 72]


def load_app_info(path: str = APP_INFO_FILE) -> dict:
    """Loads application metadata from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_app_paths() -> dict:
    """
    Returns a dictionary of all essential application paths.
    DB_PATH is dynamically retrieved from the user configuration.
    """
    app_info = load_app_info()
    user_config = ConfigManager.load()

    db_path = user_config.get("db_path")

    if not db_path:
        data_dir = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "share",
            app_info.get("service_name")
        )
        db_path = os.path.join(data_dir, "stickies.db")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    return {
        "APP_INFO": app_info,
        "DATA_DIR": os.path.dirname(db_path),
        "DB_PATH": db_path,
        "CONFIG_PATH": os.path.expanduser("~/.config/ubuntu-sticky-notes/config.conf"),
        "ICONS_DIR": ICONS_DIR,
        "APP_ICON_PATH": os.path.join(ICONS_DIR, "app.png"),
        "STYLE_CSS": STYLE_CSS,
        "BACKEND": user_config.get("backend", "wayland")
    }