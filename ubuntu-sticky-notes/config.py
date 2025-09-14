import os
import json

# ========================
# Constants
# ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_INFO_FILE = os.path.join(BASE_DIR, "app_info.json")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
UI_DIR = os.path.join(RESOURCES_DIR, "ui")

AUTOSAVE_INTERVAL_MS = 2000
COLOR_MAP = {
    "Yellow": "#FFF59D",
    "Green": "#C8E6C9",
    "Blue": "#BBDEFB",
    "Pink": "#F8BBD0"
}

"""
BASE_DIR: The absolute path to the directory containing this configuration file.
APP_INFO_FILE: Path to the JSON file containing application metadata such as name, version, author, etc.
RESOURCES_DIR: Path to the resources directory, containing icons and UI files.
ICONS_DIR: Path to the icons subdirectory inside resources.
UI_DIR: Path to the UI files subdirectory inside resources.
AUTOSAVE_INTERVAL_MS: Interval in milliseconds for automatic saving of sticky notes.
COLOR_MAP: Dictionary mapping color names to their corresponding HEX color codes.
"""


def load_app_info(path: str = APP_INFO_FILE) -> dict:
    """
    Load application metadata from a JSON file.

    Args:
        path (str): Path to the JSON file containing app information. Defaults to APP_INFO_FILE.

    Returns:
        dict: A dictionary containing application information such as name, version, author, email, website,
              description, and license.

    Raises:
        FileNotFoundError: If the JSON file does not exist at the specified path.
        json.JSONDecodeError: If the JSON file contains invalid JSON.

    Example:
        >>> info = load_app_info()
        >>> print(info['name'])
        'Ubuntu Sticky Notes'
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_data_dir(app_name: str) -> str:
    """
    Get the path to the application's data directory in the user's home folder and create it if it does not exist.

    Args:
        app_name (str): The name of the application. Used to create a folder in the user's home directory.

    Returns:
        str: Absolute path to the application's data directory.

    Notes:
        The directory is created at:
        ~/.local/share/<app_name_in_lowercase_with_dashes>

    Example:
        >>> get_data_dir('Ubuntu Sticky Notes')
        '/home/user/.local/share/ubuntu-sticky-notes'
    """
    data_dir = os.path.join(
        os.path.expanduser("~"),
        ".local",
        "share",
        app_name.replace(' ', '-').lower()
    )
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path(data_dir: str) -> str:
    """
    Get the full path to the database file used by the application.

    Args:
        data_dir (str): Path to the application's data directory.

    Returns:
        str: Absolute path to the database file named 'stickies.db' inside the data directory.

    Example:
        >>> get_db_path('/home/user/.local/share/ubuntu-sticky-notes')
        '/home/user/.local/share/ubuntu-sticky-notes/stickies.db'
    """
    return os.path.join(data_dir, "stickies.db")


def get_app_paths() -> dict:
    """
    Return a dictionary containing all essential paths and application information.

    This function loads the app info from JSON, determines the data directory, database path,
    and provides paths for icons and UI resources.

    Returns:
        dict: A dictionary with the following keys:
            - "APP_INFO": Dictionary of application metadata loaded from JSON.
            - "DATA_DIR": Path to the application's data directory.
            - "DB_PATH": Path to the SQLite database file.
            - "ICONS_DIR": Path to the icons directory.
            - "APP_ICON_PATH": Full path to the main application icon.
            - "UI_DIR": Path to the UI files directory.

    Example:
        >>> paths = get_app_paths()
        >>> print(paths['APP_INFO']['name'])
        'Ubuntu Sticky Notes'
        >>> print(paths['DB_PATH'])
        '/home/user/.local/share/ubuntu-sticky-notes/stickies.db'
    """
    app_info = load_app_info()
    data_dir = get_data_dir(app_info.get("service_name", "app"))
    return {
        "APP_INFO": app_info,
        "DATA_DIR": data_dir,
        "DB_PATH": get_db_path(data_dir),
        "ICONS_DIR": ICONS_DIR,
        "APP_ICON_PATH": os.path.join(ICONS_DIR, "app.png"),
        "UI_DIR": UI_DIR
    }
