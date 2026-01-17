from gi.repository import Gtk, Adw, Gdk, GObject


class TrashWindow(Gtk.Window):
    def __init__(self, db, main_window=None):
        super().__init__(title="Trash Bin", default_width=350, default_height=500)
        self.db = db
        self.main_window = main_window

        self.root_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_start=15,
            margin_end=15,
            margin_top=15,
            margin_bottom=15
        )
        self.set_child(self.root_box)

        self.list_box = Gtk.ListBox(show_separators=True, css_classes=["boxed-list"])
        scrolled = Gtk.ScrolledWindow(child=self.list_box, vexpand=True)
        self.root_box.append(scrolled)

        btn_clear = Gtk.Button(label="Empty Trash", css_classes=["destructive-action"])
        btn_clear.connect("clicked", self.on_empty_trash)
        self.root_box.append(btn_clear)

        self.refresh_list()

    def refresh_list(self):
        # Удаляем старые элементы
        while child := self.list_box.get_first_child():
            self.list_box.remove(child)

        for note in self.db.all_trash():
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                spacing=12,
                margin_start=10,
                margin_end=10,
                margin_top=10,
                margin_bottom=10
            )

            dot = Gtk.Box(width_request=12, height_request=12, css_classes=["color-dot"])
            dot.set_css_classes(["color-dot"])
            dot.set_name(f"dot_{note['id']}")

            label = Gtk.Label(label=f"{note['title'] or 'Untitled'}", xalign=0)
            date_label = Gtk.Label(label=note['deleted_at'], css_classes=["caption"])

            btn_restore = Gtk.Button(icon_name="edit-undo-symbolic", has_frame=False)
            btn_restore.connect("clicked", lambda _, nid=note['id']: self.restore_note(nid))

            hbox.append(dot)
            hbox.append(label)
            hbox.append(Gtk.Box(hexpand=True))  # Spacer
            hbox.append(date_label)
            hbox.append(btn_restore)

            row.set_child(hbox)
            self.list_box.append(row)

    def restore_note(self, note_id):
        self.db.restore_from_trash(note_id)
        self.refresh_list()
        if self.main_window:
            self.main_window.refresh_list()

    def on_empty_trash(self, btn):
        for note in self.db.all_trash():
            self.db.delete_permanently(note['id'])
        self.refresh_list()