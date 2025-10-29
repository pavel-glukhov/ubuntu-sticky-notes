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
from core.i18n import _


class MainWindow(Adw.ApplicationWindow):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		# Load UI from file
		builder = Gtk.Builder()
		ui_file = os.path.join(PROJECT_ROOT, "resources", "gtk", "ui", "main_window.ui")
		builder.add_from_file(ui_file)
		
		# Get widgets from builder
		self.btn_new = builder.get_object("btn_new")
		self.btn_trash = builder.get_object("btn_trash")
		self.btn_sort = builder.get_object("btn_sort")
		self.menu_button = builder.get_object("menu_button")
		self.search_entry = builder.get_object("search_entry")
		self.notes_list = builder.get_object("notes_list")
		
		# Table header labels
		self.lbl_header_name = builder.get_object("lbl_header_name")
		self.lbl_header_modified = builder.get_object("lbl_header_modified")
		self.lbl_header_created = builder.get_object("lbl_header_created")
		self.lbl_header_actions = builder.get_object("lbl_header_actions")
		
		# Get the UI window and extract its content
		ui_window = builder.get_object("MainWindow")
		main_box = builder.get_object("main_box")
		
		# Remove main_box from ui_window before setting it to our window
		if ui_window and main_box:
			ui_window.set_child(None)  # Remove child from builder window
		
		# Set up the window content
		self.set_content(main_box)
		self.set_default_size(720, 480)
		
		# Set translated labels
		self._set_translated_labels()
		
		# Apply custom CSS for rounded corners
		self._apply_custom_css()

		self.db = NotesDB()
		self.stickies = {}
		self._notes_data = {}  # Cache note data for row activation
		
		# Sorting state: (field, direction)
		# Fields: 'title', 'created_at', 'updated_at'
		# Directions: 'asc', 'desc'
		self._sort_by = ('updated_at', 'desc')  # Default: newest first

		# Initialize UI components
		self._setup_list_factory()

		# Connect signals
		self.btn_new.connect("clicked", self.on_new_clicked)
		self.btn_trash.connect("clicked", lambda *_: self._on_trash())
		self.search_entry.connect("search-changed", self.on_search_changed)
		self._setup_menu()
		self._setup_sort_menu()

		self._reload_list()
	
	def _set_translated_labels(self):
		"""Set translated labels for UI elements."""
		# Update button labels and tooltips
		self.btn_new.set_label(_("+ Add"))
		self.btn_new.set_tooltip_text(_("New Note"))
		self.btn_trash.set_tooltip_text(_("Trash"))
		self.menu_button.set_tooltip_text(_("Menu"))
		self.search_entry.set_placeholder_text(_("Search notes…"))
		self.btn_sort.set_tooltip_text(_("Sort"))
		
		# Update table headers
		self.lbl_header_name.set_label(_("Note Name"))
		self.lbl_header_modified.set_label(_("Modified"))
		self.lbl_header_created.set_label(_("Created"))
		self.lbl_header_actions.set_label(_("Actions"))
		
		# Update window title
		self.set_title(_("Sticky Notes"))
	
	def _apply_custom_css(self):
		"""Apply custom CSS for rounded corners and styling."""
		css_provider = Gtk.CssProvider()
		css = b"""
		scrolledwindow {
			border-radius: 8px;
		}
		listview {
			border-radius: 8px;
		}
		listview > row {
			border-radius: 6px;
			margin: 2px;
		}
		"""
		css_provider.load_from_data(css)
		Gtk.StyleContext.add_provider_for_display(
			self.get_display(),
			css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)
	
	def _setup_list_factory(self):
		"""Setup list factory once to avoid duplicate signal connections."""
		factory = Gtk.SignalListItemFactory()
		
		def setup(_f, li):
			# Create horizontal box for table-like row
			box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
			box.set_margin_start(48)  # Leave space for sort button
			box.set_margin_end(8)
			box.set_margin_top(8)
			box.set_margin_bottom(8)
			
			# Note title (expandable)
			lbl_title = Gtk.Label(xalign=0)
			lbl_title.set_hexpand(True)
			lbl_title.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
			
			# Updated date
			lbl_updated = Gtk.Label(xalign=0)
			lbl_updated.set_width_chars(17)  # DD.MM.YYYY HH:MM
			lbl_updated.add_css_class("dim-label")
			
			# Created date
			lbl_created = Gtk.Label(xalign=0)
			lbl_created.set_width_chars(17)  # DD.MM.YYYY HH:MM
			lbl_created.add_css_class("dim-label")
			
			# Actions box
			actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
			actions_box.set_size_request(100, -1)  # Fixed width for actions
			
			btn_share = Gtk.Button(icon_name="emblem-shared-symbolic")
			btn_share.set_tooltip_text("Paylaş")
			btn_share.add_css_class("flat")
			
			btn_delete = Gtk.Button(icon_name="user-trash-symbolic")
			btn_delete.set_tooltip_text("Çöp Kutusuna Taşı")
			btn_delete.add_css_class("flat")
			
			actions_box.append(btn_share)
			actions_box.append(btn_delete)
			
			box.append(lbl_title)
			box.append(lbl_updated)
			box.append(lbl_created)
			box.append(actions_box)
			
			li.set_child(box)
		
		def bind(_f, li):
			box = li.get_child()
			children = []
			child = box.get_first_child()
			while child:
				children.append(child)
				child = child.get_next_sibling()
			
			lbl_title = children[0]
			lbl_updated = children[1]
			lbl_created = children[2]
			actions_box = children[3]
			
			btn_share = actions_box.get_first_child()
			btn_delete = btn_share.get_next_sibling()
			
			position = li.get_position()
			
			if position in self._notes_data:
				note = self._notes_data[position]
				lbl_title.set_text(note['title'] or 'Untitled')
				
				# Format dates as DD.MM.YYYY HH:MM
				updated_date = self._format_date(note['updated_at'])
				created_date = self._format_date(note['created_at'])
				
				lbl_updated.set_text(updated_date)
				lbl_created.set_text(created_date)
			
			# Disconnect all previous handlers to avoid duplicates
			handlers = []
			
			# Get signal handlers
			def collect_handlers(obj, signal_name):
				try:
					handler_ids = []
					# This is a workaround - we'll just reconnect
					return handler_ids
				except (AttributeError, TypeError):
					return []
			
			# Simple approach: store position in widget data and use lambda
			# to avoid disconnect issues
			def on_delete_clicked(_btn):
				self._on_delete_note(_btn, position)
			
			def on_share_clicked(_btn):
				self._on_share_note(_btn, position)
			
			# Store handlers to disconnect later
			if not hasattr(btn_delete, '_sticky_handler'):
				btn_delete._sticky_handler = None
			if not hasattr(btn_share, '_sticky_handler'):
				btn_share._sticky_handler = None
			
			# Disconnect old handlers
			if btn_delete._sticky_handler:
				btn_delete.disconnect(btn_delete._sticky_handler)
			if btn_share._sticky_handler:
				btn_share.disconnect(btn_share._sticky_handler)
			
			# Connect new handlers and store IDs
			btn_delete._sticky_handler = btn_delete.connect("clicked", on_delete_clicked)
			btn_share._sticky_handler = btn_share.connect("clicked", on_share_clicked)
		
		factory.connect("setup", setup)
		factory.connect("bind", bind)
		
		self.notes_list.set_factory(factory)
		
		# Connect activate handler ONCE
		self.notes_list.connect("activate", self.on_note_activate)
	
	def _format_date(self, date_str):
		"""Format ISO date string to DD.MM.YYYY HH:MM"""
		if not date_str:
			return "—"
		try:
			from datetime import datetime
			dt = datetime.fromisoformat(date_str)
			return dt.strftime("%d.%m.%Y %H:%M")
		except (ValueError, TypeError, AttributeError):
			return "—"
	
	def _reload_list(self, query: str = ""):
		# Get all notes with full data for dates
		rows = self.db.all_notes(full=True)
		if query:
			query_lower = query.lower()
			notes = [r for r in rows if (r["title"] or "").lower().find(query_lower) != -1]
		else:
			notes = list(rows)
		
		# Apply sorting
		sort_field, sort_direction = self._sort_by
		reverse = (sort_direction == 'desc')
		
		if sort_field == 'title':
			notes.sort(key=lambda n: (n['title'] or 'Untitled').lower(), reverse=reverse)
		elif sort_field == 'created_at':
			notes.sort(key=lambda n: n['created_at'] or '', reverse=reverse)
		elif sort_field == 'updated_at':
			notes.sort(key=lambda n: n['updated_at'] or '', reverse=reverse)
		
		# Store notes for reference when activating
		self._notes_data = {i: n for i, n in enumerate(notes)}
		
		# Create list with just titles
		items = Gtk.StringList.new([n['title'] or 'Untitled' for n in notes])
		
		# Just update the model, factory is already setup
		selection = Gtk.SingleSelection.new(items)
		self.notes_list.set_model(selection)
	
	def _setup_sort_menu(self):
		"""Setup sorting menu with options."""
		menu = Gio.Menu()
		
		# Title sorting
		title_section = Gio.Menu()
		title_section.append(_("Name (A → Z)"), "win.sort::title_asc")
		title_section.append(_("Name (Z → A)"), "win.sort::title_desc")
		menu.append_section(_("By Name"), title_section)
		
		# Date sorting
		date_section = Gio.Menu()
		date_section.append(_("Modified (Newest → Oldest)"), "win.sort::updated_desc")
		date_section.append(_("Modified (Oldest → Newest)"), "win.sort::updated_asc")
		date_section.append(_("Created (Newest → Oldest)"), "win.sort::created_desc")
		date_section.append(_("Created (Oldest → Newest)"), "win.sort::created_asc")
		menu.append_section(_("By Date"), date_section)
		
		popover = Gtk.PopoverMenu.new_from_model(menu)
		self.btn_sort.set_popover(popover)
		
		# Create action with parameter
		action = Gio.SimpleAction.new("sort", GLib.VariantType.new("s"))
		action.connect("activate", self._on_sort_changed)
		self.add_action(action)
	
	def _on_sort_changed(self, action, parameter):
		"""Handle sort option change."""
		sort_option = parameter.get_string()
		
		# Parse sort option
		if sort_option == "title_asc":
			self._sort_by = ('title', 'asc')
			self.btn_sort.set_icon_name("view-sort-ascending-symbolic")
		elif sort_option == "title_desc":
			self._sort_by = ('title', 'desc')
			self.btn_sort.set_icon_name("view-sort-descending-symbolic")
		elif sort_option == "updated_asc":
			self._sort_by = ('updated_at', 'asc')
			self.btn_sort.set_icon_name("view-sort-ascending-symbolic")
		elif sort_option == "updated_desc":
			self._sort_by = ('updated_at', 'desc')
			self.btn_sort.set_icon_name("view-sort-descending-symbolic")
		elif sort_option == "created_asc":
			self._sort_by = ('created_at', 'asc')
			self.btn_sort.set_icon_name("view-sort-ascending-symbolic")
		elif sort_option == "created_desc":
			self._sort_by = ('created_at', 'desc')
			self.btn_sort.set_icon_name("view-sort-descending-symbolic")
		
		# Reload list with new sorting
		self._reload_list()

	def _setup_menu(self):
		menu = Gio.Menu()
		
		# Language submenu
		lang_menu = Gio.Menu()
		from core.i18n import SUPPORTED_LANGUAGES, get_current_language
		current_lang = get_current_language()
		
		for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
			if lang_code == current_lang:
				lang_menu.append(f"✓ {lang_name}", f"win.set-language::{lang_code}")
			else:
				lang_menu.append(lang_name, f"win.set-language::{lang_code}")
		
		menu.append_submenu(_("Language"), lang_menu)
		menu.append(_("Error Log"), "win.show-error-log")
		menu.append(_("About"), "win.about")
		
		popover = Gtk.PopoverMenu.new_from_model(menu)
		self.menu_button.set_popover(popover)

		# Language action
		a_lang = Gio.SimpleAction.new("set-language", GLib.VariantType.new("s"))
		a_lang.connect("activate", self._on_language_changed)
		self.add_action(a_lang)
		
		# Error log action
		a_error_log = Gio.SimpleAction.new("show-error-log", None)
		a_error_log.connect("activate", lambda *_: self._on_show_error_log())
		self.add_action(a_error_log)

		a_about = Gio.SimpleAction.new("about", None)
		a_about.connect("activate", lambda *_: self._on_about())
		self.add_action(a_about)

	def _on_language_changed(self, action, parameter):
		"""Handle language change."""
		lang_code = parameter.get_string()
		
		from core.i18n import set_language
		set_language(lang_code)
		
		# Update all UI labels immediately
		self._set_translated_labels()
		
		# Rebuild sort menu with new translations
		self._setup_sort_menu()
		
		# Rebuild main menu with new translations
		self._setup_menu()
		
		# Update all open sticky windows
		from gtk_app.windows.sticky_window import StickyWindow
		app = self.get_application()
		if app:
			for window in app.get_windows():
				if isinstance(window, StickyWindow):
					window.refresh_menus_for_language_change()
		
		# Reload list to update any date/time formatting if needed
		self._reload_list()

	def _on_about(self):
		dlg = AboutDialog(self)
		dlg.present()
	
	def _on_show_error_log(self):
		"""Show error log viewer dialog."""
		from src.utils.error_logger import get_recent_logs, get_log_path, get_log_size_info
		
		# Get log size info
		size_info = get_log_size_info()
		
		# Create dialog
		dialog = Adw.Window()
		dialog.set_transient_for(self)
		dialog.set_modal(True)
		dialog.set_title(_("Error Log"))
		dialog.set_default_size(800, 600)
		
		# Create main box
		main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
		main_box.set_margin_top(12)
		main_box.set_margin_bottom(12)
		main_box.set_margin_start(12)
		main_box.set_margin_end(12)
		
		# Header with file path and size
		header_label = Gtk.Label()
		size_mb = size_info['total_size_mb']
		file_count = size_info['file_count']
		header_text = f"<b>{_('Log File Location')}:</b> {get_log_path()}\n"
		header_text += f"<b>{_('Total Size')}:</b> {size_mb} MB ({file_count} file(s))"
		header_label.set_markup(header_text)
		header_label.set_xalign(0)
		header_label.set_wrap(True)
		header_label.set_selectable(True)
		main_box.append(header_label)
		
		# ScrolledWindow for log content
		scrolled = Gtk.ScrolledWindow()
		scrolled.set_vexpand(True)
		scrolled.set_hexpand(True)
		
		# TextView for log content
		text_view = Gtk.TextView()
		text_view.set_editable(False)
		text_view.set_monospace(True)
		text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
		text_view.set_left_margin(6)
		text_view.set_right_margin(6)
		text_view.set_top_margin(6)
		text_view.set_bottom_margin(6)
		
		# Get and display recent logs
		logs = get_recent_logs(500)  # Last 500 lines
		text_view.get_buffer().set_text(logs)
		
		scrolled.set_child(text_view)
		main_box.append(scrolled)
		
		# Button box
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		button_box.set_halign(Gtk.Align.END)
		
		# Copy button
		btn_copy = Gtk.Button(label=_("Copy to Clipboard"))
		btn_copy.add_css_class("suggested-action")
		btn_copy.connect("clicked", lambda *_: self._copy_log_to_clipboard(logs, dialog))
		button_box.append(btn_copy)
		
		# Close button
		btn_close = Gtk.Button(label=_("Close"))
		btn_close.connect("clicked", lambda *_: dialog.close())
		button_box.append(btn_close)
		
		main_box.append(button_box)
		
		dialog.set_content(main_box)
		dialog.present()
	
	def _copy_log_to_clipboard(self, logs, parent_dialog):
		"""Copy error log to clipboard."""
		clipboard = parent_dialog.get_clipboard()
		clipboard.set(logs)
		
		# Show confirmation toast (if using libadwaita ToastOverlay)
		# For now, just show a simple dialog
		msg = Adw.MessageDialog.new(parent_dialog)
		msg.set_heading(_("Copied"))
		msg.set_body(_("Error log copied to clipboard"))
		msg.add_response("ok", _("OK"))
		msg.set_default_response("ok")
		msg.set_close_response("ok")
		msg.present()

	def _on_trash(self):
		win = TrashWindow(self.get_application(), self.db, main_window=self)
		win.present()

	# Signal handlers
	def on_new_clicked(self, _btn):
		"""Show dialog to get note title and create new note."""
		dialog = Adw.MessageDialog.new(self)
		dialog.set_heading(_("Create New Note"))
		dialog.set_body(_("Enter note title:"))
		
		# Add entry for title
		entry = Gtk.Entry()
		entry.set_placeholder_text(_("Note title…"))
		entry.set_margin_start(12)
		entry.set_margin_end(12)
		entry.set_margin_top(6)
		entry.set_margin_bottom(6)
		dialog.set_extra_child(entry)
		
		dialog.add_response("cancel", _("Cancel"))
		dialog.add_response("create", _("Create"))
		dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
		dialog.set_default_response("create")
		dialog.set_close_response("cancel")
		
		def on_response(_dialog, response):
			if response == "create":
				title = entry.get_text().strip()
				if not title:
					title = "Untitled"
				
				print(f"[DEBUG] Creating new note with title: '{title}'")
				# Create note with title
				note_id = self.db.add(title, "", 300, 200, 320, 240, "#FFF59D", 0)
				print(f"[DEBUG] Note created with ID: {note_id}")
				self._reload_list()
				print(f"[DEBUG] List reloaded")
				
				# CRITICAL FIX: Close dialog first, then open window
				# This ensures the dialog's event loop is completely finished
				_dialog.close()
				
				# Use idle_add with higher priority and delay
				def open_sticky_window():
					print(f"[DEBUG] Opening StickyWindow for note {note_id}")
					sticky = StickyWindow(self, self.db, note_id=note_id)
					print(f"[DEBUG] StickyWindow created, presenting...")
					sticky.present()
					print(f"[DEBUG] StickyWindow presented successfully")
					return False  # Remove idle callback
				
				# Use timeout instead of idle_add for more reliable execution
				GLib.timeout_add(100, open_sticky_window)  # 100ms delay
		
		dialog.connect("response", on_response)
		
		# Submit on Enter key - but don't use dialog.response()
		def on_entry_activate(_entry):
			# Trigger the response manually without calling dialog.response()
			# This avoids the event loop conflict
			title = entry.get_text().strip()
			if not title:
				title = "Untitled"
			
			print(f"[DEBUG] Enter pressed - Creating note with title: '{title}'")
			note_id = self.db.add(title, "", 300, 200, 320, 240, "#FFF59D", 0)
			print(f"[DEBUG] Note created with ID: {note_id}")
			
			# Close dialog first
			dialog.close()
			
			# Reload list
			self._reload_list()
			
			# Open window after dialog is completely closed
			def open_sticky_window():
				print(f"[DEBUG] Opening StickyWindow for note {note_id}")
				sticky = StickyWindow(self, self.db, note_id=note_id)
				print(f"[DEBUG] StickyWindow created, presenting...")
				sticky.present()
				print(f"[DEBUG] StickyWindow presented successfully")
				return False
			
			GLib.timeout_add(150, open_sticky_window)
		
		entry.connect("activate", on_entry_activate)
		
		dialog.present()

	def on_search_changed(self, entry):
		self._reload_list(entry.get_text())

	def on_note_activate(self, _list, position):
		if position in self._notes_data:
			note = self._notes_data[position]
			note_id = note['id']
			sticky = StickyWindow(self, self.db, note_id=note_id)
			sticky.present()
	
	def _on_delete_note(self, _btn, position):
		"""Move note to trash."""
		if position in self._notes_data:
			note = self._notes_data[position]
			note_id = note['id']
			
			try:
				self.db.move_to_trash(note_id)
				self._reload_list()
			except Exception as e:
				print(f"Error moving note to trash: {e}")
	
	def _on_share_note(self, _btn, position):
		"""Share note (placeholder for now)."""
		if position in self._notes_data:
			note = self._notes_data[position]
			title = note['title'] or 'Untitled'
			
			# Show a simple info dialog for now
			dialog = Adw.MessageDialog.new(self)
			dialog.set_heading("Paylaş")
			dialog.set_body(f"'{title}' notunu paylaşma özelliği yakında eklenecek!")
			dialog.add_response("ok", "Tamam")
			dialog.set_default_response("ok")
			dialog.present()

