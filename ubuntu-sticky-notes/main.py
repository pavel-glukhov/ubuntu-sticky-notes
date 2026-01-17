import sys
import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk
from notes_db import NotesDB
from main_window import MainWindow
from config import get_app_paths


class StickyApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.ubuntu.stickynotes")
        self.db = NotesDB()

    def load_css(self):
        paths = get_app_paths()
        css_path = os.path.join(paths["DATA_DIR"], "..", "resources", "style.css")

        if not os.path.exists(css_path):
            css_path = os.path.join(os.path.dirname(__file__), "resources", "style.css")

        css_provider = Gtk.CssProvider()
        try:
            css_provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            print(f"CSS успешно загружен из: {css_path}")
        except Exception as e:
            print(f"Предупреждение: CSS не найден или поврежден ({e}). Используются стандартные стили.")

    def do_activate(self):
        self.load_css()

        self.win = MainWindow(self.db, application=self)
        self.win.present()


if __name__ == "__main__":
    app = StickyApp()
    sys.exit(app.run(sys.argv))