"""
Text Formatting Logic for StickyWindow.

This module provides a mixin class that handles all text formatting operations
within a sticky note's text buffer, such as applying bold/italic, changing
colors, adjusting font sizes, and toggling bulleted lists.
"""
from gi.repository import Gtk, Pango


class StickyFormatting:
    """
    A mixin for `StickyWindow` that manages text formatting tags and actions.
    """

    def setup_tags(self):
        """
        Initializes the Gtk.TextTagTable with both standard style tags and
        dynamic tags for colors and font sizes based on the application config.
        """
        self.tag_table = self.buffer.get_tag_table()

        # --- Standard Text Style Tags ---
        self.buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.buffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        self.buffer.create_tag("strikethrough", strikethrough=True)

        # --- Dynamic Tags from Configuration ---
        # Create a tag for each color in the palette.
        text_colors = self.config.get("text_colors", [])
        for color in text_colors:
            self.buffer.create_tag(f"text_color_{color}", foreground=color)

        # Create a tag for each font size, converting points to Pango units.
        font_sizes = self.config.get("font_sizes", [])
        for size in font_sizes:
            self.buffer.create_tag(f"font_size_{size}", size=size * Pango.SCALE)

    def apply_format(self, tag_name: str):
        """
        Toggles a standard format tag (e.g., "bold") on the selected text.

        Args:
            tag_name: The name of the tag to apply or remove.
        """
        bounds = self.buffer.get_selection_bounds()
        if not bounds:
            return
            
        start, end = bounds
        tag = self.tag_table.lookup(tag_name)
        if start.has_tag(tag):
            self.buffer.remove_tag(tag, start, end)
        else:
            self.buffer.apply_tag(tag, start, end)

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer)

    def apply_text_color(self, hex_color: str):
        """
        Applies a specific foreground color to the selected text.
        
        It first removes any other color tags from the selection to ensure only
        one color is applied at a time.

        Args:
            hex_color: The color to apply, in hexadecimal format (e.g., "#RRGGBB").
        """
        bounds = self.buffer.get_selection_bounds()
        if not bounds:
            return
            
        start, end = bounds
        # Remove all existing color tags from the selection first.
        for color in self.config.get("text_colors", []):
            self.buffer.remove_tag_by_name(f"text_color_{color}", start, end)
        
        # Apply the new color tag.
        self.buffer.apply_tag_by_name(f"text_color_{hex_color}", start, end)

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer)

    def apply_font_size(self, size: int):
        """
        Applies a specific font size to the selected text.

        It removes any other font size tags from the selection before applying
        the new one.

        Args:
            size: The font size to apply.
        """
        bounds = self.buffer.get_selection_bounds()
        if not bounds:
            return
            
        start, end = bounds
        # Remove all existing font size tags from the selection.
        for s in self.config.get("font_sizes", []):
            self.buffer.remove_tag_by_name(f"font_size_{s}", start, end)
        
        # Apply the new size tag.
        self.buffer.apply_tag_by_name(f"font_size_{size}", start, end)

        if hasattr(self, 'btn_font_size'):
            self.btn_font_size.set_label(str(size))

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer)

    def toggle_bullet_list(self):
        """
        Toggles bullet points for the currently selected lines.
        
        If a line starts with a bullet, it's removed. Otherwise, a bullet is added.
        This operation is performed on all lines within the selection.
        """
        BULLET_CHAR = " • "
        res = self.buffer.get_selection_bounds()

        start, end = res if res else (
            self.buffer.get_iter_at_mark(self.buffer.get_insert()),
            self.buffer.get_iter_at_mark(self.buffer.get_insert())
        )
        if not res:
            end = start.copy()

        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()

        text = self.buffer.get_text(start, end, False)
        lines = text.split('\n')

        new_lines = [
            line[len(BULLET_CHAR):] if line.startswith(BULLET_CHAR)
            else f"{BULLET_CHAR}{line}" for line in lines
        ]

        self.buffer.begin_user_action()
        self.buffer.delete(start, end)
        self.buffer.insert(start, '\n'.join(new_lines))
        self.buffer.end_user_action()

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer)
