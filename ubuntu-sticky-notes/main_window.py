import re
import json
import html as html_lib
from gi.repository import Gtk, Adw, Gio, GObject, GLib, Pango
from sticky_window import StickyWindow
from datetime import datetime

STICKY_COLORS = ['#FFF59D', '#F8BBD0', '#C8E6C9', '#B3E5FC']


class NoteCard(Gtk.Box):
    def __init__(self, note, db):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.note_id = note["id"]

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
        self.label.set_lines(5)  # Ограничение в 5 строк

        self.label.set_xalign(0)  # Текст слева
        self.label.set_yalign(0)  # Текст сверху
        self.label.set_valign(Gtk.Align.START)

        self.label.set_margin_top(12)
        self.label.set_margin_bottom(12)
        self.label.set_margin_start(15)
        self.label.set_margin_end(15)

        self.card_canvas.append(self.label)

        self.update_color(note["color"])
        self.setup_gestures()

    def _generate_markup(self, raw_content):
        if not raw_content: return ""
        try:
            json_bytes = bytes.fromhex(raw_content)
            segments = json.loads(json_bytes.decode('utf-8'))
            full_markup = "";
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
        except:
            l = str(raw_content).split('\n')
            return html_lib.escape("\n".join(l[:5])).rstrip()

    def update_color(self, hex_color):
        if not hex_color: hex_color = "#FFF59D"
        provider = Gtk.CssProvider()
        css = f"""
        .sticky-paper-card {{ 
            background-color: {hex_color}; 
            border-radius: 0px; /* В списке обычно прямые углы или совсем легкие */
            min-height: 50px;
            /* Никаких ограничений по ширине */
        }}
        """
        provider.load_from_data(css.encode())
        self.card_canvas.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def setup_gestures(self):
        click = Gtk.GestureClick()
        click.connect("released", lambda *args: self.get_native().open_note(self.note_id))
        self.add_controller(click)
        menu = Gtk.GestureClick(button=3)
        menu.connect("pressed",
                     lambda g, n, x, y: self.get_native().create_combined_context_menu(self.note_id, self.card_canvas))
        self.add_controller(menu)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, db, **kwargs):
        super().__init__(title="Sticky Notes", default_width=400, default_height=600, **kwargs)
        self.db = db
        self.stickies = {}

        from gi.repository import Gdk
        css_provider = Gtk.CssProvider()
        css = """
        flowbox { padding: 0px; background: transparent; }
        flowboxchild { padding: 0px; margin: 0px; border: none; min-width: 0px; outline: none; }
        /* Убираем фон самого окна, чтобы было чисто */
        window.background { background-color: #ffffff; } 
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.setup_actions()
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.root_box)

        header_bar = Adw.HeaderBar()
        header_bar.set_show_end_title_buttons(True)

        btn_new = Gtk.Button(icon_name="list-add-symbolic")
        btn_new.add_css_class("flat")
        btn_new.connect("clicked", lambda _: self.create_note())
        header_bar.pack_start(btn_new)

        btn_trash = Gtk.Button(icon_name="user-trash-symbolic")
        btn_trash.add_css_class("flat")
        btn_trash.connect("clicked", self.on_show_trash)
        header_bar.pack_end(btn_trash)

        self.root_box.append(header_bar)

        self.search_entry = Gtk.SearchEntry(placeholder_text="Search...")
        self.search_entry.set_margin_start(10)
        self.search_entry.set_margin_end(10)
        self.search_entry.set_margin_top(10)
        self.search_entry.set_margin_bottom(10)
        self.search_entry.connect("search-changed", self.on_search)
        self.root_box.append(self.search_entry)

        self.flowbox = Gtk.FlowBox(
            valign=Gtk.Align.START,
            selection_mode=Gtk.SelectionMode.NONE
        )

        scrolled = Gtk.ScrolledWindow(child=self.flowbox, vexpand=True)
        scrolled.set_has_frame(False)
        self.root_box.append(scrolled)

        self.refresh_list()

    def refresh_list(self):
        while child := self.flowbox.get_first_child():
            self.flowbox.remove(child)

        self.flowbox.set_homogeneous(False)
        self.flowbox.set_max_children_per_line(1)
        self.flowbox.set_min_children_per_line(1)

        self.flowbox.set_halign(Gtk.Align.FILL)
        self.flowbox.set_valign(Gtk.Align.START)


        self.flowbox.set_column_spacing(0)
        self.flowbox.set_row_spacing(10)

        self.flowbox.set_margin_top(5)
        self.flowbox.set_margin_bottom(10)
        self.flowbox.set_margin_start(10)
        self.flowbox.set_margin_end(10)

        notes = self.db.all_notes(full=True)
        for note in notes:
            card = NoteCard(note, self.db)
            self.flowbox.append(card)

            flow_child = card.get_parent()
            if flow_child:
                flow_child.set_margin_top(0);
                flow_child.set_margin_bottom(0)
                flow_child.set_margin_start(0);
                flow_child.set_margin_end(0)
                flow_child.set_can_focus(False)

                flow_child.set_hexpand(True)
                flow_child.set_halign(Gtk.Align.FILL)

    def create_note(self):
        note_id = self.db.add()
        self.refresh_list()
        self.open_note(note_id)

    def open_note(self, note_id):
        if note_id in self.stickies:
            self.stickies[note_id].present()
            return
        new_sticky = StickyWindow(self.db, note_id, self)
        self.stickies[note_id] = new_sticky
        new_sticky.present()

    def on_search(self, entry):
        query = entry.get_text().lower()
        child = self.flowbox.get_first_child()
        while child:
            card = child.get_child()
            lbl = card.label
            if query in lbl.get_text().lower():
                child.set_visible(True)
            else:
                child.set_visible(False)
            child = child.get_next_sibling()

    def update_card_text(self, note_id, serialized_content):
        """Мгновенно обновляет текст карточки"""
        child = self.flowbox.get_first_child()
        while child:
            card = child.get_child()
            if isinstance(card, NoteCard) and card.note_id == note_id:
                new_markup = card._generate_markup(serialized_content)
                card.label.set_markup(new_markup)
                break
            child = child.get_next_sibling()

    def update_card_color_live(self, note_id, color):
        """Мгновенно красит карточку"""
        child = self.flowbox.get_first_child()
        while child:
            card = child.get_child()
            if isinstance(card, NoteCard) and card.note_id == note_id:
                card.update_color(color)
                break
            child = child.get_next_sibling()

    def on_show_trash(self, btn):
        from trash_window import TrashWindow
        TrashWindow(self.db, self).present()

    def on_action_delete_manual(self, note_id):
        self.db.move_to_trash(note_id)
        if note_id in self.stickies: self.stickies[note_id].close()
        self.refresh_list()

    def setup_actions(self):
        action_delete = Gio.SimpleAction.new("delete_note", GLib.VariantType.new("i"))
        action_delete.connect("activate", lambda a, v: self.on_action_delete_manual(v.get_int32()))
        self.add_action(action_delete)

    def create_combined_context_menu(self, note_id, target_widget):
        popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        vbox.set_margin_start(8)
        vbox.set_margin_end(8)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8, halign=Gtk.Align.CENTER)
        for i, color in enumerate(STICKY_COLORS):
            b = Gtk.Button()
            b.set_size_request(28, 28)
            cp = Gtk.CssProvider()
            cp.load_from_data(
                f"button {{ background-color: {color}; border-radius: 14px; min-width: 28px; min-height: 28px; padding: 0; }}".encode())
            b.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            b.connect("clicked", lambda _, c=color: self.update_note_color(note_id, c, target_widget, popover))
            grid.attach(b, i % 2, i // 2, 1, 1)

        vbox.append(grid)
        vbox.append(Gtk.Separator())

        btn_del = Gtk.Button(label="Move to Trash", has_frame=False)
        btn_del.connect("clicked", lambda _: (self.on_action_delete_manual(note_id), popover.popdown()))
        vbox.append(btn_del)

        popover.set_child(vbox)
        popover.set_parent(target_widget)
        popover.popup()


    def update_note_color(self, note_id, color, widget, popover):
        self.db.update_color(note_id, color)
        self.refresh_list()
        if note_id in self.stickies: self.stickies[note_id].apply_color(color)
        popover.popdown()