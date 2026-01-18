import sys
import os
import signal
import gi

try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except ValueError:
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator
    except ValueError:
        print("Tray indicator library not found.")
        sys.exit(1)

from gi.repository import Gtk as Gtk3

APP_ID = "stickynotes-tray"


def get_custom_icon():
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
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # --- Callbacks ---
    def on_show_main(_):
        print("show_main", flush=True)

    def on_open_all(_):
        print("open_all", flush=True)

    def on_about(_):
        print("about", flush=True)

    def on_quit(_):
        print("quit", flush=True)
        Gtk3.main_quit()

    # --- Menu ---
    menu = Gtk3.Menu()

    item_main = Gtk3.MenuItem(label="Open Main Window")
    item_main.connect("activate", on_show_main)
    menu.append(item_main)

    item_all = Gtk3.MenuItem(label="Open All Notes")
    item_all.connect("activate", on_open_all)
    menu.append(item_all)

    menu.append(Gtk3.SeparatorMenuItem())

    item_about = Gtk3.MenuItem(label="About")
    item_about.connect("activate", on_about)
    menu.append(item_about)

    item_quit = Gtk3.MenuItem(label="Quit")
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
        print("Warning: app.png not found, using system icon.")
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