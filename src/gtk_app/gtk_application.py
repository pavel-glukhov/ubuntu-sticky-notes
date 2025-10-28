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
		self.tray = None

	def do_activate(self):
		# Single main window instance
		win = self.props.active_window
		if not win:
			win = MainWindow(application=self)
			# Initialize system tray after main window is created
			tray_initialized = False
			
			# Try StatusNotifierItem first (GTK4 compatible)
			try:
				from utils.status_notifier import init_status_notifier
				self.tray = init_status_notifier(self, win)
				if self.tray:
					tray_initialized = True
					print("✓ System tray initialized using StatusNotifierItem")
			except Exception as e:
				print(f"StatusNotifierItem not available: {e}")
			
			# If SNI failed, try AppIndicator (requires GTK3 bindings but may work)
			if not tray_initialized:
				try:
					from utils.system_tray import init_tray
					self.tray = init_tray(self, win)
					if self.tray:
						tray_initialized = True
						print("✓ System tray initialized using AppIndicator")
				except Exception as e:
					print(f"AppIndicator not available: {e}")
			
			if not tray_initialized:
				print("\n⚠ System tray not available on this system.")
				print("For GNOME Shell, install: sudo apt install gnome-shell-extension-appindicator")
				print("The application will work without system tray.\n")
		
		win.present()


def main():
	app = StickyNotesApp()
	return app.run()

