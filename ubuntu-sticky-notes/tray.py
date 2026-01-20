#!/usr/bin/env python3
"""System Tray Icon Module for Ubuntu Sticky Notes

This module implements a standalone GTK3-based system tray icon that runs as a
separate process from the main GTK4 application. It provides a system tray menu
for quick access to application features and communicates with the main process
via stdout commands.

The separation is necessary because GTK3 and GTK4 cannot coexist in the same
process due to library conflicts. This module uses AyatanaAppIndicator3 (or
fallback to AppIndicator3) for cross-desktop environment compatibility.

Author: Pavel Glukhov
Version: 2.0.0-beta1
License: MIT

Communication Protocol:
    Commands are sent to the main process via stdout:
    - 'show_main': Show the main window
    - 'open_all': Open all sticky notes
    - 'about': Show about dialog
    - 'quit': Terminate the application

Examples:
    Run directly (not recommended, should be spawned by main.py):
        $ python3 tray.py
    
    Spawn from main process:
        subprocess.Popen([sys.executable, 'tray.py'], stdout=PIPE)
"""

import sys
import os
import signal
import gi

# =============================================================================
# GTK3 and AppIndicator Library Loading
# =============================================================================
# Try to load AyatanaAppIndicator3 first (modern, actively maintained)                                                                                                                                                                                                                                                                                                                                                                                                                                      
# Fall back to AppIndicator3 if not available (older systems)
# Exit with error if neither is available
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except ValueError:
    # Fallback to legacy AppIndicator3
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator
    except ValueError:
        print("Tray indicator library not found.")
        sys.exit(1)

from gi.repository import Gtk as Gtk3

# Application identifier for the tray indicator
# This ID should be unique to avoid conflicts with other tray applications
APP_ID = "stickynotes-tray"


def get_custom_icon():
    """Locate and return the path to the custom application icon.
    
    Searches for the app.png icon file in multiple possible locations relative
    to the script directory. This function handles both installed and development
    environments by checking common resource paths.
    
    Search Locations:
        1. ./resources/icons/app.png (same directory)
        2. ../resources/icons/app.png (parent directory)
    
    Returns:
        tuple: A tuple containing:
            - icon_dir (str or None): Absolute path to the icons directory
            - icon_name (str or None): Icon name without extension ('app')
            
            Returns (None, None) if icon is not found.
    
    Examples:
        >>> icon_dir, icon_name = get_custom_icon()
        >>> if icon_dir:
        ...     indicator.set_icon_theme_path(icon_dir)
    
    Note:
        The function returns the icon name without the .png extension because
        GTK icon themes expect icon names, not full file paths.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Define possible icon directory locations
    # Covers both development and installed package structures
    possible_paths = [
        os.path.join(base_dir, "resources", "icons"),        # Development structure
        os.path.join(base_dir, "..", "resources", "icons")   # Installed package structure
    ]

    # Search each possible path for the icon file
    for icon_dir in possible_paths:
        # Convert to absolute path for consistency
        icon_dir = os.path.abspath(icon_dir)
        full_path = os.path.join(icon_dir, "app.png")

        # Return the first valid icon location found
        if os.path.exists(full_path):
            return icon_dir, "app"  # Return directory and icon name (without extension)

    # No icon found in any location
    return None, None


def main():
    """Initialize and run the system tray indicator.
    
    This is the main entry point for the tray subprocess. It performs the
    following operations:
    1. Sets up signal handlers for graceful termination
    2. Creates menu items with command callbacks
    3. Locates and loads the application icon
    4. Initializes the AppIndicator with menu and icon
    5. Starts the GTK3 main event loop
    
    The function communicates with the parent process by printing command
    strings to stdout. The parent process monitors stdout and executes
    the corresponding actions.
    
    Menu Structure:
        - Open Main Window (show_main)
        - Open All Notes (open_all)
        - Separator
        - About (about)
        - Quit (quit)
    
    Raises:
        SystemExit: If AppIndicator libraries are not available
    
    Note:
        This function blocks until Gtk3.main_quit() is called or the
        process receives a termination signal.
    
    See Also:
        main.py:monitor_tray_output() - Parent process command handler
    """
    # Allow Ctrl+C to terminate the tray process gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # =============================================================================
    # Menu Item Callbacks
    # =============================================================================
    # Each callback sends a command string to stdout, which is monitored by the
    # main process. The flush=True ensures immediate delivery.
    
    def on_show_main(_):
        """Handle 'Open Main Window' menu selection.
        
        Sends 'show_main' command to parent process to show and focus
        the main application window.
        
        Args:
            _ (Gtk.MenuItem): The menu item that triggered the callback (unused)
        """
        print("show_main", flush=True)

    def on_open_all(_):
        """Handle 'Open All Notes' menu selection.
        
        Sends 'open_all' command to parent process to open all sticky notes
        from the database.
        
        Args:
            _ (Gtk.MenuItem): The menu item that triggered the callback (unused)
        """
        print("open_all", flush=True)

    def on_about(_):
        """Handle 'About' menu selection.
        
        Sends 'about' command to parent process to display the about dialog
        with application information.
        
        Args:
            _ (Gtk.MenuItem): The menu item that triggered the callback (unused)
        """
        print("about", flush=True)

    def on_quit(_):
        """Handle 'Quit' menu selection.
        
        Sends 'quit' command to parent process and terminates the tray
        subprocess by calling Gtk3.main_quit().
        
        Args:
            _ (Gtk.MenuItem): The menu item that triggered the callback (unused)
        """
        print("quit", flush=True)
        Gtk3.main_quit()

    # =============================================================================
    # Tray Menu Construction
    # =============================================================================
    # Build the context menu that appears when the tray icon is clicked
    menu = Gtk3.Menu()

    # Create and connect menu items to their respective callbacks
    # Menu Item: Open Main Window
    item_main = Gtk3.MenuItem(label="Open Main Window")
    item_main.connect("activate", on_show_main)
    menu.append(item_main)

    # Menu Item: Open All Notes
    item_all = Gtk3.MenuItem(label="Open All Notes")
    item_all.connect("activate", on_open_all)
    menu.append(item_all)

    # Visual separator
    menu.append(Gtk3.SeparatorMenuItem())

    # Menu Item: About
    item_about = Gtk3.MenuItem(label="About")
    item_about.connect("activate", on_about)
    menu.append(item_about)

    # Menu Item: Quit
    item_quit = Gtk3.MenuItem(label="Quit")
    item_quit.connect("activate", on_quit)
    menu.append(item_quit)

    # Make all menu items visible
    menu.show_all()

    # =============================================================================
    # Indicator Initialization
    # =============================================================================
    # Attempt to load custom icon, fall back to system icon if not found
    icon_dir, icon_name = get_custom_icon()

    # Create indicator with custom icon if found
    if icon_dir and icon_name:
        indicator = AppIndicator.Indicator.new(
            APP_ID,
            icon_name,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        # Set the directory where GTK should look for the icon
        indicator.set_icon_theme_path(icon_dir)
    else:
        # Fallback to system icon if custom icon not found
        print("Warning: app.png not found, using system icon.")
        indicator = AppIndicator.Indicator.new(
            APP_ID,
            "accessories-text-editor",  # Standard GNOME text editor icon
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )

    # Make the indicator visible in the system tray
    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
    
    # Attach the menu to the indicator
    indicator.set_menu(menu)

    # Start the GTK3 main event loop (blocks until quit)
    Gtk3.main()


# =============================================================================
# Script Entry Point
# =============================================================================
if __name__ == "__main__":
    # Run the tray indicator when executed directly
    # Note: This should normally be spawned as a subprocess by main.py
    main()