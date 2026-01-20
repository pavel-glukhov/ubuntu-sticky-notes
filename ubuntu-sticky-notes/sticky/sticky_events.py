"""Event handling module for sticky note windows.

This module provides event handlers for sticky note windows including
window events, drag gestures, resize operations, and text buffer updates.
"""

from gi.repository import Gtk, Gdk

class StickyEvents:
    """
    Mixin class handling window events, gestures, and buffer updates for StickyWindow.
    
    This class provides event handling functionality for sticky note windows,
    including:
    - Window creation and closure events
    - Drag and resize gesture handling
    - Text buffer change notifications
    - Window mapping and positioning
    
    This class is designed to be used as a mixin with StickyWindow and should
    not be instantiated directly.
    """

    def _on_add_clicked(self, button):
        """
        Handle the add button click event to create a new sticky note.
        
        Requests the main window to create a new note instance and ensures
        that the current window's UI design remains intact during the process.
        This prevents any unwanted UI resets on the existing note window.
        
        Args:
            button (Gtk.Button): The button widget that triggered the event.
        """
        if self.main_window:
            self.main_window.create_note()
            # Safety check to prevent UI design reset on the current instance
            self._update_ui_design()

    def _on_close_clicked(self, button):
        """
        Handle the close button click event.
        
        Triggers a manual save operation before initiating the window close
        sequence to ensure that all changes are persisted to the database.
        
        Args:
            button (Gtk.Button): The button widget that triggered the event.
        """
        self.save()
        self.close()

    def _on_resize_pressed(self, gesture, n_press, x, y):
        """
        Handle the resize gesture press event.
        
        Initiates a native window resize operation via Gdk Surface when the
        user clicks on the resize handle in the bottom-right corner of the
        sticky note window. Calculates the appropriate window coordinates
        based on the current scale factor.
        
        Args:
            gesture (Gtk.GestureClick): The gesture recognizer that detected the press.
            n_press (int): The number of press events (1 for single click, 2 for double, etc.).
            x (float): The X coordinate of the press relative to the widget.
            y (float): The Y coordinate of the press relative to the widget.
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
        Handle the beginning of a header drag gesture.
        
        Begins a native window move operation when the user starts dragging
        the header area of the sticky note. For X11 display servers, stores
        the drag offsets to support legacy window positioning.
        
        Args:
            gesture (Gtk.GestureDrag): The gesture recognizer tracking the drag.
            x (float): The initial X coordinate where the drag started.
            y (float): The initial Y coordinate where the drag started.
        """
        surface = self.get_native().get_surface()
        if surface:
            surface.begin_move(gesture.get_device(), Gdk.BUTTON_PRIMARY, x, y, Gdk.CURRENT_TIME)
            if self.is_x11():
                self._drag_offset_x, self._drag_offset_y = x, y

    def _on_header_drag_update(self, gesture, dx, dy):
        """
        Handle drag gesture updates during window movement.
        
        Updates the coordinate cache as the window is being dragged. This
        method is specific to X11 display servers and maintains accurate
        position tracking during the drag operation.
        
        Args:
            gesture (Gtk.GestureDrag): The gesture recognizer tracking the drag.
            dx (float): The delta X movement since drag began.
            dy (float): The delta Y movement since drag began.
        """
        if self.is_x11():
            self.last_x = int(self.saved_x + dx)
            self.last_y = int(self.saved_y + dy)

    def _on_header_drag_end(self, gesture, dx, dy):
        """
        Handle the end of a header drag gesture.
        
        Finalizes coordinate updates after the user completes the window drag
        operation. This method is specific to X11 display servers and saves
        the final window position for future reference.
        
        Args:
            gesture (Gtk.GestureDrag): The gesture recognizer that tracked the drag.
            dx (float): The total delta X movement from start to end.
            dy (float): The total delta Y movement from start to end.
        """
        if self.is_x11():
            self.saved_x = getattr(self, "last_x", 0)
            self.saved_y = getattr(self, "last_y", 0)

    def _on_map(self, widget):
        """
        Handle the widget map event.
        
        Restores the previously saved window dimensions when the widget is
        mapped (made visible) on the screen. This ensures that sticky notes
        maintain their size across application restarts.
        
        Args:
            widget (Gtk.Widget): The widget being mapped to the screen.
        """
        if self.saved_width > 0 and self.saved_height > 0:
            self.set_default_size(self.saved_width, self.saved_height)

    def _on_buffer_changed(self, buffer):
        """
        Handle text buffer change events.
        
        Handles real-time updates when the text buffer content is modified
        by the user. Serializes the current buffer content and pushes the
        updated content to the main window preview cards for immediate
        reflection in the note list view.
        
        This method is skipped during the initial loading phase to avoid
        unnecessary update notifications.
        
        Args:
            buffer (Gtk.TextBuffer): The text buffer that was modified.
        """
        if not getattr(self, '_loading', True):
            if self.main_window:
                # Serialize current buffer content
                content = self._serialize_buffer()
                # Direct push notification to the main UI list
                self.main_window.update_card_text(self.note_id, content)