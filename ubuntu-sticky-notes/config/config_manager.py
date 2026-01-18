import os

CONF_DIR = os.path.expanduser("~/.config/ubuntu-sticky-notes")
CONF_PATH = os.path.join(CONF_DIR, "usn.conf")

DEFAULT_CONFIG = {
    "backend": "wayland",
    "db_path": "",
    "ui_scale": 1.0,  # 1.0 = 100%, 1.25 = 125%
}

class ConfigManager:
    @staticmethod
    def get_defaults():
        return {
            "backend": "wayland",
            "db_path": os.path.expanduser("~/.local/share/ubuntu-sticky-notes/notes.db")
        }

    @classmethod
    def load(cls):
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

    @staticmethod
    def save(config_dict):
        lines = []
        for key, value in config_dict.items():
            lines.append(f"{key}={value}")

        try:
            with open(CONF_PATH, "w") as f:
                f.write("\n".join(lines))
        except Exception as e:
            print(f"ERROR: Could not save config: {e}")