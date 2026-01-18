import sys
import os

# СТРОГО ПЕРВЫМ ДЕЛОМ: Настройка бэкенда
# Импортируем ConfigManager локально, чтобы не задеть библиотеки GTK раньше времени
try:
    from config_manager import ConfigManager

    config = ConfigManager.load()
    if config.get("backend") == "x11":
        os.environ["GDK_BACKEND"] = "x11"
        print("SYSTEM: Environment set to X11")
    else:
        os.environ["GDK_BACKEND"] = "wayland"
        print("SYSTEM: Environment set to Wayland")
except Exception as e:
    print(f"Config pre-init error: {e}")

import threading
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, GLib
from notes_db import NotesDB
from main_window import MainWindow
from config import get_app_paths


class StickyApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.ubuntu.stickynotes")

        # Загружаем настройки повторно для использования внутри приложения
        self.config = ConfigManager.load()
        db_path = self.config.get("db_path")

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = NotesDB(path=db_path)

        self.win = None
        self.tray_process = None

    def load_css(self):
        paths = get_app_paths()
        possible_paths = [
            os.path.join(paths["DATA_DIR"], "..", "resources", "style.css"),
            os.path.join(os.path.dirname(__file__), "resources", "style.css"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "style.css")
        ]

        css_path = None
        for p in possible_paths:
            if os.path.exists(p):
                css_path = os.path.abspath(p)
                break

        if css_path:
            css_provider = Gtk.CssProvider()
            try:
                css_provider.load_from_path(css_path)
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                print(f"CSS loaded from: {css_path}")
            except Exception as e:
                print(f"CSS Error: {e}")

    def do_activate(self):
        display = Gdk.Display.get_default()
        print(f"ACTUAL RUNNING BACKEND: {display.__class__.__name__}")

        self.load_css()

        if not self.win:
            self.win = MainWindow(self.db, application=self)
            self.win.connect("close-request", self.on_window_close_request)
            self.start_tray_subprocess()

        self.win.present()

    def on_window_close_request(self, window):
        window.set_visible(False)
        return True

    def start_tray_subprocess(self):
        script_path = os.path.join(os.path.dirname(__file__), "tray.py")
        env = os.environ.copy()

        self.tray_process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env
        )

        self.monitor_thread = threading.Thread(target=self.monitor_tray_output, daemon=True)
        self.monitor_thread.start()

    def monitor_tray_output(self):
        if not self.tray_process or not self.tray_process.stdout:
            return

        try:
            for line in iter(self.tray_process.stdout.readline, ''):
                cmd = line.strip()
                if not cmd: continue

                if cmd == "quit":
                    GLib.idle_add(self.quit_app)
                elif cmd == "show_main":
                    GLib.idle_add(self.show_main_window)
                elif cmd == "open_all":
                    GLib.idle_add(self.open_all_stickers)
                elif cmd == "about":
                    GLib.idle_add(self.show_about_dialog)
        except Exception as e:
            print(f"Tray monitor stopped: {e}")

    def show_main_window(self):
        if self.win:
            self.win.set_visible(True)
            self.win.present()

    def open_all_stickers(self):
        notes = self.db.all_notes(full=False)
        for note in notes:
            self.win.open_note(note['id'])

    def show_about_dialog(self):
        if not self.win: return
        dialog = Adw.AboutWindow(
            transient_for=self.win if self.win.get_visible() else None,
            application_name="Sticky Notes",
            developer_name="Me",
            version="1.0",
            copyright="© 2024",
            license_type=Gtk.License.GPL_3_0
        )
        dialog.present()

    def quit_app(self):
        if self.tray_process:
            self.tray_process.terminate()

        if self.win:
            for note_id in list(self.win.stickies.keys()):
                win = self.win.stickies.get(note_id)
                if win: win.close()
            self.win.destroy()

        self.quit()


if __name__ == "__main__":
    app = StickyApp()
    sys.exit(app.run(sys.argv))