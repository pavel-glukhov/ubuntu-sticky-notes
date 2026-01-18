from gi.repository import Gtk, Adw, Gio
from config.config_manager import ConfigManager


class SettingsView(Gtk.Box):
    def __init__(self, on_back_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.on_back_callback = on_back_callback
        self.config = ConfigManager.load()

        # --- Header ---
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_margin_start(10)
        header.set_margin_end(10)

        btn_back = Gtk.Button(label="<<- Back")
        btn_back.connect("clicked", lambda _: self.on_back_callback())
        header.append(btn_back)

        lbl_title = Gtk.Label(label="Settings")
        lbl_title.add_css_class("title-2")
        lbl_title.set_hexpand(True)
        header.append(lbl_title)
        self.append(header)

        # --- Content Container ---
        content_scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(content_scroll)

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.set_margin_top(15)
        list_box.set_margin_bottom(15)
        list_box.set_margin_start(15)
        list_box.set_margin_end(15)
        list_box.add_css_class("boxed-list")
        content_scroll.set_child(list_box)

        # Row 1: Backend (Wayland / X11)
        row_backend = Adw.ActionRow(
            title="Display Backend",
            subtitle="Wayland (Default) or X11 (For sticker positioning)"
        )
        self.backend_dropdown = Gtk.DropDown.new_from_strings(["Wayland", "X11"])
        self.backend_dropdown.set_selected(0 if self.config.get("backend") == "wayland" else 1)
        self.backend_dropdown.set_valign(Gtk.Align.CENTER)
        row_backend.add_suffix(self.backend_dropdown)
        list_box.append(row_backend)

        # Row 2: DB Path
        row_db = Adw.ActionRow(title="Database Path")
        self.db_entry = Gtk.Entry(text=self.config.get("db_path", ""))
        self.db_entry.set_hexpand(True)
        self.db_entry.set_valign(Gtk.Align.CENTER)

        btn_browse = Gtk.Button(icon_name="folder-open-symbolic")
        btn_browse.set_valign(Gtk.Align.CENTER)
        btn_browse.connect("clicked", self.on_browse_db)

        row_db.add_suffix(self.db_entry)
        row_db.add_suffix(btn_browse)
        list_box.append(row_db)

        # --- Save Button ---
        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        footer.set_margin_top(20)
        footer.set_margin_bottom(20)
        footer.set_margin_start(20)
        footer.set_margin_end(20)

        btn_save = Gtk.Button(label="Save Settings")
        btn_save.add_css_class("suggested-action")
        btn_save.connect("clicked", self.save_settings)
        footer.append(btn_save)

        lbl_hint = Gtk.Label(label="Changes require application restart")
        lbl_hint.add_css_class("caption")
        lbl_hint.set_margin_top(10)
        footer.append(lbl_hint)

        self.append(footer)

    def on_browse_db(self, btn):
        dialog = Gtk.FileDialog(title="Select Database File")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        db_filter = Gtk.FileFilter()
        db_filter.set_name("Database files")
        db_filter.add_pattern("*.db")
        filters.append(db_filter)
        dialog.set_filters(filters)

        def callback(dialog, result):
            try:
                file = dialog.open_finish(result)
                if file:
                    self.db_entry.set_text(file.get_path())
            except:
                pass

        dialog.open(self.get_native(), None, callback)

    def save_settings(self, _):
        new_backend = "wayland" if self.backend_dropdown.get_selected() == 0 else "x11"
        self.config["backend"] = new_backend
        self.config["db_path"] = self.db_entry.get_text()

        ConfigManager.save(self.config)

        print("Settings saved to usn.conf")