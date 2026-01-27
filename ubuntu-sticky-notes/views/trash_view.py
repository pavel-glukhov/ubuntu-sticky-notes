import builtins
from gi.repository import Gtk, Adw
from views.main_view.note_card import NoteCard

_ = builtins._

class TrashView(Gtk.Box):
    """
    A Gtk.Box widget that displays deleted notes and allows restoring or permanently deleting them.
    """
    def __init__(self, db, on_back_callback):
        """
        Initializes the TrashView.
        Args:
            db: The database controller instance.
            on_back_callback (callable): Callback function to return to the main view.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.db = db
        self.on_back_callback = on_back_callback

        # --- Header ---
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_top(10); header_box.set_margin_bottom(10)
        header_box.set_margin_start(10); header_box.set_margin_end(10)

        btn_back = Gtk.Button(label=_("<<- Back"))
        btn_back.connect("clicked", self._on_back_clicked)
        header_box.append(btn_back)

        lbl_title = Gtk.Label(label=_("Trash Bin"))
        lbl_title.add_css_class("title-2")
        lbl_title.set_hexpand(True)
        header_box.append(lbl_title)

        spacer = Gtk.Box()
        spacer.set_size_request(80, -1)
        header_box.append(spacer)

        self.append(header_box)
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Content ---
        self.flowbox = Gtk.FlowBox(valign=Gtk.Align.START, selection_mode=Gtk.SelectionMode.NONE)
        scrolled = Gtk.ScrolledWindow(child=self.flowbox, vexpand=True)
        scrolled.set_has_frame(False)
        self.append(scrolled)

        # --- Action Bar ---
        action_bar = Gtk.ActionBar()
        btn_clear = Gtk.Button(label=_("Empty Trash"))
        btn_clear.add_css_class("destructive-action")
        btn_clear.connect("clicked", self.on_empty_trash)
        action_bar.pack_end(btn_clear)
        self.append(action_bar)

        self.refresh_list()

    def _on_back_clicked(self, btn):
        """Callback for the back button."""
        if self.on_back_callback:
            self.on_back_callback()

    def refresh_list(self):
        """Refreshes the list of deleted notes from the database."""
        while child := self.flowbox.get_first_child():
            self.flowbox.remove(child)

        self.flowbox.set_homogeneous(False)
        self.flowbox.set_max_children_per_line(1)
        self.flowbox.set_min_children_per_line(1)
        self.flowbox.set_halign(Gtk.Align.FILL)
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_column_spacing(0)
        self.flowbox.set_row_spacing(10)
        self.flowbox.set_margin_top(10); self.flowbox.set_margin_bottom(10)
        self.flowbox.set_margin_start(10); self.flowbox.set_margin_end(10)

        trash_items = self.db.all_trash()

        if not trash_items:
            placeholder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, vexpand=True)
            lbl = Gtk.Label(label=_("Trash is empty"))
            lbl.add_css_class("dim-label"); lbl.add_css_class("title-3")
            icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
            icon.set_pixel_size(64)
            icon.add_css_class("dim-label")
            placeholder_box.append(icon)
            placeholder_box.append(lbl)
            self.flowbox.append(placeholder_box)
            child = placeholder_box.get_parent()
            child.set_hexpand(True); child.set_halign(Gtk.Align.FILL)
            return

        for note in trash_items:
            card = NoteCard(note, self.db, menu_callback=self.show_context_menu, refresh_callback=self.refresh_list)
            self.flowbox.append(card)
            flow_child = card.get_parent()
            if flow_child:
                flow_child.set_can_focus(False)
                flow_child.set_hexpand(True)
                flow_child.set_halign(Gtk.Align.FILL)

    def show_context_menu(self, note_id, target_widget):
        """
        Displays a context menu for a trashed note.
        Args:
            note_id (int): The ID of the note.
            target_widget (Gtk.Widget): The widget to attach the popover to.
        """
        popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, margin_top=5, margin_bottom=5, margin_start=5, margin_end=5)
        
        btn_restore = Gtk.Button(label=_("Restore Note"), has_frame=False, icon_name="edit-undo-symbolic")
        btn_restore.connect("clicked", lambda _: (self.restore_note(note_id), popover.popdown()))
        vbox.append(btn_restore)

        vbox.append(Gtk.Separator())

        btn_del = Gtk.Button(label=_("Delete Permanently"), has_frame=False)
        btn_del.add_css_class("destructive-action")
        btn_del.connect("clicked", lambda _: (self.delete_permanently(note_id), popover.popdown()))
        vbox.append(btn_del)

        popover.set_child(vbox)
        popover.set_parent(target_widget)
        popover.popup()

    def restore_note(self, note_id):
        """Restores a note from the trash."""
        self.db.restore_from_trash(note_id)
        self.refresh_list()

    def delete_permanently(self, note_id):
        """Permanently deletes a note from the database."""
        self.db.delete_permanently(note_id)
        self.refresh_list()

    def on_empty_trash(self, btn):
        """Shows a confirmation dialog to empty the trash."""
        dialog = Adw.MessageDialog(
            transient_for=self.get_native(),
            heading=_("Empty Trash"),
            body=_("Are you sure you want to permanently delete all items in the trash? This action cannot be undone."),
            modal=True,
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("empty", _("Empty Trash"))
        dialog.set_response_appearance("empty", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_empty_trash_confirm)
        dialog.present()

    def _on_empty_trash_confirm(self, dialog, response_id):
        """Callback for the empty trash confirmation dialog."""
        if response_id == "empty":
            for note in self.db.all_trash():
                self.db.delete_permanently(note['id'])
            self.refresh_list()
        dialog.close()
