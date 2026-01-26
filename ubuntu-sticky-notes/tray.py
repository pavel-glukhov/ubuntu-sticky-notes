import sys
import os
import signal
import gi

# --- Translation Setup ---
import gettext
import builtins

APP_ID_GETTEXT = 'ubuntu-sticky-notes'
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
# --- End Translation Setup ---

try:
    gi.require_version('Gtk', '3.0') # Glib indicator still uses Gtk3 for menu
    gi.require_version('AyatanaAppIndicatorGlib', '2.0')
    from gi.repository import AyatanaAppIndicatorGlib as AppIndicator
    from gi.repository import Gio, Gtk as Gtk3, GLib # Import Gio and Gtk3 for menu, GLib for mainloop
except (ValueError, ImportError) as e:
    print(f"CRITICAL: AyatanaAppIndicatorGlib not found: {e}", file=sys.stderr)
    sys.exit(1)

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
        # Gtk3.main_quit() # No longer needed with GLib.MainLoop
        GLib.MainLoop().quit() # Quit the GLib main loop

    # --- Menu ---
    # Create a Gio.Menu (model-based menu)
    menu = Gio.Menu.new()

    menu.append(_("Open Main Window"), "app.show_main")
    menu.append(_("Open All Notes"), "app.open_all")
    menu.append(_("About"), "app.about")
    menu.append(_("Quit"), "app.quit")

    # Create a Gtk.Application (even if it's a dummy one) to hold the actions
    # This is necessary for Gio.Menu actions to work
    app_actions = Gtk3.Application.new("org.ubuntu.StickyNotesTray", Gio.ApplicationFlags.FLAGS_NONE)
    
    # Add actions to the dummy application
    action_show_main = Gio.SimpleAction.new("show_main", None)
    action_show_main.connect("activate", on_show_main)
    app_actions.add_action(action_show_main)

    action_open_all = Gio.SimpleAction.new("open_all", None)
    action_open_all.connect("activate", on_open_all)
    app_actions.add_action(action_open_all)

    action_about = Gio.SimpleAction.new("about", None)
    action_about.connect("activate", on_about)
    app_actions.add_action(action_about)

    action_quit = Gio.SimpleAction.new("quit", None)
    action_quit.connect("activate", on_quit)
    app_actions.add_action(action_quit)

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
        print("Warning: app.png not found, using system icon.", file=sys.stderr)
        indicator = AppIndicator.Indicator.new(
            APP_ID,
            "accessories-text-editor",
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )

    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu) # Pass the Gio.Menu here

    # Run the GLib main loop
    main_loop = GLib.MainLoop()
    main_loop.run()


if __name__ == "__main__":
    main()