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
        if not os.path.exists(CONF_DIR):
            os.makedirs(CONF_DIR, exist_ok=True)

        defaults = cls.get_defaults()

        if not os.path.exists(CONF_PATH):
            cls.save(defaults)
            return defaults

        try:
            with open(CONF_PATH, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            config = defaults.copy()
            config.update(loaded_config)

            if not isinstance(config.get("formatting"), dict):
                config["formatting"] = defaults["formatting"]

            return config

        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading config (resetting to defaults): {e}")
            return defaults

    @staticmethod
    def save(config_dict):
        try:
            with open(CONF_PATH, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=4)
            print(f"DEBUG: Config saved to {CONF_PATH}")
        except Exception as e:
            print(f"ERROR: Could not save config: {e}")