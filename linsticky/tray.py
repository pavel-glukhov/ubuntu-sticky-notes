"""
Standalone GTK3 Tray Icon Process.

This script runs in a separate process to provide a system tray icon for the
main GTK4 application. It communicates with the main process via standard
input/output (IPC).

Compatibility Note:
This separation is a critical workaround for ensuring compatibility. The main
application uses GTK4 and Libadwaita for a modern UI, while the system tray
icon functionality often relies on libraries like AyatanaAppIndicator or
AppIndicator3, which are fundamentally tied to GTK3. Running them in the same
process would lead to library version conflicts and instability.

This approach is robust for both DEB and Snap packages.
- DEB: System dependencies for GTK3 and GTK4 can coexist.
- Snap: The `gnome` extension provides both GTK3 and GTK4 runtimes,
  allowing this multi-process architecture to work seamlessly.
"""
import sys
import os
import signal
import json
import gi
import gettext
import builtins

# --- Helper to load app info without external dependencies ---
def _load_local_app_info():
    """Loads service name from app_info.json relative to this script."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        info_path = os.path.join(base_dir, "app_info.json")
        with open(info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get('service_name', None)
    except Exception:
        return 'linsticky'

# --- Translation Setup ---
APP_ID_GETTEXT = _load_local_app_info()
current_dir = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(current_dir, 'locale')

try:
    lang_code = os.environ.get('STICKY_NOTES_LANG', 'en')
    translation = gettext.translation(APP_ID_GETTEXT, localedir=LOCALE_DIR, languages=[lang_code], fallback=True)
    builtins._ = translation.gettext
except Exception as e:
    print(f"Tray translation setup failed: {e}", file=sys.stderr)
    builtins._ = lambda s: s

# --- Indicator Library Import ---
# Try to import AyatanaAppIndicator first, as it's the modern standard.
# Fallback to the older AppIndicator3 for compatibility with older systems.
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator
    except (ValueError, ImportError) as e:
        print(f"CRITICAL: No suitable AppIndicator library found: {e}", file=sys.stderr)
        sys.exit(1)

from gi.repository import Gtk as Gtk3

APP_ID = f"{APP_ID_GETTEXT}-tray"

def get_custom_icon_path() -> tuple[str | None, str | None]:
    """
    Locates the application's icon directory.
    
    Returns:
        A tuple containing the icon directory path and the icon name, or (None, None).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_dir = os.path.join(base_dir, "resources", "icons")
    if os.path.exists(os.path.join(icon_dir, "app.png")):
        return os.path.abspath(icon_dir), "app"
    return None, None

def main():
    """Sets up and runs the GTK3 tray icon application."""
    # Ensure Ctrl+C in the terminal can kill this process.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    def send_command(command: str):
        """Sends a command to the main application process via stdout."""
        sys.stdout.write(f"{command}\n")
        sys.stdout.flush()

    # --- Menu Item Callbacks ---
    def on_show_main(_):
        send_command("show_main")

    def on_open_all(_):
        send_command("open_all")

    def on_about(_):
        send_command("about")

    def on_quit(_):
        send_command("quit")
        Gtk3.main_quit()

    # --- Menu Construction ---
    menu = Gtk3.Menu()
    
    item_main = Gtk3.MenuItem(label=_("Open Main Window"))
    item_main.connect("activate", on_show_main)
    menu.append(item_main)

    item_all = Gtk3.MenuItem(label=_("Open All Notes"))
    item_all.connect("activate", on_open_all)
    menu.append(item_all)

    menu.append(Gtk3.SeparatorMenuItem())

    item_about = Gtk3.MenuItem(label=_("About"))
    item_about.connect("activate", on_about)
    menu.append(item_about)

    item_quit = Gtk3.MenuItem(label=_("Quit"))
    item_quit.connect("activate", on_quit)
    menu.append(item_quit)

    menu.show_all()

    # --- Indicator Setup ---
    icon_dir, icon_name = get_custom_icon_path()
    indicator = AppIndicator.Indicator.new(
        APP_ID,
        icon_name or "accessories-text-editor",  # Fallback icon
        AppIndicator.IndicatorCategory.APPLICATION_STATUS
    )
    if icon_dir:
        indicator.set_icon_theme_path(icon_dir)

    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu)

    Gtk3.main()

if __name__ == "__main__":
    main()
