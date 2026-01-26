import json
import html as html_lib
from gi.repository import Gtk, Pango
import builtins # Import builtins to access the _() function

_ = builtins._ # Assign the translation function to _

class NoteCard(Gtk.Box):
    def __init__(self, note, db, menu_callback=None, refresh_callback=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.note_id = note["id"]
        self.db = db
        self.is_pinned = note['is_pinned'] == 1 if 'is_pinned' in note.keys() else False
        self.menu_callback = menu_callback
        self.refresh_callback = refresh_callback

        self.set_hexpand(True)
        self.set_vexpand(False)

        self.card_canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.card_canvas.add_css_class("sticky-paper-card")
        self.card_canvas.set_size_request(-1, 50)
        self.card_canvas.set_overflow(Gtk.Overflow.HIDDEN)
        self.append(self.card_canvas)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_top(4); header.set_margin_end(4)
        self.card_canvas.append(header)

        spacer = Gtk.Box(hexpand=True)
        header.append(spacer)

        self.pin_button = Gtk.Button()
        self.pin_button.set_has_frame(False)
        self.pin_button.add_css_class("flat")
        self._update_pin_icon()
        header.append(self.pin_button)
        
        # --- Robust content decoding ---
        initial_content_raw = note["content"] or ""
        segments = []
        try:
            # Try decoding from hex-encoded JSON (new format)
            segments = json.loads(bytes.fromhex(initial_content_raw).decode('utf-8'))
        except (ValueError, TypeError, json.JSONDecodeError):
            try:
                # Try decoding as plain JSON (intermediate format if any)
                segments = json.loads(initial_content_raw)
            except (ValueError, TypeError, json.JSONDecodeError):
                # Fallback to plain text
                segments = [{"text": initial_content_raw, "tags": []}]

        markup_text = self._generate_markup(segments)

        self.label = Gtk.Label()
        self.label.set_use_markup(True)
        self.label.set_markup(markup_text)

        self.label.set_wrap(True)
        self.label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        self.label.set_lines(5)
        self.label.set_xalign(0); self.label.set_yalign(0)
        self.label.set_valign(Gtk.Align.START)
        self.label.set_margin_top(0); self.label.set_margin_bottom(12)
        self.label.set_margin_start(15); self.label.set_margin_end(15)
        self.card_canvas.append(self.label)

        self.update_color(note["color"])
        self.setup_gestures()

    def _update_pin_icon(self):
        icon_name = "starred-symbolic" if self.is_pinned else "non-starred-symbolic"
        self.pin_button.set_icon_name(icon_name)
        self.pin_button.set_tooltip_text(_("Pin Note") if not self.is_pinned else _("Unpin Note"))

    def on_pin_clicked(self, gesture, n_press, x, y):
        self.db.toggle_pin_status(self.note_id)
        self.is_pinned = not self.is_pinned
        self._update_pin_icon()
        if self.refresh_callback:
            self.refresh_callback()
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def _generate_markup(self, segments):
        if not segments: return ""

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

            opening_tags = []
            closing_tags = []
            tags = seg.get("tags", [])
            for tag in tags:
                if tag == "bold":
                    opening_tags.append("<b>")
                    closing_tags.insert(0, "</b>")
                elif tag == "italic":
                    opening_tags.append("<i>")
                    closing_tags.insert(0, "</i>")
                elif tag == "underline":
                    opening_tags.append("<u>")
                    closing_tags.insert(0, "</u>")
                elif tag == "strikethrough":
                    opening_tags.append("<s>")
                    closing_tags.insert(0, "</s>")
                elif tag.startswith("text_color_"):
                    c = tag.replace("text_color_", "")
                    opening_tags.append(f'<span foreground="{c}">')
                    closing_tags.insert(0, "</span>")
                elif tag.startswith("font_size_"):
                    s = tag.replace("font_size_", "")
                    opening_tags.append(f'<span size="{s}pt">')
                    closing_tags.insert(0, "</span>")
            
            full_markup += "".join(opening_tags) + safe_text + "".join(closing_tags)

        return full_markup.rstrip()

    def update_color(self, hex_color):
        if not hex_color: hex_color = "#FFF59D"
        provider = Gtk.CssProvider()
        css = f".sticky-paper-card {{ background-color: {hex_color}; border-radius: 0px; min-height: 50px; }}"
        provider.load_from_data(css.encode())
        self.card_canvas.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def setup_gestures(self):
        click_open = Gtk.GestureClick()
        click_open.connect("released", lambda gesture, n, x, y: self.get_native().open_note(self.note_id))
        self.card_canvas.add_controller(click_open)

        click_pin = Gtk.GestureClick()
        click_pin.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        click_pin.connect("released", self.on_pin_clicked)
        self.pin_button.add_controller(click_pin)

        menu = Gtk.GestureClick(button=3)
        menu.connect("released", self._on_right_click)
        self.add_controller(menu)

    def _on_right_click(self, gesture, n, x, y):
        if self.menu_callback:
            self.menu_callback(self.note_id, self.card_canvas)
        else:
            self.get_native().create_combined_context_menu(self.note_id, self.card_canvas)
