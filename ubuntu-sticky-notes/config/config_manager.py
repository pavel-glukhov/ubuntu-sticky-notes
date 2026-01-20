#!/usr/bin/env python3
"""Configuration Manager Module for Ubuntu Sticky Notes

This module handles persistent user configuration storage and retrieval using
JSON files. It follows the XDG Base Directory specification by storing
configuration in ~/.config/ubuntu-sticky-notes/config.json.

Configuration Structure:
    {
        "backend": "wayland" | "x11",
        "db_path": "path/to/database.db",
        "ui_scale": 0.5 - 3.0,
        "formatting": {
            "bold": bool,
            "italic": bool,
            "underline": bool,
            "strikethrough": bool,
            "list": bool,
            "text_color": bool,
            "font_size": bool
        }
    }

Examples:
    >>> from config.config_manager import ConfigManager
    >>> config = ConfigManager.load()
    >>> print(config['backend'])
    wayland
    >>> config['ui_scale'] = 1.25
    >>> ConfigManager.save(config)

See Also:
    config.py: For static path constants and metadata loading
"""

import os
import json

# Configuration directory following XDG Base Directory specification
CONF_DIR = os.path.expanduser("~/.config/ubuntu-sticky-notes")
# Full path to the JSON configuration file
CONF_PATH = os.path.join(CONF_DIR, "config.json")


class ConfigManager:
    """Static configuration manager for persistent user settings.
    
    This class provides static methods for loading and saving user configuration
    to a JSON file. It handles default values, config directory creation, and
    error recovery in case of corrupted configuration files.
    
    All methods are static as this class serves as a namespace for configuration
    operations rather than maintaining instance state.
    
    Class Methods:
        get_defaults(): Returns default configuration dictionary
        load(): Loads configuration from file or creates with defaults
        save(config_dict): Saves configuration dictionary to file
    
    Configuration File Location:
        ~/.config/ubuntu-sticky-notes/config.json
    
    Examples:
        >>> config = ConfigManager.load()
        >>> config['backend'] = 'x11'
        >>> ConfigManager.save(config)
    
    Note:
        The class automatically creates the config directory if it doesn't exist.
        Corrupted JSON files are logged and replaced with defaults.
    """
    
    @staticmethod
    def get_defaults():
        """Get default configuration settings.
        
        Returns a dictionary containing all default application settings.
        These values are used when no configuration file exists or when the
        configuration file is corrupted.
        
        Returns:
            Dictionary with default configuration containing:
                - backend: Display server preference ('wayland' or 'x11')
                - db_path: Default database location
                - ui_scale: Interface scaling factor (1.0 = 100%)
                - formatting: Dictionary of toolbar button visibility settings
        
        Examples:
            >>> defaults = ConfigManager.get_defaults()
            >>> print(defaults['backend'])
            wayland
            >>> print(defaults['ui_scale'])
            1.0
        
        Note:
            All formatting options default to True (all buttons visible).
        """
        return {
            "backend": "wayland",
            "db_path": os.path.expanduser("~/.local/share/ubuntu-sticky-notes/notes.db"),
            "ui_scale": 1.0,
            "formatting": {
                "bold": True,
                "italic": True,
                "underline": True,
                "strikethrough": True,
                "list": True,
                "text_color": True,
                "font_size": True
            }
        }

    @classmethod
    def load(cls):
        """Load user configuration from file or create with defaults.
        
        Attempts to load the configuration from the JSON file. If the file
        doesn't exist, creates it with default values. If the file is corrupted
        or unreadable, logs the error and returns defaults.
        
        The method also validates the 'formatting' section to ensure it's a
        dictionary, resetting it to defaults if it's corrupted.
        
        Returns:
            Dictionary containing user configuration merged with defaults.
            User settings override defaults where present.
        
        Raises:
            No exceptions are raised. All errors are caught and logged.
        
        Side Effects:
            - Creates config directory if it doesn't exist
            - Creates config.json with defaults if missing
            - Prints error messages to stdout on load failures
        
        Examples:
            >>> config = ConfigManager.load()
            >>> print(config.get('backend', 'wayland'))
            wayland
        
        Note:
            This method ensures that the returned config always has all
            required keys by merging user settings with defaults.
        """
        # Ensure configuration directory exists
        if not os.path.exists(CONF_DIR):
            os.makedirs(CONF_DIR, exist_ok=True)

        defaults = cls.get_defaults()

        # If config file doesn't exist, create it with defaults
        if not os.path.exists(CONF_PATH):
            cls.save(defaults)
            return defaults

        # Attempt to load existing configuration
        try:
            with open(CONF_PATH, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            
            # Merge loaded config with defaults (user settings take precedence)
            config = defaults.copy()
            config.update(loaded_config)

            # Validate formatting section structure
            if not isinstance(config.get("formatting"), dict):
                config["formatting"] = defaults["formatting"]

            return config

        except (json.JSONDecodeError, OSError) as e:
            # If file is corrupted or unreadable, log error and use defaults
            print(f"Error loading config (resetting to defaults): {e}")
            return defaults

    @staticmethod
    def save(config_dict):
        """Save configuration dictionary to JSON file.
        
        Writes the provided configuration dictionary to the config.json file
        with pretty-printing (4-space indentation) and UTF-8 encoding.
        
        Args:
            config_dict: Dictionary containing configuration settings to save.
                Should match the structure returned by get_defaults().
        
        Side Effects:
            - Writes to ~/.config/ubuntu-sticky-notes/config.json
            - Prints success message to stdout
            - Prints error message to stdout on failure
        
        Raises:
            No exceptions are raised. All errors are caught and logged.
        
        Examples:
            >>> config = ConfigManager.load()
            >>> config['backend'] = 'x11'
            >>> config['ui_scale'] = 1.5
            >>> ConfigManager.save(config)
            DEBUG: Config saved to /home/user/.config/ubuntu-sticky-notes/config.json
        
        Note:
            The ensure_ascii=False parameter allows non-ASCII characters in
            the JSON file (useful for internationalization).
        """
        try:
            # Write configuration with pretty formatting
            with open(CONF_PATH, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=4)
            print(f"DEBUG: Config saved to {CONF_PATH}")
        except Exception as e:
            # Log any errors during save operation
            print(f"ERROR: Could not save config: {e}")