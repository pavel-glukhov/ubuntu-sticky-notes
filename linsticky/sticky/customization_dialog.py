import builtins
from gi.repository import Gtk, Adw
from config.config_manager import ConfigManager

# Ensure fallback for translation
if not hasattr(builtins, "_"):
    builtins._ = lambda s: s

class CustomizationDialog(Gtk.Window):
    """
    A modal dialog allowing the user to toggle visibility of formatting buttons.
    """
    def __init__(self, parent_window):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_title(builtins._("Customization"))
        self.set_default_size(300, 400)
        self.set_resizable(False)
        
        # Use Adw.Window styling if available via CSS classes, 
        # but Gtk.Window is safer for simple modals inside the app structure.
        self.add_css_class("dialog")

        self.parent_window = parent_window
        self.config = ConfigManager.load()
        self.formatting_config = self.config.get("formatting", {}).copy()

        # Main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        self.set_child(vbox)

        # Title
        lbl_title = Gtk.Label(label=builtins._("Toolbar Options"))
        lbl_title.add_css_class("title-4")
        lbl_title.set_halign(Gtk.Align.START)
        vbox.append(lbl_title)

        # Options List
        # Map config keys to display labels
        options = [
            ("bold", builtins._("Bold")),
            ("italic", builtins._("Italic")),
            ("underline", builtins._("Underline")),
            ("strikethrough", builtins._("Strikethrough")),
            ("list", builtins._("Bullet List")),
            ("text_color", builtins._("Text Color")),
            ("font_size", builtins._("Font Size")),
        ]

        list_box = Gtk.ListBox()
        list_box.add_css_class("boxed-list")
        vbox.append(list_box)

        self.switches = {}

        for key, label_text in options:
            row = Adw.ActionRow()
            row.set_title(label_text)
            
            switch = Gtk.Switch()
            switch.set_active(self.formatting_config.get(key, True))
            switch.set_valign(Gtk.Align.CENTER)
            
            # Connect signal to update local config immediately on toggle
            switch.connect("state-set", self._on_switch_toggled, key)
            
            row.add_suffix(switch)
            list_box.append(row)
            self.switches[key] = switch

        # Save Button
        btn_save = Gtk.Button(label=builtins._("Save & Apply"))
        btn_save.add_css_class("suggested-action")
        btn_save.add_css_class("pill")
        btn_save.connect("clicked", self._on_save_clicked)
        vbox.append(btn_save)

    def _on_switch_toggled(self, switch, state, key):
        self.formatting_config[key] = state
        return False # Propagate event

    def _on_save_clicked(self, button):
        """Saves configuration and triggers update in the main application."""
        # Update the main config dictionary
        self.config["formatting"] = self.formatting_config
        
        # Save to disk
        ConfigManager.save(self.config)
        
        # Trigger update in the main window to refresh all open notes
        if self.parent_window.main_window:
            self.parent_window.main_window.reload_configuration()
        
        self.close()
