"""About dialog for GTK/libadwaita UI."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import os
import json
from core.config import PROJECT_ROOT


class AboutDialog(Adw.Dialog):
    def __init__(self, parent: Gtk.Window | None = None, **kwargs):
        super().__init__(transient_for=parent, **kwargs)
        
        # Load UI from file
        builder = Gtk.Builder()
        ui_file = os.path.join(PROJECT_ROOT, "resources", "gtk", "ui", "about_dialog.ui")
        builder.add_from_file(ui_file)
        
        # Get widgets from builder
        self.label_title = builder.get_object("label_title")
        self.label_info = builder.get_object("label_info")
        self.label_description = builder.get_object("label_description")
        
        # Get the UI dialog and extract its content
        ui_dialog = builder.get_object("AboutDialog")
        content_box = builder.get_object("content_box")
        
        # Remove content_box from ui_dialog before setting it to our dialog
        if ui_dialog and content_box:
            ui_dialog.set_child(None)
        
        # Set dialog content
        self.set_child(content_box)
        
        info = self._load_info()
        app = info.get("app_name", "Ubuntu Sticky Notes")
        ver = info.get("version", "")
        author = info.get("author", "")
        email = info.get("email", "")
        website = info.get("website", "")
        desc = info.get("description", "")

        self.label_title.set_markup(f"<b>{app}</b>")
        self.label_info.set_text(f"Version {ver}\n{author} <{email}>\n{website}")
        self.label_description.set_text(desc)

    def _load_info(self) -> dict:
        try:
            with open(os.path.join(PROJECT_ROOT, "src", "core", "app_info.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
