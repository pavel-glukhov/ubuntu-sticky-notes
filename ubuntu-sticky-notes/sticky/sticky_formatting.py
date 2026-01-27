import json
from gi.repository import Gtk, Pango


class StickyFormatting:
    """
    Mixin class for StickyWindow handling text buffer formatting,
    including styles, colors, font sizes, and list toggles.
    """

    def setup_tags(self):
        """
        Initializes the GtkTextTagTable with standard styles and dynamic
        color/size tags based on the application configuration.
        """
        self.tag_table = self.buffer.get_tag_table()

        # Standard text styles
        self.buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.buffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        self.buffer.create_tag("strikethrough", strikethrough=True)

        # Dynamic color tags
        text_colors = self.config.get("text_colors", [])
        for color in text_colors:
            self.buffer.create_tag(f"text_color_{color}", foreground=color)

        # Dynamic font size tags (using Pango.SCALE for correct rendering)
        font_sizes = self.config.get("font_sizes", [])
        for size in font_sizes:
            self.buffer.create_tag(f"font_size_{size}", size=size * Pango.SCALE)

    def apply_format(self, tag_name: str):
        """
        Toggles a basic format tag (bold, italic, etc.) on the selected text range.
        Args:
            tag_name (str): The name of the tag to apply/remove.
        """
        res = self.buffer.get_selection_bounds()
        if res:
            start, end = res
            tag = self.tag_table.lookup(tag_name)

            if start.has_tag(tag):
                self.buffer.remove_tag(tag, start, end)
            else:
                self.buffer.apply_tag(tag, start, end)

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer) # Force update

    def apply_text_color(self, hex_color: str):
        """
        Applies a foreground color tag to the selection.
        Removes any existing color tags in the range before applying the new one.
        Args:
            hex_color (str): The hexadecimal color string to apply.
        """
        res = self.buffer.get_selection_bounds()
        if res:
            start, end = res
            
            # Clear existing color tags to prevent overlaps
            text_colors = self.config.get("text_colors", [])
            for color in text_colors:
                self.buffer.remove_tag_by_name(f"text_color_{color}", start, end)

            self.buffer.apply_tag_by_name(f"text_color_{hex_color}", start, end)

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer) # Force update

    def apply_font_size(self, size: int):
        """
        Applies a font size tag to the selection and updates the UI button label.
        Removes existing font size tags in the range before applying the new one.
        Args:
            size (int): The font size to apply.
        """
        res = self.buffer.get_selection_bounds()
        if res:
            start, end = res

            # Clear existing font tags
            font_sizes = self.config.get("font_sizes", [])
            for s in font_sizes:
                self.buffer.remove_tag_by_name(f"font_size_{s}", start, end)

            self.buffer.apply_tag_by_name(f"font_size_{size}", start, end)

        if hasattr(self, 'btn_font_size'):
            self.btn_font_size.set_label(str(size))

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer) # Force update

    def toggle_bullet_list(self):
        """
        Toggles bullet points for the selected lines.
        Prepends a bullet character if missing, or removes it if present.
        """
        BULLET_CHAR = " • "
        res = self.buffer.get_selection_bounds()

        # Default to cursor position if no selection exists
        start, end = res if res else (
            self.buffer.get_iter_at_mark(self.buffer.get_insert()),
            self.buffer.get_iter_at_mark(self.buffer.get_insert())
        )
        if not res:
            end = start.copy()

        # Align to line boundaries
        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()

        text = self.buffer.get_text(start, end, False)
        lines = text.split('\n')

        # Process lines to add/remove bullets
        new_lines = [
            line[len(BULLET_CHAR):] if line.startswith(BULLET_CHAR)
            else f"{BULLET_CHAR}{line}" for line in lines
        ]

        # Use atomic user action for Undo/Redo support
        self.buffer.begin_user_action()
        self.buffer.delete(start, end)
        self.buffer.insert(start, '\n'.join(new_lines))
        self.buffer.end_user_action()

        self.text_view.grab_focus()
        self._on_buffer_changed(self.buffer) # Force update