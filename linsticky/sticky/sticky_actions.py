"""
Data Persistence and Action Mixin for StickyWindow.

This module provides methods for loading, saving, and printing note data.
It handles the serialization of the text buffer's content and formatting
into a JSON structure suitable for database storage.
"""
import json
from gi.repository import Gtk, GLib, Pango, PangoCairo
from .customization_dialog import CustomizationDialog


class StickyActions:
    """
    A mixin class for `StickyWindow` that encapsulates data-related actions
    like loading from DB, saving, and printing.
    """

    def load_from_db(self):
        """
        Fetches note data from the database and populates the UI.
        
        This method loads the note's content, color, and geometry, and applies
        them to the window. It supports both the modern JSON-based format and
        a legacy plain-text format for backward compatibility.
        """
        if not self.note_id:
            return

        row = self.db.get(self.note_id)
        if not row:
            print(f"WARNING: Note with ID {self.note_id} not found in database.")
            return

        self._loading = True

        content = row["content"] or ""
        self.buffer.set_text("")

        try:
            # New format: JSON string stored as a hex-encoded blob.
            segments = json.loads(bytes.fromhex(content).decode('utf-8'))
            iter_pos = self.buffer.get_start_iter()
            for seg in segments:
                text, tags = seg.get("text", ""), seg.get("tags", [])
                if tags:
                    self.buffer.insert_with_tags_by_name(iter_pos, text, *tags)
                else:
                    self.buffer.insert(iter_pos, text)
        except (ValueError, TypeError):
            # Fallback for legacy plain text format.
            self.buffer.set_text(content.replace("<br>", "\n"))

        # Restore window state.
        self.apply_color(row["color"] or "#FFF59D")
        self.saved_width = row['w'] or 300
        self.saved_height = row['h'] or 380
        self.saved_x = row['x'] or 300
        self.saved_y = row['y'] or 300

        self._loading = False

    def save(self, force: bool = False):
        """
        Saves the current state of the note (content, geometry, color) to the database.

        Args:
            force: If True, bypasses the check that prevents saving during destruction.
        """
        if not force and (getattr(self, '_is_destroying', False) or not self.get_native()):
            return False
        if getattr(self, '_loading', True):
            return True

        try:
            # Get the raw buffer data and encode it for database storage.
            segments = self._get_buffer_segments()
            hex_data = json.dumps(segments).encode('utf-8').hex()
            
            w = self.get_width() if self.get_visible() else self.saved_width
            h = self.get_height() if self.get_visible() else self.saved_height
            
            # Position is not reliably gettable in GTK4/Wayland, so we use the last known saved position.
            x, y = getattr(self, 'saved_x', 300), getattr(self, 'saved_y', 300)

            if self.note_id:
                self.db.update(
                    self.note_id, hex_data, x, y, w, h,
                    self.current_color, 1 if getattr(self, 'is_pinned', False) else 0
                )
                self.saved_width, self.saved_height = w, h
        except Exception as e:
            print(f"ERROR: Failed to save note {self.note_id}: {e}")
        return True

    def _get_buffer_segments(self) -> list:
        """
        Serializes the text buffer's content and tags into a list of dictionaries.

        Returns:
            A list of segments, where each segment is a dict with "text" and "tags".
        """
        start_iter, end_iter = self.buffer.get_bounds()
        segments = []
        while not start_iter.equal(end_iter):
            next_iter = start_iter.copy()
            if not next_iter.forward_to_tag_toggle(None):
                next_iter = end_iter
            text = self.buffer.get_text(start_iter, next_iter, True)
            active_tags = [t.get_property("name") for t in start_iter.get_tags() if t.get_property("name")]
            if text:
                segments.append({"text": text, "tags": active_tags})
            start_iter = next_iter
        if not segments:
            segments = [{"text": "", "tags": []}]
        
        return segments

    def on_print_clicked(self, _):
        """Initializes a print operation for the current note."""
        print_op = Gtk.PrintOperation()
        print_op.connect("draw-page", self._draw_page_for_printing)
        print_op.set_n_pages(1)
        print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

    def _draw_page_for_printing(self, operation, context, page_nr):
        """Renders the note's content into the print context."""
        cr = context.get_cairo_context()
        layout = context.create_pango_layout()
        start, end = self.buffer.get_bounds()
        layout.set_text(self.buffer.get_text(start, end, False), -1)
        layout.set_width(int(context.get_width() * Pango.SCALE))
        PangoCairo.show_layout(cr, layout)

    def on_customization_clicked(self, _):
        """Opens the customization dialog."""
        dialog = CustomizationDialog(self)
        dialog.present()

    def _on_close_requested(self, window) -> bool:
        """
        Handles data persistence and cleanup before the window is destroyed.

        Returns:
            True to confirm the close request has been handled.
        """
        self._is_destroying = True
        
        try:
            self.save(force=True)
        except Exception as e:
            print(f"ERROR: Final save on close failed for note {self.note_id}: {e}")
        
        if hasattr(self, 'save_timer_id') and self.save_timer_id:
            GLib.source_remove(self.save_timer_id)
            self.save_timer_id = None

        if self.main_window:
            self.main_window.on_sticky_closed(self.note_id)

        self.destroy()
        return True
