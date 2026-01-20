#!/usr/bin/env python3
"""System tray icon module for Ubuntu Sticky Notes.

Implements a standalone GTK3-based system tray icon that runs as a separate
process from the main GTK4 application. Communicates with the main process
via stdout commands. The separation is necessary because GTK3 and GTK4 cannot
coexist in the same process.

This module uses AyatanaAppIndicator3 or AppIndicator3 for cross-desktop
environment compatibility.
"""

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
    """Locate and return the path to the custom application icon.
    
    Searches for app.png in multiple locations relative to the script
    directory, handling both development and installed environments.
    
    Returns:
        tuple: (icon_dir, icon_name) if found, (None, None) otherwise.
            icon_dir is the absolute path to the icons directory.
            icon_name is 'app' (without extension).
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
    """Initialize and run the system tray indicator.
    
    Sets up signal handlers, creates the menu with callbacks, locates the
    application icon, initializes the AppIndicator, and starts the GTK3
    main event loop. Communicates with the parent process by printing
    command strings to stdout.
    
    Commands sent to stdout:
        show_main: Show the main window
        open_all: Open all sticky notes
        about: Display about dialog
        quit: Terminate the application
    
    Note:
        This function blocks until Gtk3.main_quit() is called.
    """
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    def on_show_main(_):
        """Send 'show_main' command to show the main window."""
        print("show_main", flush=True)

    def on_open_all(_):
        """Send 'open_all' command to open all sticky notes."""
        print("open_all", flush=True)

    def on_about(_):
        """Send 'about' command to display the about dialog."""
        print("about", flush=True)

    def on_quit(_):
        """Send 'quit' command and terminate the tray subprocess."""
        print("quit", flush=True)
        Gtk3.main_quit()

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