"""Main window implemented with libadwaita, following GNOME HIG.

Functionally mirrors the previous main window: list notes, search, open/create.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib
import os

from data.database import NotesDB
from gtk_app.windows.sticky_window import StickyWindow
from gtk_app.windows.trash_window import TrashWindow
from gtk_app.dialogs.about_dialog import AboutDialog
from core.config import PROJECT_ROOT


class MainWindow(Adw.ApplicationWindow):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		# Load UI from file
		builder = Gtk.Builder()
		ui_file = os.path.join(PROJECT_ROOT, "resources", "gtk", "ui", "main_window.ui")
		builder.add_from_file(ui_file)
		
		# Get widgets from builder
		self.btn_new = builder.get_object("btn_new")
		self.menu_button = builder.get_object("menu_button")
		self.search_entry = builder.get_object("search_entry")
		self.notes_list = builder.get_object("notes_list")
		
		# Get the UI window and extract its content
		ui_window = builder.get_object("MainWindow")
		main_box = builder.get_object("main_box")
		
		# Remove main_box from ui_window before setting it to our window
		if ui_window and main_box:
			ui_window.set_child(None)  # Remove child from builder window
		
		# Set up the window content
		self.set_content(main_box)
		self.set_default_size(720, 480)

		self.db = NotesDB()
		self.stickies = {}
		self._first_hide = True  # Flag to show notification on first hide
		
		# Override close button to minimize to background instead
		self.connect("close-request", self._on_close_request)

		# Actions
		self.btn_new.connect("clicked", self.on_new_clicked)
		self.search_entry.connect("search-changed", self.on_search_changed)
		self._setup_menu()

		self._reload_list()
	
	def _on_close_request(self, _widget):
		"""Handle window close request - hide instead of closing."""
		if self._first_hide:
			self._first_hide = False
			# Show Adwaita toast notification
			toast = Adw.Toast.new("App is running in background. Use Quit from menu to exit.")
			toast.set_timeout(4)
			# Note: We need an AdwToastOverlay for this, but for now just print
			print("Ubuntu Sticky Notes is running in the background.")
			print("Use the application menu 'Quit' option to exit completely.")
		self.hide()
		return True  # Prevent default close behavior

	def _reload_list(self, query: str = ""):
		# Simplified: use a StringList model. Filter on client side for now.
		rows = self.db.all_notes(full=False)
		if query:
			query_lower = query.lower()
			notes = [r for r in rows if (r["title"] or "").lower().find(query_lower) != -1]
		else:
			notes = rows
		items = Gtk.StringList.new([f"{n['id']}: {n['title'] or 'Untitled'}" for n in notes])
		factory = Gtk.SignalListItemFactory()
		factory.connect("setup", lambda f, li: li.set_child(Gtk.Label(xalign=0)))
		def bind(_f, li):
			idx = li.get_item().get_string()
			li.get_child().set_text(idx)
		factory.connect("bind", bind)
		selection = Gtk.SingleSelection.new(items)
		self.notes_list.set_model(selection)
		self.notes_list.set_factory(factory)
		self.notes_list.connect("activate", self.on_note_activate)

	def _setup_menu(self):
		menu = Gio.Menu()
		menu.append("About", "win.about")
		menu.append("Trash", "win.trash")
		menu.append("Quit", "app.quit")
		popover = Gtk.PopoverMenu.new_from_model(menu)
		self.menu_button.set_popover(popover)

		a_about = Gio.SimpleAction.new("about", None)
		a_about.connect("activate", lambda *_: self._on_about())
		self.add_action(a_about)

		a_trash = Gio.SimpleAction.new("trash", None)
		a_trash.connect("activate", lambda *_: self._on_trash())
		self.add_action(a_trash)

		app = self.get_application()
		if app and not app.lookup_action("quit"):
			a_quit = Gio.SimpleAction.new("quit", None)
			a_quit.connect("activate", lambda *_: app.quit())
			app.add_action(a_quit)

	def _on_about(self):
		dlg = AboutDialog(self)
		dlg.present()

	def _on_trash(self):
		win = TrashWindow(self.get_application(), self.db)
		win.present()

	# Signal handlers
	def on_new_clicked(self, _btn):
		sticky = StickyWindow(self, self.db, note_id=None)
		sticky.present()

	def on_search_changed(self, entry):
		self._reload_list(entry.get_text())

	def on_note_activate(self, _list, position):
		item = _list.get_model().get_item(position)
		text = item.get_string()
		note_id = int(text.split(":", 1)[0])
		sticky = StickyWindow(self, self.db, note_id=note_id)
		sticky.present()

