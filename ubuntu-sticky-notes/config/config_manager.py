import os

CONF_DIR = os.path.expanduser("~/.config/ubuntu-sticky-notes")
CONF_PATH = os.path.join(CONF_DIR, "usn.conf")


class ConfigManager:
    @staticmethod
    def get_defaults():
        return {
            "backend": "wayland",
            "db_path": os.path.expanduser("~/.local/share/ubuntu-sticky-notes/notes.db")
        }

    @classmethod
    def load(cls):
        """Загружает конфиг или создает его с дефолтными значениями"""

        if not os.path.exists(CONF_DIR):
            os.makedirs(CONF_DIR, exist_ok=True)

        config = cls.get_defaults()

        if not os.path.exists(CONF_PATH):
            cls.save(config)
            return config

        try:
            with open(CONF_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        k, v = line.split("=", 1)
                        config[k] = v
        except Exception as e:
            print(f"Error loading config: {e}")

        return config

    @classmethod
    def save(cls, config):
        """Сохраняет переданный словарь в файл usn.conf"""
        try:
            if not os.path.exists(CONF_DIR):
                os.makedirs(CONF_DIR, exist_ok=True)

            with open(CONF_PATH, "w") as f:
                for k, v in config.items():
                    f.write(f"{k}={v}\n")
            print(f"Config saved to {CONF_PATH}")
        except Exception as e:
            print(f"Error saving config: {e}")