"""Trash window for GTK/libadwaita UI.

Shows deleted notes with actions to restore or delete permanently.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

import os
from core.config import PROJECT_ROOT
from core.i18n import _


class TrashWindow(Adw.ApplicationWindow):
    def __init__(self, application, db, main_window=None, **kwargs):
        super().__init__(application=application, **kwargs)
        
        # Load UI from file
        builder = Gtk.Builder()
        ui_file = os.path.join(PROJECT_ROOT, "resources", "gtk", "ui", "trash_window.ui")
        builder.add_from_file(ui_file)
        
        # Get widgets from builder
        self.trash_list = builder.get_object("trash_list")
        self.btn_restore = builder.get_object("btn_restore")
        self.btn_delete = builder.get_object("btn_delete")
        self.btn_empty = builder.get_object("btn_empty")
        
        # Get the UI window and extract its content
        ui_window = builder.get_object("TrashWindow")
        main_box = builder.get_object("main_box")
        
        # Remove main_box from ui_window before setting it to our window
        if ui_window and main_box:
            ui_window.set_child(None)
        
        # Set up the window content
        self.set_content(main_box)
        self.set_default_size(600, 400)
        
        # Set translated labels
        self._set_translated_labels()
        
        # Apply custom CSS for rounded corners
        self._apply_custom_css()
        
        self.db = db
        self.main_window = main_window  # Store reference to main window
        self._selected_note_id = None

        # Connect button signals
        self.btn_restore.connect("clicked", self._on_restore_clicked)
        self.btn_delete.connect("clicked", self._on_delete_clicked)
        self.btn_empty.connect("clicked", self._on_empty_clicked)

        self._setup_list()
        self._reload()

    def _set_translated_labels(self):
        """Set translated labels for UI elements."""
        self.set_title(_("Trash"))
        self.btn_restore.set_label(_("Restore"))
        self.btn_delete.set_label(_("Delete"))
        self.btn_empty.set_label(_("Empty Trash"))
        self.btn_restore.set_tooltip_text(_("Restore selected note"))
        self.btn_delete.set_tooltip_text(_("Permanently delete selected note"))

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

    def _setup_list(self):
        self._notes_data = {}
        self._items = Gtk.StringList.new([])
        self._selection = Gtk.SingleSelection.new(self._items)
        
        # Connect selection changed signal
        self._selection.connect("selection-changed", self._on_selection_changed)

        factory = Gtk.SignalListItemFactory()
        
        def setup(_f, li):
            label = Gtk.Label(xalign=0)
            label.set_margin_start(8)
            label.set_margin_end(8)
            label.set_margin_top(8)
            label.set_margin_bottom(8)
            li.set_child(label)
        
        def bind(_f, li):
            text = li.get_item().get_string()
            li.get_child().set_text(text)
        
        factory.connect("setup", setup)
        factory.connect("bind", bind)

        self.trash_list.set_model(self._selection)
        self.trash_list.set_factory(factory)

    def _on_selection_changed(self, selection, _position, _n_items):
        """Handle selection changes to enable/disable action buttons."""
        selected = selection.get_selected()
        
        if selected != Gtk.INVALID_LIST_POSITION and selected in self._notes_data:
            self._selected_note_id = self._notes_data[selected]['id']
            self.btn_restore.set_sensitive(True)
            self.btn_delete.set_sensitive(True)
        else:
            self._selected_note_id = None
            self.btn_restore.set_sensitive(False)
            self.btn_delete.set_sensitive(False)

    def _reload(self):
        rows = self.db.all_trash()
        
        # Store notes data BEFORE updating items
        self._notes_data = {i: r for i, r in enumerate(rows)}
        
        # Create list with just titles
        texts = [r['title'] or 'Untitled' for r in rows]
        self._items.splice(0, self._items.get_n_items(), texts)
        
        # Update empty button sensitivity
        self.btn_empty.set_sensitive(len(rows) > 0)
        
        # Check current selection and update buttons
        selected = self._selection.get_selected()
        if selected != Gtk.INVALID_LIST_POSITION and selected in self._notes_data:
            self._selected_note_id = self._notes_data[selected]['id']
            self.btn_restore.set_sensitive(True)
            self.btn_delete.set_sensitive(True)
        else:
            self._selected_note_id = None
            self.btn_restore.set_sensitive(False)
            self.btn_delete.set_sensitive(False)

    def _on_restore_clicked(self, _btn):
        if self._selected_note_id:
            try:
                self.db.restore_from_trash(self._selected_note_id)
                # Notify main window to refresh its list
                if self.main_window:
                    self.main_window._reload_list()
            finally:
                self._reload()

    def _on_delete_clicked(self, _btn):
        if self._selected_note_id:
            # Show confirmation dialog
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading(_("Delete Permanently?"))
            dialog.set_body(_("This note will be permanently deleted and cannot be recovered."))
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("delete", _("Delete"))
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            
            def on_response(_dialog, response):
                if response == "delete":
                    try:
                        self.db.delete_permanently(self._selected_note_id)
                    finally:
                        self._reload()
            
            dialog.connect("response", on_response)
            dialog.present()

    def _on_empty_clicked(self, _btn):
        # Show confirmation dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Empty Trash?"))
        dialog.set_body(_("All notes in trash will be permanently deleted and cannot be recovered."))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("empty", _("Delete All"))
        dialog.set_response_appearance("empty", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(_dialog, response):
            if response == "empty":
                try:
                    rows = self.db.all_trash()
                    for row in rows:
                        self.db.delete_permanently(row['id'])
                finally:
                    self._reload()
        
        dialog.connect("response", on_response)
        dialog.present()
