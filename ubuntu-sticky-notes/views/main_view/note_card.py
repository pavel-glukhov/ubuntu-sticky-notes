"""Note card module for Ubuntu Sticky Notes.

Provides card widgets that display note previews in the main view.
"""

import json
import html as html_lib
from gi.repository import Gtk, Pango


class NoteCard(Gtk.Box):
    """Visual card representation of a note.
    
    Displays a preview of note content with color and formatting.
    Handles click and right-click gestures for opening and context menu.
    
    Attributes:
        note_id: ID of the note being displayed.
        menu_callback: Optional callback for right-click menu.
        card_canvas: Container box with colored background.
        label: Label displaying formatted note content.
    """
    def __init__(self, note, db, menu_callback=None):
        """Initialize the note card.
        
        Args:
            note: Dictionary containing note data (id, content, color).
            db: Database controller instance (unused in current implementation).
            menu_callback: Optional callback for custom context menu.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.note_id = note["id"]
        self.menu_callback = menu_callback

        self.set_margin_top(0)
        self.set_margin_bottom(0)
        self.set_margin_start(0)
        self.set_margin_end(0)

        self.set_hexpand(True)
        self.set_vexpand(False)

        self.card_canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.card_canvas.add_css_class("sticky-paper-card")

        self.card_canvas.set_size_request(-1, 50)
        self.card_canvas.set_overflow(Gtk.Overflow.HIDDEN)
        self.append(self.card_canvas)

        markup_text = self._generate_markup(note["content"])

        self.label = Gtk.Label()
        self.label.set_use_markup(True)
        self.label.set_markup(markup_text)

        self.label.set_wrap(True)
        self.label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        self.label.set_lines(5)

        self.label.set_xalign(0)
        self.label.set_yalign(0)
        self.label.set_valign(Gtk.Align.START)

        self.label.set_margin_top(12)
        self.label.set_margin_bottom(12)
        self.label.set_margin_start(15)
        self.label.set_margin_end(15)

        self.card_canvas.append(self.label)

        self.update_color(note["color"])
        self.setup_gestures()

    def _generate_markup(self, raw_content):
        """Generate Pango markup from serialized note content.
        
        Parses hex-encoded JSON with text segments and formatting tags,
        converting them to Pango markup. Limits output to 5 lines.
        
        Args:
            raw_content: Hex-encoded JSON string or plain text.
            
        Returns:
            Pango markup string with formatting tags.
        """
        if not raw_content: return ""

        try:
            json_bytes = bytes.fromhex(raw_content)
            segments = json.loads(json_bytes.decode('utf-8'))

            full_markup = ""
            line_count = 0

            for seg in segments:
                text = seg.get("text", "")

                lines_in_seg = text.split('\n')
                if line_count >= 5: break

                if line_count + len(lines_in_seg) - 1 >= 5:
                    allowed = 5 - line_count
                    text = "\n".join(lines_in_seg[:allowed])
                    line_count = 5
                else:
                    line_count += len(lines_in_seg) - 1

                safe_text = html_lib.escape(text)

                tags = seg.get("tags", [])
                st, et = "", ""
                for tag in tags:
                    if tag == "bold":
                        st += "<b>"; et = "</b>" + et
                    elif tag == "italic":
                        st += "<i>"; et = "</i>" + et
                    elif tag == "underline":
                        st += "<u>"; et = "</u>" + et
                    elif tag == "strikethrough":
                        st += "<s>"; et = "</s>" + et
                    elif tag.startswith("text_color_"):
                        c = tag.replace("text_color_", "")
                        st += f'<span foreground="{c}">';
                        et = "</span>" + et

                full_markup += f"{st}{safe_text}{et}"

            return full_markup.rstrip()

        except Exception:
            text_content = str(raw_content).replace("<br>", "\n")

            lines = text_content.split('\n')
            if len(lines) > 5:
                text_content = "\n".join(lines[:5])

            return html_lib.escape(text_content).rstrip()

    def update_color(self, hex_color):
        """Update the background color of the card.
        
        Args:
            hex_color: Hex color code (e.g., '#FFF59D').
        """
        if not hex_color: hex_color = "#FFF59D"
        provider = Gtk.CssProvider()
        css = f"""
        .sticky-paper-card {{ 
            background-color: {hex_color}; 
            border-radius: 0px; 
            min-height: 50px;
        }}
        """
        provider.load_from_data(css.encode())
        self.card_canvas.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def setup_gestures(self):
        """Set up mouse gesture handlers for the card."""
        click = Gtk.GestureClick()
        click.connect("released", lambda *args: self.get_native().open_note(self.note_id))
        self.add_controller(click)

        menu = Gtk.GestureClick(button=3)
        menu.connect("pressed", self._on_right_click)
        self.add_controller(menu)

    def _on_right_click(self, gesture, n, x, y):
        """Handle right-click to show context menu.
        
        Args:
            gesture: Gesture that triggered the event.
            n: Number of clicks.
            x: X coordinate.
            y: Y coordinate.
        """
        if self.menu_callback:
            self.menu_callback(self.note_id, self.card_canvas)
        else:
            self.get_native().create_combined_context_menu(self.note_id, self.card_canvas)