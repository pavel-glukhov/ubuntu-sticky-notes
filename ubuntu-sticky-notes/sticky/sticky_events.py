from gi.repository import Gtk, Gdk


class StickyEvents:
    """
    Mixin class handling window events, gestures, and buffer updates for StickyWindow.
    """

    def _on_add_clicked(self, button: Gtk.Button):
        """
        Requests the main window to create a new note instance.
        Ensures the current window's design remains intact during the process.
        Args:
            button (Gtk.Button): The clicked button.
        """
        if self.main_window:
            self.main_window.create_note()
            # Safety check to prevent UI design reset on the current instance
            self._update_ui_design()

    def _on_close_clicked(self, button: Gtk.Button):
        """
        Triggers a manual save before initiating the window close sequence.
        Args:
            button (Gtk.Button): The clicked button.
        """
        self.save()
        self.close()

    def _on_resize_pressed(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float):
        """
        Initiates a native window resize operation via Gdk Surface.
        Triggered by clicking the resize handle in the bottom-right corner.
        Args:
            gesture (Gtk.GestureClick): The gesture instance.
            n_press (int): Number of presses.
            x (float): X-coordinate of the press.
            y (float): Y-coordinate of the press.
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

    def _on_header_drag_begin(self, gesture: Gtk.GestureDrag, x: float, y: float):
        """
        Begins a native window move operation when dragging the header.
        Stores drag offsets for legacy X11 support.
        Args:
            gesture (Gtk.GestureDrag): The gesture instance.
            x (float): X-coordinate of the drag start.
            y (float): Y-coordinate of the drag start.
        """
        surface = self.get_native().get_surface()
        if surface:
            surface.begin_move(gesture.get_device(), Gdk.BUTTON_PRIMARY, x, y, Gdk.CURRENT_TIME)
            if self.is_x11():
                self._drag_offset_x, self._drag_offset_y = x, y

    def _on_header_drag_update(self, gesture: Gtk.GestureDrag, dx: float, dy: float):
        """
        Updates coordinate cache during dragging (X11 specific).
        Args:
            gesture (Gtk.GestureDrag): The gesture instance.
            dx (float): Change in X-coordinate.
            dy (float): Change in Y-coordinate.
        """
        if self.is_x11():
            self.last_x = int(self.saved_x + dx)
            self.last_y = int(self.saved_y + dy)

    def _on_header_drag_end(self, gesture: Gtk.GestureDrag, dx: float, dy: float):
        """
        Finalizes coordinate updates after dragging (X11 specific).
        Args:
            gesture (Gtk.GestureDrag): The gesture instance.
            dx (float): Total change in X-coordinate.
            dy (float): Total change in Y-coordinate.
        """
        if self.is_x11():
            self.saved_x = getattr(self, "last_x", 0)
            self.saved_y = getattr(self, "last_y", 0)

    def _on_map(self, widget: Gtk.Widget):
        """
        Restores the saved window dimensions when the widget is mapped to the screen.
        Args:
            widget (Gtk.Widget): The widget that emitted the signal.
        """
        if self.saved_width > 0 and self.saved_height > 0:
            self.set_default_size(self.saved_width, self.saved_height)

    def _on_buffer_changed(self, buffer: Gtk.TextBuffer):
        """
        Handles real-time updates when the text buffer is modified.
        Pushes updated content to the main window preview cards.
        Args:
            buffer (Gtk.TextBuffer): The text buffer that changed.
        """
        if not getattr(self, '_loading', True):
            if self.main_window:
                content = self._serialize_buffer()
                self.main_window.update_card_text(self.note_id, content)
