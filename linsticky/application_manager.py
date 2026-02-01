"""
Core Application Logic and UI Management.

This module acts as the central controller for the application, responsible for:
- Initializing and managing the main application window (MainWindow).
- Applying user-defined settings like UI scaling and custom CSS.
- Launching and managing the separate tray icon process for compatibility.
- Handling inter-process communication (IPC) from the tray icon.
- Orchestrating application-wide actions like 'Show All' or 'About'.
"""
import os
import sys
import threading
import subprocess
from datetime import datetime
import builtins

from gi.repository import Gtk, Adw, Gdk, GLib

from config.config import get_app_paths, load_app_info
from views.main_view.main_view import MainWindow

_ = builtins._

class ApplicationManager:
    """
    Manages core application logic, UI setup, and inter-process communication.
    
    This class decouples the main Adw.Application instance from the direct
    management of windows and processes, improving modularity.
    """
    def __init__(self, app_instance: Adw.Application, db_instance, config_instance):
        """
        Initializes the ApplicationManager.

        Args:
            app_instance: The main Adw.Application instance.
            db_instance: The NotesDB database controller.
            config_instance: The application's configuration dictionary.
        """
        self.app = app_instance
        self.db = db_instance
        self.config = config_instance
        self.main_window = None
        self.tray_process = None

    def setup_ui_settings(self):
        """Applies UI scaling, loads custom CSS, and sets up the icon theme."""
        # Apply UI scaling based on configuration.
        try:
            raw_scale = self.config.get("ui_scale", 1.0)
            scale = float(str(raw_scale)[:4])
            if not (0.5 <= scale <= 2.0):
                scale = 1.0
        except (ValueError, TypeError):
            scale = 1.0
        self._apply_ui_scale(scale)
        
        # Load the main stylesheet.
        self._load_css()

        # Add the application's icon directory to the default icon theme.
        display = Gdk.Display.get_default()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "resources", "icons")
        if os.path.exists(icons_dir):
            icon_theme = Gtk.IconTheme.get_for_display(display)
            icon_theme.add_search_path(icons_dir)
            # Use the full application ID for the icon name to avoid conflicts
            # and ensure consistency with the .desktop file.
            Gtk.Window.set_default_icon_name("io.linsticky.app")

    def _apply_ui_scale(self, scale: float):
        """
        Applies UI scaling by setting a custom CSS provider.
        Note: Modifying 'gtk-xft-dpi' is less reliable in modern GTK4/Wayland.
        Using a CSS provider for scaling is more consistent.

        Args:
            scale: The UI scaling factor (e.g., 1.0 for 100%, 1.5 for 150%).
        """
        custom_css = f"""
        .sticky-window {{
            font-size: {10 * scale}pt;
        }}
        .sticky-text-edit {{
            font-size: {int(12 * scale)}pt;
        }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(custom_css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        print(f"SYSTEM: UI Scale applied: {scale}")

    def _load_css(self):
        """Loads the main stylesheet from the resources directory."""
        paths = get_app_paths(user_config=self.config)
        css_path = paths.get("STYLE_CSS")
        if css_path and os.path.exists(css_path):
            provider = Gtk.CssProvider()
            try:
                provider.load_from_path(css_path)
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e:
                print(f"ERROR: Failed to load custom CSS from {css_path}: {e}")

    def setup_main_window(self):
        """Initializes and presents the main application window."""
        if not self.main_window:
            self.main_window = MainWindow(self.db, application=self.app)
            self.main_window.connect("close-request", self.on_main_window_close_request)
        self.main_window.present()

    def on_main_window_close_request(self, window: Gtk.Window) -> bool:
        """
        Handles the close request for the main window by hiding it,
        allowing the application to continue running in the background via the tray icon.

        Returns:
            True to prevent the default action (window destruction).
        """
        window.set_visible(False)
        return True

    def start_tray_subprocess(self):
        """
        Starts the GTK3-based tray icon in a separate process.
        
        Compatibility Note:
        This is a crucial workaround for compatibility between GTK4 (main app) and
        the Ayatana AppIndicator library (tray icon), which often relies on GTK3.
        Running the tray in a separate process prevents library version conflicts
        within the same process, a common issue in both DEB and Snap environments.
        """
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray.py")
        env = os.environ.copy()
        
        # Pass the current language to the tray process for localized tooltips.
        env['STICKY_NOTES_LANG'] = self.config.get("language", "en")
        
        # Unset GDK_BACKEND for the tray process to let it choose its own,
        # avoiding potential conflicts if the main app forced a specific backend.
        if "GDK_BACKEND" in env:
            del env["GDK_BACKEND"]

        # FIX FOR SNAP: Force default theme to avoid "colors.css" warning in logs.
        # This prevents GTK3 from trying to load user themes that don't exist in the snap sandbox.
        if "SNAP" in os.environ:
            env["GTK_THEME"] = "Adwaita"

        self.tray_process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

        # Monitor tray process output for commands and errors in separate threads.
        threading.Thread(target=self._monitor_tray_output, args=(self.tray_process.stdout, "TRAY"), daemon=True).start()
        threading.Thread(target=self._monitor_tray_output, args=(self.tray_process.stderr, "TRAY_ERROR"), daemon=True).start()

    def _monitor_tray_output(self, pipe, prefix: str):
        """
        Monitors stdout/stderr from the tray process for IPC commands or errors.

        Args:
            pipe: The process pipe (stdout or stderr) to read from.
            prefix: A logging prefix ("TRAY" or "TRAY_ERROR").
        """
        if not pipe:
            return
        try:
            for line in iter(pipe.readline, ''):
                cmd = line.strip()
                if not cmd: continue

                if prefix == "TRAY_ERROR":
                    print(f"{prefix}: {cmd}")
                    continue

                # IPC commands are simple strings printed to stdout by the tray process.
                if cmd == "quit":
                    GLib.idle_add(self.app.quit_app)
                elif cmd == "show_main":
                    GLib.idle_add(self.show_main_window)
                elif cmd == "open_all":
                    GLib.idle_add(self.open_all_stickers)
                elif cmd == "about":
                    GLib.idle_add(self.show_about_dialog)
        except Exception as e:
            print(f"DEBUG: Tray monitor thread terminated unexpectedly: {e}")

    def show_main_window(self):
        """Makes the main application window visible and brings it to the foreground."""
        if self.main_window:
            self.main_window.set_visible(True)
            self.main_window.present()

    def open_all_stickers(self):
        """Opens all non-archived sticky notes from the database."""
        notes = self.db.all_notes(full=False)
        for note in notes:
            if self.main_window:
                self.main_window.open_note(note['id'])

    def restore_notes(self):
        """Restores sticky notes that were marked as 'open' in the previous session."""
        open_note_ids = self.db.get_open_notes()
        for note_id in open_note_ids:
            if self.main_window:
                self.main_window.open_note(note_id)

    def show_about_dialog(self):
        """Displays the application's 'About' dialog window."""
        if not self.main_window: return

        app_info = load_app_info()
        author = app_info.get("author", "Unknown")
        email = app_info.get("email")
        developers = [f"{author} <{email}>"] if email else [author]
        # Create a custom content area for the license info
        content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Add license info as a label instead of using license_type
        license_label = Gtk.Label(label="License: MIT")
        license_label.add_css_class("caption")
        content_area.append(license_label)

        dialog = Adw.AboutWindow(
            transient_for=self.main_window if self.main_window.get_visible() else None,
            application_name=app_info.get("app_name"),
            version=app_info.get("version"),
            developer_name=author,
            website=app_info.get("website"),
            comments=f'{app_info.get("description")}\n\n{app_info.get("license")}',
            application_icon="app",
            developers=developers,
        )
        dialog.present()

    def quit_app_manager(self):
        """
        Safely terminates the tray process and closes all open application windows
        before the application exits.
        """
        if self.tray_process:
            self.tray_process.terminate()
        
        if self.main_window:
            # Close all individual sticky note windows first.
            for note_id in list(self.main_window.stickies.keys()):
                win = self.main_window.stickies.get(note_id)
                if win: 
                    win.close()
            # Finally, destroy the main window.
            self.main_window.destroy()
