"""
Event and Gesture Handling for StickyWindow.

This module contains the mixin class responsible for handling all user
interactions with a sticky note, including button clicks, drag-and-drop
for moving, resizing gestures, and keyboard shortcuts.
"""
from gi.repository import Gtk, Gdk


class StickyEvents:
    """
    A mixin for `StickyWindow` that handles UI events, gestures, and signals.
    """

    def _on_add_clicked(self, button: Gtk.Button):
        """
        Handles the 'add new note' button click by delegating to the main window.
        """
        if self.main_window:
            self.main_window.create_note()
        # Re-apply design to the current window as a safeguard against any
        # potential style context changes triggered by creating a new window.
        self._update_ui_design()

    def _on_close_clicked(self, button: Gtk.Button):
        """
        Handles the 'close' button click, ensuring the note is saved before closing.
        """
        self.save()
        self.close()

    def _on_resize_pressed(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float):
        """
        Initiates a native window resize operation when the resize handle is clicked.
        """
        surface = self.get_native().get_surface()
        if not surface:
            return
            
        size = int(16 * self.scale)
        window_x = self.get_width() - (size - x)
        window_y = self.get_height() - (size - y)
        
        surface.begin_resize(
            Gdk.SurfaceEdge.SOUTH_EAST,
            gesture.get_device(),
            Gdk.BUTTON_PRIMARY,
            window_x,
            window_y,
            Gdk.CURRENT_TIME
        )

    def _on_header_drag_begin(self, gesture: Gtk.GestureDrag, x: float, y: float):
        """
        Begins a native window move operation when the header area is dragged.
        """
        surface = self.get_native().get_surface()
        if surface:
            surface.begin_move(gesture.get_device(), Gdk.BUTTON_PRIMARY, x, y, Gdk.CURRENT_TIME)

    def _on_header_drag_update(self, gesture: Gtk.GestureDrag, dx: float, dy: float):
        """
        Updates the note's position coordinates during a drag operation.
        This is primarily for X11 compatibility where continuous updates are needed.
        """
        if "X11" in Gdk.Display.get_default().__class__.__name__:
            self.saved_x += dx
            self.saved_y += dy

    def _on_header_drag_end(self, gesture: Gtk.GestureDrag, dx: float, dy: float):
        """
        Finalizes the note's position after a drag operation is complete.
        """
        # The final position is implicitly handled by the window manager in Wayland.
        # For X11, the continuous updates in `_on_header_drag_update` are sufficient.
        # This method is kept for potential future logic.
        pass

    def _on_map(self, widget: Gtk.Widget):
        """
        Restores the window's saved size when it is first displayed (mapped).
        """
        if self.saved_width > 0 and self.saved_height > 0:
            self.set_default_size(self.saved_width, self.saved_height)

    def _on_buffer_changed(self, buffer: Gtk.TextBuffer):
        """
        Handles the 'changed' signal from the text buffer to update the main
        window's preview card in real-time.
        """
        if not getattr(self, '_loading', True) and self.main_window:
            # Pass the raw segment data for real-time preview generation.
            segments = self._get_buffer_segments()
            self.main_window.update_card_text(self.note_id, segments)

    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        """
        Handles keyboard shortcuts for text formatting (e.g., Ctrl+B for bold).
        """
        ctrl_pressed = (state & Gdk.ModifierType.CONTROL_MASK)
        shift_pressed = (state & Gdk.ModifierType.SHIFT_MASK)

        if not ctrl_pressed:
            return False

        key_map = {
            (Gdk.KEY_B, Gdk.KEY_b): "bold",
            (Gdk.KEY_I, Gdk.KEY_i): "italic",
            (Gdk.KEY_U, Gdk.KEY_u): "underline",
        }
        shift_key_map = {
            (Gdk.KEY_S, Gdk.KEY_s): "strikethrough",
        }

        if shift_pressed:
            for keys, format_tag in shift_key_map.items():
                if keyval in keys:
                    self.apply_format(format_tag)
                    return True
            if keyval in (Gdk.KEY_L, Gdk.KEY_l):
                self.toggle_bullet_list()
                return True
        else:
            for keys, format_tag in key_map.items():
                if keyval in keys:
                    self.apply_format(format_tag)
                    return True

        return False
