"""Trash window for GTK/libadwaita UI.

Shows deleted notes with actions to restore or delete permanently.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

import os
from core.config import PROJECT_ROOT


class TrashWindow(Adw.ApplicationWindow):
    def __init__(self, application, db, **kwargs):
        super().__init__(application=application, **kwargs)
        
        # Load UI from file
        builder = Gtk.Builder()
        ui_file = os.path.join(PROJECT_ROOT, "resources", "gtk", "ui", "trash_window.ui")
        builder.add_from_file(ui_file)
        
        # Get widgets from builder
        self.trash_list = builder.get_object("trash_list")
        
        # Get the UI window and extract its content
        ui_window = builder.get_object("TrashWindow")
        main_box = builder.get_object("main_box")
        
        # Remove main_box from ui_window before setting it to our window
        if ui_window and main_box:
            ui_window.set_child(None)
        
        # Set up the window content
        self.set_content(main_box)
        self.set_default_size(600, 400)
        
        self.db = db

        self._setup_list()
        self._reload()

    def _setup_list(self):
        self._items = Gtk.StringList.new([])
        self._selection = Gtk.SingleSelection.new(self._items)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_setup)
        factory.connect("bind", self._on_bind)

        self.trash_list.set_model(self._selection)
        self.trash_list.set_factory(factory)

    def _on_setup(self, _factory, list_item: Gtk.ListItem):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(xalign=0)
        label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        label.set_hexpand(True)
        btn_restore = Gtk.Button(label="Restore")
        btn_delete = Gtk.Button(label="Delete")
        box.append(label)
        box.append(btn_restore)
        box.append(btn_delete)
        list_item.set_child(box)

    def _on_bind(self, _factory, list_item: Gtk.ListItem):
        box: Gtk.Box = list_item.get_child()
        label: Gtk.Label = box.get_first_child()
        # The item string is "<id>: <title>"
        s = list_item.get_item().get_string()
        label.set_text(s)

        # Find buttons
        children = []
        child = box.get_first_child()
        while child:
            children.append(child)
            child = child.get_next_sibling()
        btn_restore: Gtk.Button = children[-2]
        btn_delete: Gtk.Button = children[-1]

        note_id = int(s.split(":", 1)[0])
        
        # Disconnect all existing handlers
        try:
            btn_restore.disconnect_by_func(self._on_restore_clicked)
        except:
            pass
        try:
            btn_delete.disconnect_by_func(self._on_delete_clicked)
        except:
            pass
        
        # Connect new handlers
        btn_restore.connect("clicked", self._on_restore_clicked, note_id)
        btn_delete.connect("clicked", self._on_delete_clicked, note_id)

    def _reload(self):
        rows = self.db.all_trash()
        texts = [f"{r['id']}: {r['title'] or 'Untitled'}" for r in rows]
        self._items.splice(0, self._items.get_n_items(), texts)

    def _on_restore_clicked(self, _btn, note_id: int):
        try:
            self.db.restore_from_trash(note_id)
        finally:
            self._reload()

    def _on_delete_clicked(self, _btn, note_id: int):
        try:
            self.db.delete_permanently(note_id)
        finally:
            self._reload()
