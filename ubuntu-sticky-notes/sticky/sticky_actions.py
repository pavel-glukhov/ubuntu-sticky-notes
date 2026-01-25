import json
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo


class StickyActions:
    """
    Mixin class providing persistence, database loading, and printing actions.
    """

    def load_from_db(self):
        """
        Fetches note data from the database and populates the text buffer and UI.
        """
        if not self.note_id:
            return

        row = self.db.get(self.note_id)
        if not row:
            return

        # Block saving signals during initial data load
        self._loading = True

        content = row["content"] or ""
        self.buffer.set_text("")

        try:
            # Decode hex-encoded JSON content and apply tags
            segments = json.loads(bytes.fromhex(content).decode('utf-8'))
            iter_pos = self.buffer.get_start_iter()
            for seg in segments:
                text, tags = seg.get("text", ""), seg.get("tags", [])
                if tags:
                    self.buffer.insert_with_tags_by_name(iter_pos, text, *tags)
                else:
                    self.buffer.insert(iter_pos, text)
        except Exception:
            # Fallback for legacy plain text format
            self.buffer.set_text(content.replace("<br>", "\n"))

        # Restore window state: color and dimensions
        self.apply_color(row["color"] or "#FFF59D")
        self.saved_width = row['w'] or 300
        self.saved_height = row['h'] or 380

        self._loading = False

    def save(self):
        """
        Saves the current state of the note to the database.
        """
        # Prevent saving if window is being destroyed or already destroyed
        if getattr(self, '_is_destroying', False) or not self.get_native():
            return False

        if getattr(self, '_loading', True):
            return True

        try:
            # Get serialized segments (JSON object)
            serialized_segments = self._serialize_buffer()
            # Encode to hex string for DB storage
            hex_data = json.dumps(serialized_segments).encode('utf-8').hex()

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

        except Exception as e:
            print(f"ERROR: Save error: {e}")
        return True

    def _serialize_buffer(self):
        """Serializes text buffer and tags into a list of dictionaries (JSON object)."""
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
        """Initializes a print operation for the note."""
        print_op = Gtk.PrintOperation()
        print_op.connect("draw-page", self._draw_page)
        print_op.set_n_pages(1)
        print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

    def _draw_page(self, operation, context, page_nr):
        """Renders the buffer content for printing."""
        cr = context.get_cairo_context()
        layout = context.create_pango_layout()
        start, end = self.buffer.get_bounds()
        layout.set_text(self.buffer.get_text(start, end, False), -1)
        layout.set_width(int(context.get_width() * Pango.SCALE))
        PangoCairo.show_layout(cr, layout)

    def _on_close_requested(self, window):
        """Handles data persistence before window destruction."""
        # Mark as destroying to prevent further saves
        self._is_destroying = True
        
        # Perform one last save
        try:
            # Revert flag setting for a moment to allow this save
            self._is_destroying = False
            self.save()
            self._is_destroying = True
            
        except Exception as e:
            print(f"Error saving on close: {e}")
        
        # Stop the auto-save timer if it exists
        if hasattr(self, 'save_timer_id') and self.save_timer_id:
            GLib.source_remove(self.save_timer_id)
            self.save_timer_id = None

        # Notify main window that we are closing
        if self.main_window:
            self.main_window.on_sticky_closed(self.note_id)

        # Explicitly destroy the window to stop timers and free resources
        self.destroy()
        return True # Indicate that the close request has been handled
