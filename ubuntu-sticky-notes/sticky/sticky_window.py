import json
import gi
from gi.repository import Gtk, Gdk, GLib, Pango

from .sticky_formatting import StickyFormatting
from .sticky_actions import StickyActions
from .sticky_ui import StickyUI
from .sticky_events import StickyEvents


class StickyWindow(Gtk.Window, StickyFormatting, StickyActions, StickyUI, StickyEvents):
    """
    Main Window class for a single sticky note.
    Inherits from multiple mixins to separate concerns (UI, Events, Actions, Formatting).
    """
    def __init__(self, db, note_id=None, main_window=None):
        """
        Initializes the StickyWindow.
        Args:
            db: The database controller instance.
            note_id (int, optional): The ID of the note. Defaults to None.
            main_window (MainWindow, optional): Reference to the main application window. Defaults to None.
        """
        super().__init__()

        # 1. State and Data Initialization
        self.db = db
        self.note_id = note_id
        self.main_window = main_window
        self.config = getattr(main_window, 'config', {}) # Get initial config from main_window
        self._loading = True
        self._is_destroying = False # Flag to prevent operations during destruction
        self.scale = 1.0
        self.current_color = "#FFF59D"
        self.default_font_size = 12
        
        # Load saved position and size from DB
        if self.note_id:
            note_data = self.db.get(self.note_id)
            if note_data:
                self.saved_x = note_data['x'] if note_data['x'] is not None else 300
                self.saved_y = note_data['y'] if note_data['y'] is not None else 300
                self.saved_width = note_data['w'] if note_data['w'] is not None else 300
                self.saved_height = note_data['h'] if note_data['h'] is not None else 380
            else:
                self.saved_x, self.saved_y, self.saved_width, self.saved_height = 300, 300, 300, 380
        else:
            self.saved_x, self.saved_y, self.saved_width, self.saved_height = 300, 300, 300, 380

        # 2. Style Management
        self.window_css_provider = Gtk.CssProvider()
        self.get_style_context().add_provider(
            self.window_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # 3. Window Configuration
        self.set_decorated(False)
        self.add_css_class("sticky-window")
        
        # Apply saved position and size
        self.set_default_size(self.saved_width, self.saved_height)
        # Note: set_default_size sets the size, but for position we might need to wait for realization or use other methods depending on backend.
        # Gtk4 doesn't have a simple move() for toplevels in the same way, especially on Wayland.
        # We will try to set it, but it might be ignored by the compositor on Wayland.
        # For X11 backend it might work if we use a Gdk.Surface method after mapping, but Gtk.Window doesn't expose move() directly in Gtk4.
        # We'll rely on the window manager for placement mostly, but save what we can.
        
        # 4. UI Hierarchy Construction
        self.overlay = Gtk.Overlay()
        self.set_child(self.overlay)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("sticky-main-area")
        self.overlay.set_child(self.main_box)

        self.setup_header()
        self.setup_text_area()
        self.setup_tags()
        self.setup_formatting_bar()
        self.setup_resize_handle()

        # 5. Database Load and Signal Connectivity
        self.load_from_db()
        self._loading = False
        self._connect_main_signals()

        # 6. Persistence Controllers
        focus_ctrl = Gtk.EventControllerFocus()
        focus_ctrl.connect("leave", lambda *_: self.save())
        self.add_controller(focus_ctrl)
        
        # Store timer ID to remove it later
        self.save_timer_id = GLib.timeout_add_seconds(2, self.save)

    def _connect_main_signals(self):
        """Connects core window and buffer signals."""
        self.connect("close-request", self._on_close_requested)
        self.connect("map", self._on_map)
        # Track size changes
        self.connect("notify::default-width", self._on_configure_event)
        self.connect("notify::default-height", self._on_configure_event)
        
        self.buffer.connect("notify::cursor-position", self.on_cursor_moved)
        self.buffer.connect("changed", self._on_buffer_changed)

    def is_x11(self):
        """Determines if the application is running under the X11 backend."""
        display = Gdk.Display.get_default()
        return "X11" in display.__class__.__name__

    def _on_configure_event(self, *args):
        """
        Called when the window size changes.
        Updates the internal state with the new dimensions.
        """
        self.saved_width = self.get_default_size()[0]
        self.saved_height = self.get_default_size()[1]
        # Position tracking in GTK4 is limited, especially on Wayland.
        # We rely on the save() method to try and get the surface position if possible.

    def _update_ui_design(self, hex_color=None):
        """
        Updates the visual design of the sticky note, including background color and CSS.
        Args:
            hex_color (str, optional): The new background color in hex format. Defaults to None.
        """
        if hex_color:
            self.current_color = hex_color.strip()
        scale = self.scale
        css = f"""
        window.sticky-window {{ background-color: {self.current_color}; border-radius: 12px; border: 1px solid rgba(0,0,0,0.1); }}
        .header-btn-subtle, .format-btn-tiny {{ background-color: transparent; border-radius: 4px; color: rgba(0,0,0,0.7); }}
        .header-btn-subtle:hover, .format-btn-tiny:hover {{ background-color: rgba(0,0,0,0.1); }}
        .compact-header {{ min-height: {int(22 * scale)}px; }}
        .sticky-text-edit, .sticky-text-edit text, textview, text {{ background-color: transparent; color: #000000; }}
        .resize-handle {{ background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.1) 50%); min-width: {int(16 * scale)}px; min-height: {int(16 * scale)}px; }}
        """
        clean_css = "\n".join([line.strip() for line in css.split('\n') if line.strip()])
        self.window_css_provider.load_from_data(clean_css.encode('utf-8'))

    def setup_formatting_bar(self):
        """Configures the bottom toolbar with formatting buttons based on user preferences."""
        if hasattr(self, 'format_bar'):
            while child := self.format_bar.get_first_child():
                self.format_bar.remove(child)
        else:
            self.format_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            self.format_bar.add_css_class("compact-format-bar")
            self.main_box.append(self.format_bar)

        scale = self.scale
        icon_size = int(18 * scale)
        fmt_config = self.config.get("formatting", {})
        if not isinstance(fmt_config, dict): fmt_config = {}

        buttons_config = [
            ("bold", "<b>B</b>", self.apply_format, "bold"),
            ("italic", "<i>I</i>", self.apply_format, "italic"),
            ("underline", "<u>U</u>", self.apply_format, "underline"),
            ("strikethrough", "<s>S</s>", self.apply_format, "strikethrough"),
            ("list", "≡", self.toggle_bullet_list, None)
        ]

        has_any_btn = False
        for key, label, callback, arg in buttons_config:
            if fmt_config.get(key, True):
                btn = Gtk.Button(has_frame=False)
                btn.set_child(Gtk.Label(label=label, use_markup=True))
                btn.add_css_class("format-btn-tiny")
                btn.set_size_request(icon_size, icon_size)
                if arg:
                    btn.connect("clicked", (lambda cb, a: lambda _: cb(a))(callback, arg))
                else:
                    btn.connect("clicked", (lambda cb: lambda _: cb())(callback))
                self.format_bar.append(btn)
                has_any_btn = True

        show_color = fmt_config.get("text_color", True)
        show_font = fmt_config.get("font_size", True)

        if has_any_btn and (show_color or show_font):
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL, margin_start=int(3*scale), margin_end=int(3*scale))
            self.format_bar.append(sep)

        if show_color:
            btn_text_color = Gtk.MenuButton(has_frame=False)
            btn_text_color.set_child(Gtk.Label(label='<span foreground="#444">A</span>', use_markup=True))
            btn_text_color.add_css_class("format-btn-tiny")
            btn_text_color.set_size_request(icon_size, icon_size)
            self.setup_text_color_popover(btn_text_color)
            self.format_bar.append(btn_text_color)

        if show_font:
            self.btn_font_size = Gtk.MenuButton(label=str(self.default_font_size), has_frame=False)
            self.btn_font_size.add_css_class("format-btn-tiny")
            self.btn_font_size.set_size_request(int(icon_size * 1.5), icon_size)
            self.setup_font_size_popover(self.btn_font_size)
            self.format_bar.append(self.btn_font_size)

    def on_cursor_moved(self, buffer, pspec):
        """Updates the font size label in the UI based on the cursor's current text tags."""
        if not hasattr(self, 'btn_font_size'):
            return
        cursor_iter = buffer.get_iter_at_mark(buffer.get_insert())
        tags = cursor_iter.get_tags()
        current_size = self.default_font_size
        for tag in tags:
            name = tag.get_property("name")
            if name and name.startswith("font_size_"):
                try:
                    current_size = int(name.replace("font_size_", ""))
                except ValueError:
                    pass
        self.btn_font_size.set_label(str(current_size))

    def update_pin_ui(self):
        """Placeholder for updating the 'Pinned' status icon in the UI."""
        pass

    def reload_config(self, new_config):
        """
        Reloads configuration and updates UI elements.
        Args:
            new_config (dict): The new configuration dictionary.
        """
        self.config = new_config
        # Re-setup header to update the menu with new palette
        if hasattr(self, 'header_box'):
            self.main_box.remove(self.header_box)
        self.setup_header()
        # Re-insert header at the top
        self.main_box.reorder_child_after(self.header_box, None)
        
        # Also update formatting bar if needed (e.g. if buttons visibility changed)
        self.setup_formatting_bar()
