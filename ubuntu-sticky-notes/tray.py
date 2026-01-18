import sys
import os
import signal
import gi


try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
except ValueError:
    sys.exit(1)

from gi.repository import Gtk as Gtk3, AyatanaAppIndicator3 as AppIndicator


def get_icon_paths():
    """
    Вычисляет путь к иконке.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(current_dir, "..", "resources", "icons")
    icons_dir = os.path.abspath(icons_dir)

    if not os.path.exists(icons_dir):
        icons_dir = os.path.join(current_dir, "resources", "icons")

    icon_filename = "app.png"
    full_path = os.path.join(icons_dir, icon_filename)

    if os.path.exists(full_path):
        return icons_dir, "app"
    else:
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
    icon_dir, icon_name = get_icon_paths()

    if icon_dir and icon_name:
        indicator = AppIndicator.Indicator.new(
            "stickynotes-tray",
            icon_name,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_icon_theme_path(icon_dir)
    else:
        indicator = AppIndicator.Indicator.new(
            "stickynotes-tray",
            "text-editor",  # Fallback icon
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )

    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu)

    Gtk3.main()


if __name__ == "__main__":
    main()