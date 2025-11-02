"""Libadwaita (GTK4) application entry and wiring for Ubuntu Sticky Notes."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

from core.config import get_app_paths
from gtk_app.windows.main_window import MainWindow
from data.database import NotesDB


class StickyNotesApp(Adw.Application):
	def __init__(self):
		super().__init__(application_id="com.github.ubuntu_sticky_notes",
						 flags=Gio.ApplicationFlags.FLAGS_NONE)
		Adw.init()
		self.paths = get_app_paths()
		self.main_window = None
		self.db = NotesDB()
		
		# Hold the application so it doesn't quit when main window closes
		self.hold()

	def do_activate(self):
		"""Show main window or restore it if already exists."""
		if self.main_window is None:
			self.main_window = MainWindow(application=self)
			# Connect to close request to hide instead of destroy
			self.main_window.connect("close-request", self._on_main_window_close)
		
		self.main_window.present()
	
	def _on_main_window_close(self, window):
		"""Handle main window close - hide if sticky notes are open, quit if none."""
		# Check if there are any open sticky notes
		from gtk_app.windows.sticky_window import StickyWindow
		
		# Count open sticky windows
		sticky_count = 0
		for win in self.get_windows():
			if isinstance(win, StickyWindow):
				sticky_count += 1
		
		if sticky_count > 0:
			# There are open sticky notes, just hide the main window
			window.set_visible(False)
			# Return True to prevent default close behavior (destruction)
			return True
		else:
			# No sticky notes open, quit the application
			self.quit()
			# Return False to allow normal close
			return False
	
	def show_main_window(self):
		"""Show or restore the main window."""
		if self.main_window is None:
			self.main_window = MainWindow(application=self)
			self.main_window.connect("close-request", self._on_main_window_close)
		
		self.main_window.present()
	
	def do_startup(self):
		"""Called once when the application starts."""
		Adw.Application.do_startup(self)
		
		# Create actions for app-level commands
		quit_action = Gio.SimpleAction.new("quit", None)
		quit_action.connect("activate", self._on_quit)
		self.add_action(quit_action)
		
		show_main_action = Gio.SimpleAction.new("show-main", None)
		show_main_action.connect("activate", lambda *_: self.show_main_window())
		self.add_action(show_main_action)
		
		# Restore previously open sticky notes
		self._restore_open_notes()
	
	def _on_quit(self, action, param):
		"""Quit the application - close all windows and exit."""
		# Get all windows and close them
		windows = list(self.get_windows())
		for window in windows:
			window.destroy()
		
		self.quit()
	
	def _restore_open_notes(self):
		"""Restore sticky notes that were open in the last session."""
		try:
			from gtk_app.windows.sticky_window import StickyWindow
			open_note_ids = self.db.get_open_notes()
			
			for note_id in open_note_ids:
				# Create sticky window for each open note
				# Use None as transient_for since main window may not exist yet
				sticky = StickyWindow(
					transient_for=None, 
					db=self.db, 
					note_id=note_id,
					application=self
				)
				sticky.present()
		except Exception as e:
			print(f"Error restoring open notes: {e}")


def main():
	app = StickyNotesApp()
	return app.run()

