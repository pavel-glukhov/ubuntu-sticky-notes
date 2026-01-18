import os
import json

CONF_DIR = os.path.expanduser("~/.config/ubuntu-sticky-notes")
CONF_PATH = os.path.join(CONF_DIR, "config.json")  # Лучше переименовать в .json


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
        # Создаем папку, если нет
        if not os.path.exists(CONF_DIR):
            os.makedirs(CONF_DIR, exist_ok=True)

        defaults = cls.get_defaults()

        # Если файла нет, создаем дефолтный
        if not os.path.exists(CONF_PATH):
            cls.save(defaults)
            return defaults

        try:
            with open(CONF_PATH, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)

            # Объединяем загруженное с дефолтным (чтобы новые ключи появились в старом конфиге)
            # Это называется "Soft merge"
            config = defaults.copy()
            config.update(loaded_config)

            # Дополнительная защита: убедимся, что formatting это словарь
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
                # indent=4 делает файл читаемым человеком
                json.dump(config_dict, f, ensure_ascii=False, indent=4)
            print(f"DEBUG: Config saved to {CONF_PATH}")
        except Exception as e:
            print(f"ERROR: Could not save config: {e}")