"""Deprecated PyQt entry (kept for compatibility).

The project migrated to GTK/libadwaita. Importing this module is no longer supported
and will raise a clear error guiding users to install GTK GI bindings and run
`main.py` which launches the GTK UI.
"""

import sys


def main():
    raise RuntimeError(
        "PyQt UI has been removed. Use the GTK UI via main.py.\n"
        "If running the app fails due to missing GI, install:\n"
        "  sudo apt update\n"
        "  sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1\n"
    )


if __name__ == "__main__":
    main()
