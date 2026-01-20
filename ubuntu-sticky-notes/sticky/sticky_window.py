"""Main sticky note window module.

This module provides the main StickyWindow class that combines multiple mixins
to create a fully functional sticky note window with formatting, UI, events,
and action handling capabilities.
"""

import json
import gi
from gi.repository import Gtk, Gdk, GLib, Pango

# Import project-specific mixins
from .sticky_formatting import StickyFormatting
from .sticky_actions import StickyActions
from .sticky_ui import StickyUI
from .sticky_events import StickyEvents

# UI Constants
STICKY_COLORS = ['#FFF59D', '#F8BBD0', '#C8E6C9', '#B3E5FC']
TEXT_COLORS = ['#000000', '#424242', '#D32F2F', '#C2185B', '#7B1FA2', '#303F9F', '#1976D2', '#0288D1', '#0097A7', '#00796B', '#388E3C', '#689F38', '#AFB42B', '#FBC02D', '#FFA000', '#E64A19']
FONT_SIZES = [8, 10, 12, 14, 16, 18, 20, 24, 32, 48, 72]

class StickyWindow(Gtk.Window, StickyFormatting, StickyActions, StickyUI, StickyEvents):
    """
    Main window class for a single sticky note.
    
    Combines multiple mixins to provide a complete sticky note experience
    including text formatting, UI construction, event handling, and database
    persistence. Manages window state, appearance, and user interactions.
    
    Attributes:
        db: Database controller for note persistence.
        note_id: Unique identifier for the note.
        main_window: Reference to the main application window.
        config: Application configuration dictionary.
        current_color: Current background color of the note.
        scale: UI scaling factor.
    """
    def __init__(self, db, note_id=None, main_window=None):
        """
        Initialize a sticky note window.
        
        Sets up the window state, loads CSS styling, constructs the UI
        hierarchy, loads data from database, and establishes auto-save
        mechanisms.
        
        Args:
            db: Database controller instance for note persistence.
            note_id: Unique identifier for the note. If None, creates a new note.
            main_window: Reference to the main application window.
        """
        super().__init__()

        # 1. State and Data Initialization
        self.db = db
        self.note_id = note_id
        self.main_window = main_window
        self.config = getattr(main_window, 'config', {})

        # Prevent auto-saving during initial data fetch
        self._loading = True

        self.scale = 1.0
        self.current_color = "#FFF59D"
        self.default_font_size = 12
        self.saved_width, self.saved_height = 300, 380

        # 2. Style Management
        self.window_css_provider = Gtk.CssProvider()
        self.get_style_context().add_provider(
            self.window_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # 3. Window Configuration
        self.set_decorated(False)  # Frameless window
        self.add_css_class("sticky-window")

        # 4. UI Hierarchy Construction
        self.overlay = Gtk.Overlay()
        self.set_child(self.overlay)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("sticky-main-area")
        self.overlay.set_child(self.main_box)

        # Initialize components via mixins
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
        # Save immediately when the window loses focus
        focus_ctrl = Gtk.EventControllerFocus()
        focus_ctrl.connect("leave", lambda *_: self.save())
        self.add_controller(focus_ctrl)

        # Periodic background auto-save (every 2 seconds)
        GLib.timeout_add_seconds(2, self.save)

    def _connect_main_signals(self):
        """
        Connect core window and buffer signals.
        
        Establishes signal connections for window close requests, mapping,
        cursor position changes, and text buffer modifications.
        """
        self.connect("close-request", self._on_close_requested)
        self.connect("map", self._on_map)
        self.buffer.connect("notify::cursor-position", self.on_cursor_moved)
        self.buffer.connect("changed", self._on_buffer_changed)

    def is_x11(self):
        """
        Determine if the application is running under the X11 backend.
        
        Returns:
            bool: True if running on X11, False otherwise (e.g., Wayland).
        """
        display = Gdk.Display.get_default()
        return "X11" in display.__class__.__name__

    def _update_ui_design(self, hex_color=None):
        """
        Dynamically generate and apply CSS to update note appearance.
        
        Generates CSS styling for the note's background color, UI scaling,
        and component appearance, then applies it to the window.
        
        Args:
            hex_color (str, optional): New background color in hex format.
                If None, uses current color.
        """
        if hex_color:
            self.current_color = hex_color.strip()

        scale = self.scale
        css = f"""
        window.sticky-window {{ 
            background-color: {self.current_color}; 
            border-radius: 12px; 
            border: 1px solid rgba(0,0,0,0.1); 
        }}
        .header-btn-subtle, .format-btn-tiny {{ 
            background-color: transparent; 
            border-radius: 4px; 
            color: rgba(0,0,0,0.7); 
        }}
        .header-btn-subtle:hover, .format-btn-tiny:hover {{ 
            background-color: rgba(0,0,0,0.1); 
        }}
        .compact-header {{ 
            min-height: {int(22 * scale)}px; 
        }}
        .sticky-text-edit, .sticky-text-edit text, textview, text {{ 
            background-color: transparent; 
            color: #000000; 
        }}
        .resize-handle {{ 
            background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.1) 50%); 
            min-width: {int(16 * scale)}px; 
            min-height: {int(16 * scale)}px; 
        }}
        """
        # Cleanup string for the GTK CSS parser
        clean_css = "\n".join([line.strip() for line in css.split('\n') if line.strip()])
        self.window_css_provider.load_from_data(clean_css.encode('utf-8'))

    def setup_formatting_bar(self):
        """
        Configure the bottom toolbar with formatting buttons.
        
        Creates formatting buttons (bold, italic, underline, strikethrough,
        list, text color, font size) based on user preferences and
        configuration settings.
        """
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

        # Core formatting buttons
        formats = [
            ("<b>B</b>", "bold"), ("<i>I</i>", "italic"),
            ("<u>U</u>", "underline"), ("<s>S</s>", "strikethrough")
        ]

        has_any_btn = False
        for label, tag_name in formats:
            if fmt_config.get(tag_name, True):
                btn = Gtk.Button(has_frame=False)
                btn.set_child(Gtk.Label(label=label, use_markup=True))
                btn.add_css_class("format-btn-tiny")
                btn.set_size_request(icon_size, icon_size)
                btn.connect("clicked", lambda _, t=tag_name: self.apply_format(t))
                self.format_bar.append(btn)
                has_any_btn = True

        if fmt_config.get("list", True):
            btn_list = Gtk.Button(has_frame=False)
            btn_list.set_child(Gtk.Label(label="≡"))
            btn_list.add_css_class("format-btn-tiny")
            btn_list.set_size_request(icon_size, icon_size)
            btn_list.connect("clicked", lambda _: self.toggle_bullet_list())
            self.format_bar.append(btn_list)
            has_any_btn = True

        # Popovers for color and font size
        show_color = fmt_config.get("text_color", True)
        show_font = fmt_config.get("font_size", True)

        if has_any_btn and (show_color or show_font):
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_start(int(3 * scale))
            sep.set_margin_end(int(3 * scale))
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
        """
        Update the font size label based on cursor position.
        
        Inspects the text tags at the current cursor position and updates
        the font size button label to reflect the active font size.
        
        Args:
            buffer (Gtk.TextBuffer): The text buffer that triggered the signal.
            pspec (GObject.ParamSpec): Parameter specification for the property.
        """
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
        """
        Update the 'Pinned' status icon in the UI.
        
        Placeholder method for updating visual indicators when a note's
        pinned status changes.
        """
        pass