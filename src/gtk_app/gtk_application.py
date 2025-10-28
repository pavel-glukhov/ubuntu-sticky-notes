"""Libadwaita (GTK4) application entry and wiring for Ubuntu Sticky Notes."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

from core.config import get_app_paths
from gtk_app.windows.main_window import MainWindow


class StickyNotesApp(Adw.Application):
	def __init__(self):
		super().__init__(application_id="com.github.ubuntu_sticky_notes",
						 flags=Gio.ApplicationFlags.FLAGS_NONE)
		Adw.init()
		self.paths = get_app_paths()

	def do_activate(self):
		# Single main window instance
		win = self.props.active_window
		if not win:
			win = MainWindow(application=self)
		
		win.present()


def main():
	app = StickyNotesApp()
	return app.run()

