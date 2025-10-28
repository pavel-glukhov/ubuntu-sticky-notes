"""Sticky note window (GTK4/libadwaita).

Current scope:
- Plain-text editing via Gtk.TextView
- Autosave to SQLite (using existing NotesDB API)
- Pin button persists a flag (visual only for now)

Follow-ups: apply window keep-above (if available on GTK4/WM), rich text.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

import os
from core.config import AUTOSAVE_INTERVAL_MS, COLOR_MAP, PROJECT_ROOT


class StickyWindow(Adw.ApplicationWindow):
    def __init__(self, transient_for, db, note_id=None, **kwargs):
        super().__init__(transient_for=transient_for, **kwargs)
        
        # Load UI from file
        builder = Gtk.Builder()
        ui_file = os.path.join(PROJECT_ROOT, "resources", "gtk", "ui", "sticky_window.ui")
        builder.add_from_file(ui_file)
        
        # Get widgets from builder
        self.text_view = builder.get_object("text_view")
        self.btn_close = builder.get_object("btn_close")
        self.btn_pin = builder.get_object("btn_pin")
        
        # Get the UI window and extract its content
        ui_window = builder.get_object("StickyWindow")
        main_box = builder.get_object("main_box")
        
        # Remove main_box from ui_window before setting it to our window
        if ui_window and main_box:
            ui_window.set_child(None)
        
        # Set up the window content
        self.set_content(main_box)
        self.set_default_size(320, 240)
        
        self.db = db
        self.note_id = note_id

        self._buffer: Gtk.TextBuffer = self.text_view.get_buffer()
        self._always_on_top = 0
        self._color = COLOR_MAP.get("Yellow", "#FFF59D")

        self.btn_close.connect("clicked", self._on_close_clicked)
        self.btn_pin.connect("clicked", self._on_pin_clicked)

        if self.note_id:
            self._load_from_db()

        # Start autosave timer
        GLib.timeout_add(AUTOSAVE_INTERVAL_MS, self._autosave)

        # Mark open
        if self.note_id:
            try:
                self.db.set_open_state(self.note_id, 1)
            except Exception:
                pass

    def _load_from_db(self):
        try:
            row = self.db.get(self.note_id)
        except Exception:
            row = None
        if row:
            content = row["content"] or ""
            self._buffer.set_text(content)
            self._color = row.get("color", self._color) if isinstance(row, dict) else (row["color"] if "color" in row.keys() else self._color)
            self._always_on_top = int(row["always_on_top"]) if "always_on_top" in row.keys() else 0
            self._apply_color(self._color)

    def _apply_color(self, hex_color: str):
        # Basic background via CSS on TextView
        css = f"textview {{ background-color: {hex_color}; }}"
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode("utf-8"))
        self.text_view.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def _on_close_clicked(self, *_):
        self._save_now()
        if self.note_id:
            try:
                self.db.set_open_state(self.note_id, 0)
            except Exception:
                pass
        self.close()

    def _on_pin_clicked(self, *_):
        # Toggle persisted flag (visual only for now; keep-above integration TBD)
        self._always_on_top = 0 if self._always_on_top else 1
        self._save_now()

    def _autosave(self):
        self._save_now()
        return True

    def _save_now(self):
        start, end = self._buffer.get_bounds()
        content = self._buffer.get_text(start, end, True)
        try:
            if self.note_id:
                # We don't track x/y/w/h here yet; keep previous values
                row = self.db.get(self.note_id)
                if row:
                    x, y, w, h = row["x"], row["y"], row["w"], row["h"]
                    self.db.update(self.note_id, content, x, y, w, h, self._color, self._always_on_top)
            else:
                # Create a new record with minimal geometry; can be updated later
                self.note_id = self.db.add(None, content, 300, 200, 320, 240, self._color, self._always_on_top)
                try:
                    self.db.set_open_state(self.note_id, 1)
                except Exception:
                    pass
        except Exception:
            # Keep UI responsive even if DB layer is not ready yet
            pass
