import os
import json

CONF_DIR = os.path.expanduser("~/.config/ubuntu-sticky-notes")
CONF_PATH = os.path.join(CONF_DIR, "config.json")


class ConfigManager:
    @staticmethod
    def get_defaults():
        return {
            "backend": "wayland",
            "db_path": os.path.expanduser("~/.local/share/ubuntu-sticky-notes/notes.db"),
            "ui_scale": 1.0,
            "language": "en",
            # Define default palette directly here to avoid circular import
            "palette": ['#FFF59D', '#F8BBD0', '#C8E6C9', '#B3E5FC'],
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
        defaults = cls.get_defaults()
        
        if not os.path.exists(CONF_PATH):
            try:
                os.makedirs(CONF_DIR, exist_ok=True)
                cls.save(defaults)
            except OSError as e:
                print(f"ERROR: Could not create config directory or file: {e}")
            return defaults

        try:
            with open(CONF_PATH, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            
            config = defaults.copy()
            # Deep update for formatting dict
            if 'formatting' in loaded_config and isinstance(loaded_config['formatting'], dict):
                config['formatting'].update(loaded_config['formatting'])
                loaded_config['formatting'] = config['formatting']
            
            config.update(loaded_config)

            if not isinstance(config.get("formatting"), dict):
                config["formatting"] = defaults["formatting"]
            
            # Ensure palette exists and is a list
            if "palette" not in config or not isinstance(config["palette"], list):
                config["palette"] = defaults["palette"]

            return config

        except (json.JSONDecodeError, OSError) as e:
            print(f"WARNING: Error loading config file '{CONF_PATH}'. Resetting to defaults. Error: {e}")
            return defaults

    @staticmethod
    def save(config_dict):
        try:
            os.makedirs(CONF_DIR, exist_ok=True)
            with open(CONF_PATH, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=4)
        except OSError as e:
            print(f"ERROR: Could not save config to '{CONF_PATH}': {e}")
