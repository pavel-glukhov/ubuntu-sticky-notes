import sys
import os
import signal
import gi
import gettext
import builtins

# --- Translation Setup ---
APP_ID_GETTEXT = 'ubuntu.sticky.notes'
current_dir = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(current_dir, 'locale')

try:
    lang_code = os.environ.get('STICKY_NOTES_LANG', 'en')
    translation = gettext.translation(APP_ID_GETTEXT, localedir=LOCALE_DIR, languages=[lang_code], fallback=True)
    builtins._ = translation.gettext
except FileNotFoundError:
    builtins._ = lambda s: s
except Exception as e:
    print(f"Tray translation setup failed: {e}", file=sys.stderr)
    builtins._ = lambda s: s

try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator
    except (ValueError, ImportError) as e:
        print(f"CRITICAL: AyatanaAppIndicator/AppIndicator not found: {e}", file=sys.stderr)
        sys.exit(1)

from gi.repository import Gtk as Gtk3


APP_ID = "stickynotes-tray"


def get_custom_icon():
    """
    Determines the path and name of the custom application icon.
    Searches in common locations relative to the script.
    Returns:
        tuple: (icon_dir, icon_name) if found, otherwise (None, None).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, "resources", "icons"),
        os.path.join(base_dir, "..", "resources", "icons")
    ]
    for icon_dir in possible_paths:
        icon_dir = os.path.abspath(icon_dir)
        full_path = os.path.join(icon_dir, "app.png")
        if os.path.exists(full_path):
            return icon_dir, "app"
    return None, None


def main():
    """Main function to set up and run the tray application."""
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    def on_show_main(_):
        """Callback for 'Open Main Window' menu item."""
        sys.stdout.write("show_main\n")
        sys.stdout.flush()

    def on_open_all(_):
        """Callback for 'Open All Notes' menu item."""
        sys.stdout.write("open_all\n")
        sys.stdout.flush()

    def on_about(_):
        """Callback for 'About' menu item."""
        sys.stdout.write("about\n")
        sys.stdout.flush()

    def on_quit(_):
        """Callback for 'Quit' menu item. Exits the tray application."""
        sys.stdout.write("quit\n")
        sys.stdout.flush()
        Gtk3.main_quit()

    # --- Menu (Gtk.Menu) ---
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

    # --- Icon Setup ---
    icon_dir, icon_name = get_custom_icon()

    if icon_dir and icon_name:
        indicator = AppIndicator.Indicator.new(
            APP_ID,
            icon_name,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_icon_theme_path(icon_dir)
    else:
        # Fallback to a generic icon if custom icon is not found
        indicator = AppIndicator.Indicator.new(
            APP_ID,
            "accessories-text-editor",
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )

    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu)

    Gtk3.main()


if __name__ == "__main__":
    main()