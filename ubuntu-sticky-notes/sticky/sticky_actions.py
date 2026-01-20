"""Sticky note actions mixin module.

Provides database persistence, loading, serialization, and printing functionality
for sticky note windows.
"""

import json
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo


class StickyActions:
    """Mixin class providing persistence and action handlers for sticky notes.
    
    Handles database operations, content serialization with formatting tags,
    and print functionality.
    """

    def load_from_db(self):
        """Load note data from database and populate text buffer.
        
        Decodes hex-encoded JSON content with formatting tags and applies them
        to the text buffer. Restores window dimensions and color.
        """
        if not self.note_id:
            return

        row = self.db.get(self.note_id)
        if not row:
            return

        self._loading = True

        content = row["content"] or ""
        self.buffer.set_text("")

        try:
            segments = json.loads(bytes.fromhex(content).decode('utf-8'))
            iter_pos = self.buffer.get_start_iter()
            for seg in segments:
                text, tags = seg.get("text", ""), seg.get("tags", [])
                if tags:
                    self.buffer.insert_with_tags_by_name(iter_pos, text, *tags)
                else:
                    self.buffer.insert(iter_pos, text)
        except Exception:
            self.buffer.set_text(content.replace("<br>", "\n"))

        self.apply_color(row["color"] or "#FFF59D")
        self.saved_width = row['w'] or 300
        self.saved_height = row['h'] or 380

        self._loading = False

    def save(self):
        """Save note state to database.
        
        Serializes buffer content with formatting tags to hex-encoded JSON
        and persists window dimensions, color, and pin state.
        
        Returns:
            True to indicate operation completion.
        """
        if getattr(self, '_loading', True):
            return True

        try:
            hex_data = self._serialize_buffer()
            w = self.get_width() if self.get_visible() else self.saved_width
            h = self.get_height() if self.get_visible() else self.saved_height

            if self.note_id:
                self.db.update(
                    self.note_id,
                    hex_data,
                    0, 0,
                    w, h,
                    self.current_color,
                    1 if getattr(self, 'is_pinned', False) else 0
                )
                self.saved_width, self.saved_height = w, h

            if self.main_window:
                GLib.idle_add(self.main_window.refresh_list)
        except Exception as e:
            print(f"DEBUG: Save error: {e}")
        return True

    def _serialize_buffer(self):
        """Serialize text buffer with formatting tags to hex-encoded JSON.
        
        Returns:
            Hex-encoded JSON string containing text segments with their tags.
        """
        start_iter, end_iter = self.buffer.get_bounds()
        segments = []
        while not start_iter.equal(end_iter):
            next_iter = start_iter.copy()
            if not next_iter.forward_to_tag_toggle(None):
                next_iter = end_iter
            text = self.buffer.get_text(start_iter, next_iter, True)
            active_tags = [t.get_property("name") for t in start_iter.get_tags()]
            if text:
                segments.append({"text": text, "tags": active_tags})
            start_iter = next_iter
        if not segments:
            segments = [{"text": "", "tags": []}]
        return json.dumps(segments).encode('utf-8').hex()

    def on_print_clicked(self, _):
        """Initialize print operation for the note.
        
        Args:
            _: Widget that triggered the event (unused).
        """
        print_op = Gtk.PrintOperation()
        print_op.connect("draw-page", self._draw_page)
        print_op.set_n_pages(1)
        print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

    def _draw_page(self, operation, context, page_nr):
        """Render buffer content for printing.
        
        Args:
            operation: Print operation instance.
            context: Print context.
            page_nr: Page number being rendered.
        """
        cr = context.get_cairo_context()
        layout = context.create_pango_layout()
        start, end = self.buffer.get_bounds()
        layout.set_text(self.buffer.get_text(start, end, False), -1)
        layout.set_width(int(context.get_width() * Pango.SCALE))
        PangoCairo.show_layout(cr, layout)

    def _on_close_requested(self, window):
        """Handle window close request.
        
        Saves note data and removes window from main window's sticky list.
        
        Args:
            window: Window being closed.
            
        Returns:
            False to allow window destruction.
        """
        self.save()
        if self.main_window and self.note_id in self.main_window.stickies:
            del self.main_window.stickies[self.note_id]
        return False