"""
UI Construction Mixin for StickyWindow.

This module provides a mixin for `StickyWindow` that is responsible for
building all the UI components of a single sticky note, such as the header,
text area, menus, and resize handle.
"""
from gi.repository import Gtk, Gdk
import builtins

# Ensure a fallback for gettext `_` is available.
if not hasattr(builtins, "_"):
    builtins._ = lambda s: s

class StickyUI:
    """
    A mixin for `StickyWindow` that handles the construction of the UI.
    """

    def setup_header(self):
        """Creates the compact header bar containing window controls."""
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_size_request(-1, int(22 * self.scale))
        self.header_box.add_css_class("compact-header")

        btn_add = Gtk.Button(label="+", has_frame=False)
        btn_add.add_css_class("header-btn-subtle")
        btn_add.connect("clicked", self._on_add_clicked)
        self.header_box.append(btn_add)

        # The spacer is a draggable area for moving the window.
        spacer = Gtk.Box(hexpand=True)
        spacer.set_can_target(True)
        header_drag = Gtk.GestureDrag.new()
        header_drag.connect("drag-begin", self._on_header_drag_begin)
        header_drag.connect("drag-update", self._on_header_drag_update)
        header_drag.connect("drag-end", self._on_header_drag_end)
        spacer.add_controller(header_drag)
        self.header_box.append(spacer)

        btn_menu = Gtk.MenuButton(has_frame=False, icon_name="open-menu-symbolic")
        btn_menu.add_css_class("header-btn-subtle")
        self.setup_main_menu(btn_menu)
        self.header_box.append(btn_menu)

        btn_close = Gtk.Button(label="✕", has_frame=False)
        btn_close.add_css_class("header-btn-subtle")
        btn_close.connect("clicked", self._on_close_clicked)
        self.header_box.append(btn_close)

        self.main_box.append(self.header_box)

    def setup_main_menu(self, btn: Gtk.MenuButton):
        """
        Constructs the main popover menu for note color and print actions.
        """
        popover = Gtk.Popover()
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(4 * self.scale))
        main_vbox.add_css_class("menu-box")

        lbl_color = Gtk.Label(label=builtins._("Color"), xalign=0)
        lbl_color.add_css_class("menu-label")
        main_vbox.append(lbl_color)

        grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        btn_size = int(22 * self.scale)
        
        for i, color in enumerate(self.config.get("palette", [])):
            b = Gtk.Button()
            b.set_size_request(btn_size, btn_size)
            # Apply color swatch style via a dedicated CSS provider for the button.
            cp = Gtk.CssProvider()
            cp.load_from_data(f"button {{ background-color: {color}; border-radius: 50%; }}".encode())
            b.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            b.connect("clicked", lambda _, c=color: (self.apply_color(c), popover.popdown()))
            grid.attach(b, i % 4, i // 4, 1, 1)
        main_vbox.append(grid)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=4, margin_bottom=4)
        main_vbox.append(sep)

        # Customization Menu Item
        box_custom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_custom.append(Gtk.Image.new_from_icon_name("emblem-system-symbolic"))
        box_custom.append(Gtk.Label(label=builtins._("Customize")))
        btn_custom = Gtk.Button(child=box_custom, has_frame=False)
        btn_custom.add_css_class("menu-row-btn")
        btn_custom.connect("clicked", lambda _: (self.on_customization_clicked(None), popover.popdown()))
        main_vbox.append(btn_custom)

        box_print = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_print.append(Gtk.Image.new_from_icon_name("printer-symbolic"))
        box_print.append(Gtk.Label(label=builtins._("Print note")))
        btn_print = Gtk.Button(child=box_print, has_frame=False)
        btn_print.add_css_class("menu-row-btn")
        btn_print.connect("clicked", lambda _: (self.on_print_clicked(None), popover.popdown()))
        main_vbox.append(btn_print)

        popover.set_child(main_vbox)
        btn.set_popover(popover)

    def setup_text_color_popover(self, btn: Gtk.MenuButton):
        """Creates the popover for selecting text color."""
        popover = Gtk.Popover()
        grid = Gtk.Grid(column_spacing=2, row_spacing=2, margin_top=4, margin_bottom=4, margin_start=4, margin_end=4)
        btn_size = int(18 * self.scale)
        
        for i, color in enumerate(self.config.get("text_colors", [])):
            b = Gtk.Button()
            b.set_size_request(btn_size, btn_size)
            cp = Gtk.CssProvider()
            cp.load_from_data(f"button {{ background-color: {color}; border-radius: 3px; }}".encode())
            b.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            b.connect("clicked", lambda _, c=color: (self.apply_text_color(c), popover.popdown()))
            grid.attach(b, i % 4, i // 4, 1, 1)

        popover.set_child(grid)
        btn.set_popover(popover)

    def setup_font_size_popover(self, btn: Gtk.MenuButton):
        """Creates the popover for selecting font size."""
        popover = Gtk.Popover()
        scrolled = Gtk.ScrolledWindow(max_content_height=200, propagate_natural_height=True)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        for size in self.config.get("font_sizes", []):
            b = Gtk.Button(label=str(size), has_frame=False)
            b.add_css_class("format-btn-tiny")
            b.connect("clicked", lambda _, s=size: (self.apply_font_size(s), popover.popdown()))
            vbox.append(b)
            
        scrolled.set_child(vbox)
        popover.set_child(scrolled)
        btn.set_popover(popover)

    def apply_color(self, hex_color: str):
        """
        Applies a new background color to the note and updates the live preview card.
        """
        self.current_color = hex_color
        self._update_ui_design()
        if self.main_window:
            self.main_window.update_card_color_live(self.note_id, hex_color)

    def setup_resize_handle(self):
        """Adds a draggable resize handle to the bottom-right corner."""
        self.resize_handle = Gtk.Box()
        size = int(16 * self.scale)
        self.resize_handle.set_size_request(size, size)
        self.resize_handle.set_halign(Gtk.Align.END)
        self.resize_handle.set_valign(Gtk.Align.END)
        self.resize_handle.add_css_class("resize-handle")
        self.resize_handle.set_cursor(Gdk.Cursor.new_from_name("se-resize", None))

        click_gest = Gtk.GestureClick.new()
        click_gest.connect("pressed", self._on_resize_pressed)
        self.resize_handle.add_controller(click_gest)
        self.overlay.add_overlay(self.resize_handle)

    def setup_text_area(self):
        """Initializes the main text view and attaches the keyboard shortcut controller."""
        self.text_view = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.text_view.add_css_class("sticky-text-edit")
        self.buffer = self.text_view.get_buffer()
        self.buffer.connect("changed", self._on_buffer_changed)

        # Attach the key controller directly to the text view.
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.text_view.add_controller(key_ctrl)

        self.scrolled = Gtk.ScrolledWindow(child=self.text_view, vexpand=True)
        self.main_box.append(self.scrolled)
