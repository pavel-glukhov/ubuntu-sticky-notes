from gi.repository import Gtk, Gdk

class StickyEvents:
    """
    Mixin class handling window events, gestures, and buffer updates for StickyWindow.
    """

    def _on_add_clicked(self, button):
        """
        Requests the main window to create a new note instance.
        Ensures the current window's design remains intact during the process.
        """
        if self.main_window:
            self.main_window.create_note()
            # Safety check to prevent UI design reset on the current instance
            self._update_ui_design()

    def _on_close_clicked(self, button):
        """
        Triggers a manual save before initiating the window close sequence.
        """
        self.save()
        self.close()

    def _on_resize_pressed(self, gesture, n_press, x, y):
        """
        Initiates a native window resize operation via Gdk Surface.
        Triggered by clicking the resize handle in the bottom-right corner.
        """
        surface = self.get_native().get_surface()
        if surface:
            size = int(16 * self.scale)
            window_x = self.get_width() - (size - x)
            window_y = self.get_height() - (size - y)
            device = gesture.get_device()
            surface.begin_resize(
                Gdk.SurfaceEdge.SOUTH_EAST,
                device,
                Gdk.BUTTON_PRIMARY,
                window_x,
                window_y,
                Gdk.CURRENT_TIME
            )

    def _on_header_drag_begin(self, gesture, x, y):
        """
        Begins a native window move operation when dragging the header.
        Stores drag offsets for legacy X11 support.
        """
        surface = self.get_native().get_surface()
        if surface:
            surface.begin_move(gesture.get_device(), Gdk.BUTTON_PRIMARY, x, y, Gdk.CURRENT_TIME)
            if self.is_x11():
                self._drag_offset_x, self._drag_offset_y = x, y

    def _on_header_drag_update(self, gesture, dx, dy):
        """
        Updates coordinate cache during dragging (X11 specific).
        """
        if self.is_x11():
            self.last_x = int(self.saved_x + dx)
            self.last_y = int(self.saved_y + dy)

    def _on_header_drag_end(self, gesture, dx, dy):
        """
        Finalizes coordinate updates after dragging (X11 specific).
        """
        if self.is_x11():
            self.saved_x = getattr(self, "last_x", 0)
            self.saved_y = getattr(self, "last_y", 0)

    def _on_map(self, widget):
        """
        Restores the saved window dimensions when the widget is mapped to the screen.
        """
        if self.saved_width > 0 and self.saved_height > 0:
            self.set_default_size(self.saved_width, self.saved_height)

    def _on_buffer_changed(self, buffer):
        """
        Handles real-time updates when the text buffer is modified.
        Pushes updated content to the main window preview cards.
        """
        if not getattr(self, '_loading', True):
            if self.main_window:
                # Serialize current buffer content
                content = self._serialize_buffer()
                # Direct push notification to the main UI list
                self.main_window.update_card_text(self.note_id, content)