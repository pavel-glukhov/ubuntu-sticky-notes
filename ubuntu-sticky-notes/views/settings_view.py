"""Settings view module for Ubuntu Sticky Notes.

Provides a settings interface for configuring display backend, UI scaling,
database location, and formatting toolbar customization.
"""

from gi.repository import Gtk, Adw, Gio, Gdk
from config.config_manager import ConfigManager


class SettingsView(Gtk.Box):
    """Settings view for application configuration.
    
    Provides UI for configuring backend, UI scale, database path, and
    formatting toolbar options. Changes can be applied without restart.
    
    Attributes:
        on_back_callback: Function to call when back button is clicked.
        on_settings_change_callback: Function to call after settings are saved.
        config: Current configuration dictionary.
        switches: Dictionary mapping formatting option keys to CheckButtons.
    """
    
    def __init__(self, on_back_callback, on_settings_change_callback=None):
        """Initialize the settings view.
        
        Args:
            on_back_callback: Function to call when returning to main view.
            on_settings_change_callback: Optional function to call after saving.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.on_back_callback = on_back_callback
        self.on_settings_change_callback = on_settings_change_callback

        self.config = ConfigManager.load()

        if "formatting" not in self.config or not isinstance(self.config["formatting"], dict):
            print("DEBUG: Formatting config was missing or corrupted. Resetting to defaults.")
            self.config["formatting"] = {}

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_margin_top(10);
        header.set_margin_bottom(10)
        header.set_margin_start(10);
        header.set_margin_end(10)

        btn_back = Gtk.Button(label="<<- Back")
        btn_back.connect("clicked", lambda _: self.on_back_callback())
        header.append(btn_back)

        lbl_title = Gtk.Label(label="Settings")
        lbl_title.add_css_class("title-2")
        lbl_title.set_hexpand(True)
        header.append(lbl_title)
        self.append(header)

        content_scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(content_scroll)

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.set_margin_top(15);
        list_box.set_margin_bottom(15)
        list_box.set_margin_start(15);
        list_box.set_margin_end(15)
        list_box.add_css_class("boxed-list")
        content_scroll.set_child(list_box)

        row_backend = Adw.ActionRow(
            title="Display Backend",
            subtitle="Wayland (Default) or X11 (For sticker positioning)"
        )
        self.backend_dropdown = Gtk.DropDown.new_from_strings(["Wayland", "X11"])
        self.backend_dropdown.set_selected(0 if self.config.get("backend") == "wayland" else 1)
        self.backend_dropdown.set_valign(Gtk.Align.CENTER)
        row_backend.add_suffix(self.backend_dropdown)
        list_box.append(row_backend)

        row_scale = Adw.ActionRow(
            title="Interface Scale",
            subtitle="Upscale UI elements and fonts (e.g. 1.25 = 125%)"
        )
        self.scale_spin = Gtk.SpinButton.new_with_range(0.5, 3.0, 0.05)
        raw_scale = self.config.get("ui_scale", 1.0)
        try:
            clean_scale = float(str(raw_scale)[:4])
        except (ValueError, TypeError):
            clean_scale = 1.0
        self.scale_spin.set_value(clean_scale)
        self.scale_spin.set_valign(Gtk.Align.CENTER)
        row_scale.add_suffix(self.scale_spin)
        list_box.append(row_scale)

        row_db = Adw.ActionRow(title="Database Path")
        self.db_entry = Gtk.Entry(text=str(self.config.get("db_path", "")))
        self.db_entry.set_hexpand(True)
        self.db_entry.set_valign(Gtk.Align.CENTER)
        btn_browse = Gtk.Button(icon_name="folder-open-symbolic")
        btn_browse.set_valign(Gtk.Align.CENTER)
        btn_browse.connect("clicked", self.on_browse_db)
        row_db.add_suffix(self.db_entry)
        row_db.add_suffix(btn_browse)
        list_box.append(row_db)

        fmt_expander = Adw.ExpanderRow(title="Formatting Buttons", subtitle="Choose which buttons to show on stickers")

        self.switches = {}

        buttons_to_toggle = [
            ("bold", "Bold (B)"),
            ("italic", "Italic (I)"),
            ("underline", "Underline (U)"),
            ("strikethrough", "Strikethrough (S)"),
            ("list", "Bullet List"),
            ("text_color", "Text Color"),
            ("font_size", "Font Size")
        ]

        current_fmt = self.config["formatting"]

        for key, name in buttons_to_toggle:
            row = Adw.ActionRow(title=name)

            switch = Gtk.CheckButton()
            switch.set_valign(Gtk.Align.CENTER)

            is_active = current_fmt.get(key, True)
            switch.set_active(is_active)

            row.add_suffix(switch)

            row.set_activatable_widget(switch)

            fmt_expander.add_row(row)
            self.switches[key] = switch

        list_box.append(fmt_expander)

        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        footer.set_margin_top(20);
        footer.set_margin_bottom(20)
        footer.set_margin_start(20);
        footer.set_margin_end(20)

        btn_save = Gtk.Button(label="Save Settings")
        btn_save.add_css_class("suggested-action")
        btn_save.connect("clicked", self.save_settings)
        footer.append(btn_save)

        lbl_hint = Gtk.Label(label="Changes apply immediately")
        lbl_hint.add_css_class("caption")
        lbl_hint.set_margin_top(10)
        footer.append(lbl_hint)

        self.append(footer)

    def on_browse_db(self, btn):
        """Open file dialog to browse for database file.
        
        Args:
            btn: The button that triggered this callback.
        """
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
        """Save all settings to configuration file.
        
        Collects values from all UI elements, validates them, saves to
        ConfigManager, and triggers the settings change callback.
        
        Args:
            _: The button that triggered this callback (unused).
        """
        print("DEBUG: Saving settings process started...")

        new_backend = "wayland" if self.backend_dropdown.get_selected() == 0 else "x11"
        new_db_path = self.db_entry.get_text()

        try:
            new_scale = float(self.scale_spin.get_value())
            final_scale = round(new_scale, 2)
        except:
            final_scale = 1.0

        self.config["backend"] = new_backend
        self.config["db_path"] = new_db_path
        self.config["ui_scale"] = final_scale

        fmt_settings = {}
        for key, switch in self.switches.items():
            state = switch.get_active()
            fmt_settings[key] = state

        self.config["formatting"] = fmt_settings

        print(f"DEBUG: Data to save: Scale={final_scale}, Formatting={fmt_settings}")

        try:
            ConfigManager.save(self.config)
            print("DEBUG: ConfigManager.save() called successfully.")
        except Exception as e:
            print(f"ERROR: Failed to save config: {e}")

        if self.on_settings_change_callback:
            self.on_settings_change_callback()