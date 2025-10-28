"""System tray management utilities for Ubuntu Sticky Notes (GTK4 version)."""

import os
import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, Gio
from core.config import get_app_paths

# Try to import AppIndicator3 for system tray support
try:
	gi.require_version('AppIndicator3', '0.1')
	from gi.repository import AppIndicator3
	HAS_APPINDICATOR = True
except (ValueError, ImportError) as e:
	HAS_APPINDICATOR = False
	print(f"AppIndicator3 not available ({e}). Install with: sudo apt install gir1.2-appindicator3-0.1")


class SystemTrayManager:
	"""Manages the system tray icon and menu for Ubuntu Sticky Notes."""
	
	def __init__(self, app, main_window):
		"""
		Initialize the system tray icon.
		
		Args:
			app: The Adw.Application instance
			main_window: The MainWindow instance
		"""
		self.app = app
		self.main_window = main_window
		self.paths = get_app_paths()
		self.indicator = None
		
		if HAS_APPINDICATOR:
			self._init_appindicator()
		else:
			print("System tray not available without AppIndicator3")
	
	def _init_appindicator(self):
		"""Initialize AppIndicator-based tray icon."""
		# Create AppIndicator
		icon_path = self.paths["APP_ICON_PATH"]
		if not os.path.exists(icon_path):
			icon_path = "note"
		
		self.indicator = AppIndicator3.Indicator.new(
			"ubuntu-sticky-notes",
			icon_path,
			AppIndicator3.IndicatorCategory.APPLICATION_STATUS
		)
		
		self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
		self.indicator.set_title("Ubuntu Sticky Notes")
		
		# Create menu
		self.menu = Gtk.Menu()
		self._build_menu()
		self.indicator.set_menu(self.menu)
	
	def _build_menu(self):
		"""Build the tray menu."""
		# Show/Hide Main Window
		item_toggle = Gtk.MenuItem(label="📒 Show Notes List")
		item_toggle.connect("activate", self._on_toggle_main_window)
		self.menu.append(item_toggle)
		
		# New Note
		item_new = Gtk.MenuItem(label="🆕 New Sticky Note")
		item_new.connect("activate", self._on_new_note)
		self.menu.append(item_new)
		
		self.menu.append(Gtk.SeparatorMenuItem())
		
		# Open Previous State
		item_restore = Gtk.MenuItem(label="📘 Open Previous State")
		item_restore.connect("activate", self._on_restore_state)
		self.menu.append(item_restore)
		
		# Open All Notes
		item_open_all = Gtk.MenuItem(label="📗 Open All Notes")
		item_open_all.connect("activate", self._on_open_all)
		self.menu.append(item_open_all)
		
		# Hide All Notes
		item_hide_all = Gtk.MenuItem(label="🗂 Hide All Notes")
		item_hide_all.connect("activate", self._on_hide_all)
		self.menu.append(item_hide_all)
		
		self.menu.append(Gtk.SeparatorMenuItem())
		
		# About
		item_about = Gtk.MenuItem(label="ℹ️ About")
		item_about.connect("activate", self._on_about)
		self.menu.append(item_about)
		
		self.menu.append(Gtk.SeparatorMenuItem())
		
		# Quit
		item_quit = Gtk.MenuItem(label="❌ Quit")
		item_quit.connect("activate", self._on_quit)
		self.menu.append(item_quit)
		
		self.menu.show_all()
	
	def _on_toggle_main_window(self, _item):
		"""Toggle main window visibility."""
		if self.main_window.is_visible():
			self.main_window.hide()
		else:
			self.main_window.present()
	
	def _on_new_note(self, _item):
		"""Create a new sticky note."""
		self.main_window.on_new_clicked(None)
	
	def _on_restore_state(self, _item):
		"""Restore previously open notes."""
		from gtk_app.windows.sticky_window import StickyWindow
		
		try:
			open_notes = self.main_window.db.get_open_notes()
			for note_id in open_notes:
				if note_id not in self.main_window.stickies:
					sticky = StickyWindow(self.main_window, self.main_window.db, note_id=note_id)
					self.main_window.stickies[note_id] = sticky
					sticky.present()
		except Exception as e:
			print(f"Error restoring state: {e}")
	
	def _on_open_all(self, _item):
		"""Open all notes."""
		from gtk_app.windows.sticky_window import StickyWindow
		
		try:
			rows = self.main_window.db.all_notes(full=False)
			for row in rows:
				note_id = row["id"]
				if note_id not in self.main_window.stickies:
					sticky = StickyWindow(self.main_window, self.main_window.db, note_id=note_id)
					self.main_window.stickies[note_id] = sticky
					sticky.present()
		except Exception as e:
			print(f"Error opening all notes: {e}")
	
	def _on_hide_all(self, _item):
		"""Hide all sticky notes."""
		for sticky in self.main_window.stickies.values():
			sticky.hide()
	
	def _on_about(self, _item):
		"""Show about dialog."""
		from gtk_app.dialogs.about_dialog import AboutDialog
		dlg = AboutDialog(self.main_window)
		dlg.present()
	
	def _on_quit(self, _item):
		"""Quit the application."""
		# Save all open notes state
		for note_id, sticky in self.main_window.stickies.items():
			try:
				if sticky.is_visible():
					self.main_window.db.set_open_state(note_id, 1)
				else:
					self.main_window.db.set_open_state(note_id, 0)
			except:
				pass
		
		self.app.quit()


def init_tray(app, main_window):
	"""
	Initialize the system tray icon.
	
	Args:
		app: The Adw.Application instance
		main_window: The MainWindow instance
		
	Returns:
		SystemTrayManager instance or None if not available
	"""
	if not HAS_APPINDICATOR:
		return None
	return SystemTrayManager(app, main_window)

	"""Manages the system tray icon and menu for Ubuntu Sticky Notes."""
	
	def __init__(self, app, main_window):
		"""
		Initialize the system tray icon.
		
		Args:
			app: The Adw.Application instance
			main_window: The MainWindow instance
		"""
		self.app = app
		self.main_window = main_window
		self.paths = get_app_paths()
		
		# Create AppIndicator
		self.indicator = AppIndicator3.Indicator.new(
			"ubuntu-sticky-notes",
			self.paths["APP_ICON_PATH"] if os.path.exists(self.paths["APP_ICON_PATH"]) else "note",
			AppIndicator3.IndicatorCategory.APPLICATION_STATUS
		)
		
		self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
		self.indicator.set_title("Ubuntu Sticky Notes")
		
		# Create menu
		self.menu = Gtk.Menu()
		self._build_menu()
		self.indicator.set_menu(self.menu)
	
	def _build_menu(self):
		"""Build the tray menu."""
		# Show/Hide Main Window
		item_toggle = Gtk.MenuItem(label="📒 Show Notes List")
		item_toggle.connect("activate", self._on_toggle_main_window)
		self.menu.append(item_toggle)
		
		# New Note
		item_new = Gtk.MenuItem(label="🆕 New Sticky Note")
		item_new.connect("activate", self._on_new_note)
		self.menu.append(item_new)
		
		self.menu.append(Gtk.SeparatorMenuItem())
		
		# Open Previous State
		item_restore = Gtk.MenuItem(label="📘 Open Previous State")
		item_restore.connect("activate", self._on_restore_state)
		self.menu.append(item_restore)
		
		# Open All Notes
		item_open_all = Gtk.MenuItem(label="📗 Open All Notes")
		item_open_all.connect("activate", self._on_open_all)
		self.menu.append(item_open_all)
		
		# Hide All Notes
		item_hide_all = Gtk.MenuItem(label="🗂 Hide All Notes")
		item_hide_all.connect("activate", self._on_hide_all)
		self.menu.append(item_hide_all)
		
		self.menu.append(Gtk.SeparatorMenuItem())
		
		# About
		item_about = Gtk.MenuItem(label="ℹ️ About")
		item_about.connect("activate", self._on_about)
		self.menu.append(item_about)
		
		self.menu.append(Gtk.SeparatorMenuItem())
		
		# Quit
		item_quit = Gtk.MenuItem(label="❌ Quit")
		item_quit.connect("activate", self._on_quit)
		self.menu.append(item_quit)
		
		self.menu.show_all()
	
	def _on_toggle_main_window(self, _item):
		"""Toggle main window visibility."""
		if self.main_window.is_visible():
			self.main_window.hide()
		else:
			self.main_window.present()
	
	def _on_new_note(self, _item):
		"""Create a new sticky note."""
		self.main_window.on_new_clicked(None)
	
	def _on_restore_state(self, _item):
		"""Restore previously open notes."""
		from gtk_app.windows.sticky_window import StickyWindow
		
		try:
			open_notes = self.main_window.db.get_open_notes()
			for note_id in open_notes:
				if note_id not in self.main_window.stickies:
					sticky = StickyWindow(self.main_window, self.main_window.db, note_id=note_id)
					self.main_window.stickies[note_id] = sticky
					sticky.present()
		except Exception as e:
			print(f"Error restoring state: {e}")
	
	def _on_open_all(self, _item):
		"""Open all notes."""
		from gtk_app.windows.sticky_window import StickyWindow
		
		try:
			rows = self.main_window.db.all_notes(full=False)
			for row in rows:
				note_id = row["id"]
				if note_id not in self.main_window.stickies:
					sticky = StickyWindow(self.main_window, self.main_window.db, note_id=note_id)
					self.main_window.stickies[note_id] = sticky
					sticky.present()
		except Exception as e:
			print(f"Error opening all notes: {e}")
	
	def _on_hide_all(self, _item):
		"""Hide all sticky notes."""
		for sticky in self.main_window.stickies.values():
			sticky.hide()
	
	def _on_about(self, _item):
		"""Show about dialog."""
		from gtk_app.dialogs.about_dialog import AboutDialog
		dlg = AboutDialog(self.main_window)
		dlg.present()
	
	def _on_quit(self, _item):
		"""Quit the application."""
		# Save all open notes state
		for note_id, sticky in self.main_window.stickies.items():
			try:
				if sticky.is_visible():
					self.main_window.db.set_open_state(note_id, 1)
				else:
					self.main_window.db.set_open_state(note_id, 0)
			except:
				pass
		
		self.app.quit()


def init_tray(app, main_window):
	"""
	Initialize the system tray icon.
	
	Args:
		app: The Adw.Application instance
		main_window: The MainWindow instance
		
	Returns:
		SystemTrayManager instance
	"""
	return SystemTrayManager(app, main_window)

