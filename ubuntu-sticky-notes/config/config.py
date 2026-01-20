#!/usr/bin/env python3
"""Configuration Module for Ubuntu Sticky Notes

This module provides path management, application metadata loading, and
configuration constants for the Ubuntu Sticky Notes application. It centralizes
all file system paths, resource locations, and application settings.

The module works in conjunction with ConfigManager to provide a complete
configuration system that handles both static (hard-coded) and dynamic
(user-configurable) settings.

Author: Pavel Glukhov
Version: 2.0.0-beta1
License: MIT

Module Constants:
    BASE_DIR: Project root directory
    RESOURCES_DIR: Resources folder path
    ICONS_DIR: Application icons directory
    STYLE_CSS: CSS stylesheet path
    APP_INFO_FILE: Application metadata JSON file
    AUTOSAVE_INTERVAL_MS: Auto-save interval in milliseconds
    STICKY_COLORS: Default color palette for sticky notes

Examples:
    >>> from config.config import get_app_paths, STICKY_COLORS
    >>> paths = get_app_paths()
    >>> print(paths['DB_PATH'])
    /home/user/.local/share/ubuntu-sticky-notes/stickies.db
    >>> print(STICKY_COLORS[0])
    #FFF59D
"""

import json
import os
from config.config_manager import ConfigManager

# =============================================================================
# Path Constants (System)
# ==================================================================================================================================
# These paths are relative to the config.py location and point to application
# resources and configuration files.

# Path to the directory where config.py is located (config/ directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Resource Paths - Static application resources
RESOURCES_DIR = os.path.join(BASE_DIR, "../resources")  # Parent directory resources folder
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")        # Application icons
STYLE_CSS = os.path.join(RESOURCES_DIR, "style.css")    # GTK CSS stylesheet

# Metadata - Application information file
APP_INFO_FILE = os.path.join(BASE_DIR, "../app_info.json")

# =============================================================================
# Application Settings Constants
# =============================================================================
# Auto-save interval in milliseconds (2 seconds)
AUTOSAVE_INTERVAL_MS = 2000

# Default color palette for sticky notes (Yellow, Pink, Green, Blue)
STICKY_COLORS = ['#FFF59D', '#F8BBD0', '#C8E6C9', '#B3E5FC']


def load_app_info(path: str = APP_INFO_FILE) -> dict:
    """Load application metadata from a JSON file.
    
    Reads and parses the app_info.json file containing application metadata
    such as name, version, author, email, website, description, license, and
    dependencies.
    
    Args:
        path: Path to the JSON metadata file. Defaults to APP_INFO_FILE.
    
    Returns:
        Dictionary containing application metadata with keys:
            - service_name: Application service identifier
            - app_name: Display name of the application
            - version: Version string (e.g., "2.0.0~beta1")
            - author: Author name
            - email: Contact email
            - website: Project website URL
            - description: Application description
            - license: License type
            - architecture: Package architecture
            - dependencies: List of system dependencies
    
    Raises:
        FileNotFoundError: If the metadata file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    
    Examples:
        >>> info = load_app_info()
        >>> print(info['app_name'])
        Ubuntu Sticky Notes
        >>> print(info['version'])
        2.0.0~beta1
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_app_paths() -> dict:
    """Get all essential application paths and directories.
    
    Constructs a comprehensive dictionary of file system paths used throughout
    the application. This includes database location, configuration files,
    resource directories, and user-specific settings.
    
    The function combines static paths (resources, icons, CSS) with dynamic
    paths from user configuration (database location, backend preference).
    It also ensures that necessary directories exist by creating them if needed.
    
    Returns:
        Dictionary containing the following keys:
            - APP_INFO (dict): Application metadata from app_info.json
            - DATA_DIR (str): User data directory path
            - DB_PATH (str): SQLite database file path
            - CONFIG_PATH (str): Configuration file path (legacy)
            - ICONS_DIR (str): Application icons directory
            - APP_ICON_PATH (str): Path to main application icon
            - STYLE_CSS (str): CSS stylesheet path
            - BACKEND (str): Display backend ('wayland' or 'x11')
    
    Note:
        The database path is retrieved from user configuration via ConfigManager.
        If not set in config, defaults to:
        ~/.local/share/ubuntu-sticky-notes/stickies.db
    
    Examples:
        >>> paths = get_app_paths()
        >>> print(paths['DB_PATH'])
        /home/user/.local/share/ubuntu-sticky-notes/stickies.db
        >>> print(paths['BACKEND'])
        wayland
    
    See Also:
        ConfigManager.load(): For user configuration loading
        load_app_info(): For application metadata
    """
    app_info = load_app_info()
    user_config = ConfigManager.load()

    # Retrieve database path from user configuration
    # If not set, construct default path following XDG Base Directory specification
    db_path = user_config.get("db_path")

    if not db_path:
        # Default: ~/.local/share/ubuntu-sticky-notes/stickies.db
        data_dir = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "share",
            app_info.get("service_name")  # Dynamic service name from metadata
        )
        db_path = os.path.join(data_dir, "stickies.db")

    # Create database directory if it doesn't exist
    # This prevents errors when the application first runs
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