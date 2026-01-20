#!/usr/bin/env python3
"""Configuration module for Ubuntu Sticky Notes.

Provides path management, application metadata loading, and configuration
constants. Works with ConfigManager for complete configuration handling.
"""

import json
import os
from config.config_manager import ConfigManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "../resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
STYLE_CSS = os.path.join(RESOURCES_DIR, "style.css")
APP_INFO_FILE = os.path.join(BASE_DIR, "../app_info.json")
AUTOSAVE_INTERVAL_MS = 2000
STICKY_COLORS = ['#FFF59D', '#F8BBD0', '#C8E6C9', '#B3E5FC']


def load_app_info(path: str = APP_INFO_FILE) -> dict:
    """Load application metadata from JSON file.
    
    Args:
        path: Path to the JSON metadata file.
    
    Returns:
        Dictionary containing application metadata.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_app_paths() -> dict:
    """Get all essential application paths and directories.
    
    Combines static paths (resources, icons, CSS) with dynamic paths from
    user configuration. Creates necessary directories if they don't exist.
    
    Returns:
        Dictionary containing APP_INFO, DATA_DIR, DB_PATH, CONFIG_PATH,
        ICONS_DIR, APP_ICON_PATH, STYLE_CSS, and BACKEND.
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