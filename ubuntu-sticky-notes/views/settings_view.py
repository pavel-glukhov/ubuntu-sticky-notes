import builtins
from gi.repository import Gtk, Adw, Gio
from config.config_manager import ConfigManager

_ = builtins._

class SettingsView(Gtk.Box):
    def __init__(self, on_back_callback, on_settings_change_callback=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.on_back_callback = on_back_callback
        self.on_settings_change_callback = on_settings_change_callback

        self.config = ConfigManager.load()

        if "formatting" not in self.config or not isinstance(self.config["formatting"], dict):
            self.config["formatting"] = {}

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_margin_top(10); header.set_margin_bottom(10)
        header.set_margin_start(10); header.set_margin_end(10)

        btn_back = Gtk.Button(label=_("<<- Back"))
        btn_back.connect("clicked", lambda _: self.on_back_callback())
        header.append(btn_back)

        lbl_title = Gtk.Label(label=_("Settings"))
        lbl_title.add_css_class("title-2")
        lbl_title.set_hexpand(True)
        header.append(lbl_title)
        self.append(header)

        content_scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(content_scroll)

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.set_margin_top(15); list_box.set_margin_bottom(15)
        list_box.set_margin_start(15); list_box.set_margin_end(15)
        list_box.add_css_class("boxed-list")
        content_scroll.set_child(list_box)

        lang_row = Adw.ComboRow(title=_("Language"), subtitle=_("Requires app restart to take effect"))
        self.lang_model = Gtk.StringList.new(["English", "Русский"])
        lang_row.set_model(self.lang_model)
        current_lang = self.config.get("language", "en")
        lang_row.set_selected(1 if current_lang == "ru" else 0)
        list_box.append(lang_row)
        self.lang_row = lang_row

        row_backend = Adw.ActionRow(title=_("Display Backend"), subtitle=_("Wayland (Default) or X11 (For sticker positioning)"))
        self.backend_dropdown = Gtk.DropDown.new_from_strings(["Wayland", "X11"])
        self.backend_dropdown.set_selected(0 if self.config.get("backend") == "wayland" else 1)
        self.backend_dropdown.set_valign(Gtk.Align.CENTER)
        row_backend.add_suffix(self.backend_dropdown)
        list_box.append(row_backend)

        row_scale = Adw.ActionRow(title=_("Interface Scale"), subtitle=_("Upscale UI elements and fonts (e.g. 1.25 = 125%)"))
        self.scale_spin = Gtk.SpinButton.new_with_range(0.5, 3.0, 0.05)
        try:
            clean_scale = float(str(self.config.get("ui_scale", 1.0))[:4])
        except (ValueError, TypeError):
            clean_scale = 1.0
        self.scale_spin.set_value(clean_scale)
        self.scale_spin.set_valign(Gtk.Align.CENTER)
        row_scale.add_suffix(self.scale_spin)
        list_box.append(row_scale)

        row_db = Adw.ActionRow(title=_("Database Path"))
        self.db_entry = Gtk.Entry(text=str(self.config.get("db_path", "")))
        self.db_entry.set_hexpand(True)
        self.db_entry.set_valign(Gtk.Align.CENTER)
        btn_browse = Gtk.Button(icon_name="folder-open-symbolic", valign=Gtk.Align.CENTER)
        btn_browse.connect("clicked", self.on_browse_db)
        row_db.add_suffix(self.db_entry)
        row_db.add_suffix(btn_browse)
        list_box.append(row_db)

        fmt_expander = Adw.ExpanderRow(title=_("Formatting Buttons"), subtitle=_("Choose which buttons to show on stickers"))
        self.switches = {}
        buttons_to_toggle = [
            ("bold", _("Bold (B)")), ("italic", _("Italic (I)")),
            ("underline", _("Underline (U)")), ("strikethrough", _("Strikethrough (S)")),
            ("list", _("Bullet List")),
            ("text_color", _("Text Color")), ("font_size", _("Font Size"))
        ]
        current_fmt = self.config["formatting"]
        for key, name in buttons_to_toggle:
            row = Adw.ActionRow(title=name)
            switch = Gtk.CheckButton(valign=Gtk.Align.CENTER)
            switch.set_active(current_fmt.get(key, True))
            row.add_suffix(switch)
            row.set_activatable_widget(switch)
            fmt_expander.add_row(row)
            self.switches[key] = switch
        list_box.append(fmt_expander)

        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20, margin_bottom=20, margin_start=20, margin_end=20)
        btn_save = Gtk.Button(label=_("Save Settings"), css_classes=["suggested-action"])
        btn_save.connect("clicked", self.save_settings)
        footer.append(btn_save)
        self.lbl_hint = Gtk.Label(label=_("Some changes may require a restart to apply."), css_classes=["caption"], margin_top=10)
        footer.append(self.lbl_hint)
        self.append(footer)

    def on_browse_db(self, btn):
        dialog = Gtk.FileDialog(title=_("Select Database File"))
        db_filter = Gtk.FileFilter(); db_filter.set_name(_("Database files")); db_filter.add_pattern("*.db")
        filters = Gio.ListStore.new(Gtk.FileFilter); filters.append(db_filter)
        dialog.set_filters(filters)
        dialog.open(self.get_native(), None, self._on_browse_finish)

    def _on_browse_finish(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file: self.db_entry.set_text(file.get_path())
        except Exception as e:
            print(f"ERROR: Could not get file path from dialog: {e}")

    def save_settings(self, _):
        old_lang = self.config.get("language", "en")
        
        selected_lang_idx = self.lang_row.get_selected()
        new_lang = "ru" if selected_lang_idx == 1 else "en"
        self.config["language"] = new_lang

        self.config["backend"] = "wayland" if self.backend_dropdown.get_selected() == 0 else "x11"
        self.config["db_path"] = self.db_entry.get_text()
        try:
            self.config["ui_scale"] = round(float(self.scale_spin.get_value()), 2)
        except (ValueError, TypeError):
            self.config["ui_scale"] = 1.0
            
        fmt_settings = {key: switch.get_active() for key, switch in self.switches.items()}
        self.config["formatting"] = fmt_settings

        ConfigManager.save(self.config)

        if self.on_settings_change_callback:
            self.on_settings_change_callback()

        if old_lang != new_lang:
            self.show_restart_dialog()

    def show_restart_dialog(self):
        dialog = Adw.MessageDialog(
            transient_for=self.get_native(),
            heading=_("Restart Required"),
            body=_("The language change will take full effect after you restart the application."),
        )
        dialog.add_response("ok", _("OK"))
        dialog.connect("response", lambda d, r: d.close())
        dialog.present()
