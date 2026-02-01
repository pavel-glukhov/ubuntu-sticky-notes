import builtins
from gi.repository import Gtk, Adw, Gio, Gdk
from config.config_manager import ConfigManager
from config.config import get_supported_languages

_ = builtins._

class SettingsView(Gtk.Box):
    """
    A Gtk.Box widget that serves as the settings interface for the application.
    Allows users to configure language, display backend, UI scale, database path,
    color palette, and formatting buttons visibility.
    """
    def __init__(self, on_back_callback, on_settings_change_callback=None):
        """
        Initializes the SettingsView.
        Args:
            on_back_callback (callable): Callback function to return to the main view.
            on_settings_change_callback (callable, optional): Callback function
                                                                to notify about settings changes. Defaults to None.
        """
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

        # --- Language Settings ---
        lang_row = Adw.ComboRow(title=_("Language"), subtitle=_("Requires app restart to take effect"))
        
        # Dynamically load supported languages
        supported_languages = get_supported_languages()
        
        # Ensure order is preserved for names and codes
        self.lang_names = []
        self.lang_codes = []
        for name, code in supported_languages.items():
            self.lang_names.append(_(name)) # Translate language names for display if possible
            self.lang_codes.append(code)
        
        self.lang_model = Gtk.StringList.new(self.lang_names)
        lang_row.set_model(self.lang_model)
        
        current_lang_code = self.config.get("language", "en")
        try:
            current_lang_index = self.lang_codes.index(current_lang_code)
            lang_row.set_selected(current_lang_index)
        except ValueError:
            lang_row.set_selected(0) # Default to English if not found
        
        list_box.append(lang_row)
        self.lang_row = lang_row
        # ------------------------

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

        # --- Palette Settings ---
        palette_expander = Adw.ExpanderRow(title=_("Color Palette"), subtitle=_("Customize sticker colors"))
        self.palette_buttons = []
        current_palette = self.config.get("palette", [])
        
        palette_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        palette_grid.set_margin_top(10); palette_grid.set_margin_bottom(10)
        palette_grid.set_margin_start(10); palette_grid.set_margin_end(10)
        palette_grid.set_halign(Gtk.Align.CENTER)

        for i, color in enumerate(current_palette):
            btn = Gtk.Button()
            btn.set_size_request(40, 40)
            self._set_button_color(btn, color)
            btn.connect("clicked", self.on_color_btn_clicked, i)
            self.palette_buttons.append(btn)
            palette_grid.attach(btn, i % 4, i // 4, 1, 1)
        
        palette_row = Adw.ActionRow()
        palette_row.add_suffix(palette_grid)
        palette_expander.add_row(palette_row)
        
        reset_row = Adw.ActionRow(title=_("Reset Palette"))
        btn_reset = Gtk.Button(label=_("Reset"), valign=Gtk.Align.CENTER)
        btn_reset.connect("clicked", self.on_reset_palette)
        reset_row.add_suffix(btn_reset)
        palette_expander.add_row(reset_row)

        list_box.append(palette_expander)
        # ------------------------

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

    def refresh_ui_from_config(self):
        """
        Reloads configuration from disk and updates UI elements to reflect external changes.
        This ensures synchronization if settings were changed via the sticker customization dialog.
        """
        self.config = ConfigManager.load()
        
        # Update formatting switches
        current_fmt = self.config.get("formatting", {})
        for key, switch in self.switches.items():
            switch.set_active(current_fmt.get(key, True))
            
        # Update palette buttons if needed (simplified check)
        current_palette = self.config.get("palette", [])
        for i, btn in enumerate(self.palette_buttons):
            if i < len(current_palette):
                self._set_button_color(btn, current_palette[i])

    def _set_button_color(self, btn, color):
        """
        Applies the given color to a Gtk.Button's background using CSS.
        Args:
            btn (Gtk.Button): The button widget to style.
            color (str): The hexadecimal color string (e.g., "#RRGGBB").
        """
        cp = Gtk.CssProvider()
        cp.load_from_data(f"button {{ background-color: {color}; border-radius: 50%; border: 1px solid rgba(0,0,0,0.2); }}".encode())
        btn.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def on_color_btn_clicked(self, btn, index: int):
        """
        Callback for when a color button in the palette is clicked.
        Opens a color selection dialog.
        Args:
            btn (Gtk.Button): The clicked button.
            index (int): The index of the color in the palette being edited.
        """
        try:
            dialog = Gtk.ColorDialog()
            dialog.choose_rgba(self.get_native(), None, None, self._on_color_chosen, index)
        except AttributeError:
            # Fallback for older GTK4 versions (before 4.10)
            dialog = Gtk.ColorChooserDialog(title=_("Select Color"), transient_for=self.get_native())
            dialog.set_use_alpha(False)
            
            current_hex = self.config["palette"][index]
            rgba = Gdk.RGBA()
            rgba.parse(current_hex)
            dialog.set_rgba(rgba)
            
            dialog.connect("response", self._on_color_chooser_response, index)
            dialog.show()

    def _on_color_chosen(self, dialog, result, index: int):
        """
        Callback for Gtk.ColorDialog.choose_rgba_finish.
        Updates the palette color and the button's appearance.
        Args:
            dialog (Gtk.ColorDialog): The color dialog instance.
            result (Gio.Task): The result of the color selection.
            index (int): The index of the color in the palette that was edited.
        """
        try:
            rgba = dialog.choose_rgba_finish(result)
            hex_color = f"#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}".upper()
            self.config["palette"][index] = hex_color
            self._set_button_color(self.palette_buttons[index], hex_color)
        except Exception as e:
            print(f"Color selection failed: {e}")

    def _on_color_chooser_response(self, dialog, response, index: int):
        """
        Callback for Gtk.ColorChooserDialog response.
        Updates the palette color and the button's appearance.
        Args:
            dialog (Gtk.ColorChooserDialog): The color chooser dialog instance.
            response (Gtk.ResponseType): The response from the dialog (e.g., OK, CANCEL).
            index (int): The index of the color in the palette that was edited.
        """
        if response == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            hex_color = f"#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}".upper()
            self.config["palette"][index] = hex_color
            self._set_button_color(self.palette_buttons[index], hex_color)
        dialog.destroy()

    def on_reset_palette(self, btn):
        """
        Resets the color palette to its default values.
        Args:
            btn (Gtk.Button): The clicked reset button.
        """
        # Get default palette from ConfigManager
        defaults = ConfigManager.get_defaults()
        self.config["palette"] = list(defaults["palette"])
        for i, btn in enumerate(self.palette_buttons):
            if i < len(self.config["palette"]):
                self._set_button_color(btn, self.config["palette"][i])

    def on_browse_db(self, btn):
        """
        Callback for the 'Browse' button to select a database file.
        Opens a file dialog.
        Args:
            btn (Gtk.Button): The clicked browse button.
        """
        dialog = Gtk.FileDialog(title=_("Select Database File"))
        db_filter = Gtk.FileFilter(); db_filter.set_name(_("Database files")); db_filter.add_pattern("*.db")
        filters = Gio.ListStore.new(Gtk.FileFilter); filters.append(db_filter)
        dialog.set_filters(filters)
        dialog.open(self.get_native(), None, self._on_browse_finish)

    def _on_browse_finish(self, dialog, result):
        """
        Callback for Gtk.FileDialog.open_finish.
        Sets the selected database path in the entry.
        Args:
            dialog (Gtk.FileDialog): The file dialog instance.
            result (Gio.Task): The result of the file selection.
        """
        try:
            file = dialog.open_finish(result)
            if file: self.db_entry.set_text(file.get_path())
        except Exception as e:
            print(f"ERROR: Could not get file path from dialog: {e}")

    def save_settings(self, _):
        """
        Saves the current settings to the configuration file.
        Triggers a restart dialog if critical settings (language, backend, db path, scale) have changed.
        """
        old_lang = self.config.get("language", "en")
        old_backend = self.config.get("backend", "wayland")
        old_db_path = self.config.get("db_path", "")
        old_ui_scale = self.config.get("ui_scale", 1.0)
        
        selected_lang_idx = self.lang_row.get_selected()
        new_lang = self.lang_codes[selected_lang_idx]
        self.config["language"] = new_lang

        new_backend = "wayland" if self.backend_dropdown.get_selected() == 0 else "x11"
        self.config["backend"] = new_backend
        
        new_db_path = self.db_entry.get_text()
        self.config["db_path"] = new_db_path
        
        try:
            new_ui_scale = round(float(self.scale_spin.get_value()), 2)
            self.config["ui_scale"] = new_ui_scale
        except (ValueError, TypeError):
            self.config["ui_scale"] = 1.0
            new_ui_scale = 1.0
            
        fmt_settings = {key: switch.get_active() for key, switch in self.switches.items()}
        self.config["formatting"] = fmt_settings

        ConfigManager.save(self.config)

        if self.on_settings_change_callback:
            self.on_settings_change_callback()
            
        if (old_lang != new_lang or 
            old_backend != new_backend or 
            old_db_path != new_db_path or 
            old_ui_scale != new_ui_scale):
            self.show_restart_dialog()

    def show_restart_dialog(self):
        """Displays a dialog informing the user that a restart is required."""
        dialog = Adw.MessageDialog(
            transient_for=self.get_native(),
            heading=_("Restart Required"),
            body=_("Some changes require an application restart to take full effect."),
        )
        dialog.add_response("ok", _("OK"))
        dialog.connect("response", lambda d, r: d.close())
        dialog.present()
