import gi
import json
from gi.repository import Gtk, Gdk, GLib, GObject, Pango, PangoCairo

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

STICKY_COLORS = ['#FFF59D', '#F8BBD0', '#C8E6C9', '#B3E5FC']
TEXT_COLORS = [
    '#000000', '#424242', '#D32F2F', '#C2185B',
    '#7B1FA2', '#303F9F', '#1976D2', '#0288D1',
    '#0097A7', '#00796B', '#388E3C', '#689F38',
    '#AFB42B', '#FBC02D', '#FFA000', '#E64A19'
]
FONT_SIZES = [8, 10, 12, 14, 16, 18, 20, 24, 32, 48, 72]
ALLOWED_TAGS = {"bold", "italic", "underline", "strikethrough"}


class StickyWindow(Gtk.Window):
    def __init__(self, db, note_id=None, main_window=None):
        super().__init__(decorated=False, default_width=300, default_height=380)
        self.add_css_class("sticky-window")

        self.db = db
        self.note_id = note_id
        self.main_window = main_window
        self._loading = True
        self.current_color = "#FFF59D"
        self.default_font_size = 12
        self.is_pinned = False

        # Переменные для хранения размеров при загрузке
        self.saved_width = 300
        self.saved_height = 380

        self.window_css_provider = Gtk.CssProvider()
        css_data = """
                .format-btn-tiny {
                    padding: 0px; margin: 0px;
                    min-height: 20px; min-width: 20px;
                    border-radius: 2px;
                    font-size: 10px;
                    background: transparent;
                    color: rgba(0,0,0,0.7);
                    border: none;
                }
                .format-btn-tiny:hover { background: rgba(0,0,0,0.05); color: black; }

                .compact-format-bar { padding: 1px; background: rgba(255,255,255,0.4); }

                .header-btn-subtle {
                    opacity: 0; transition: opacity 0.2s ease;
                    padding: 0 4px; margin: 0 1px;
                    min-height: 20px; min-width: 20px;
                    background: transparent; border: none; color: rgba(0,0,0,0.5);
                }
                .sticky-window:hover .header-btn-subtle { opacity: 1; }
                .header-btn-subtle:hover { background: rgba(0,0,0,0.1); color: black; }

                .menu-box { padding: 10px; }
                .menu-label { font-size: 10px; font-weight: bold; color: grey; margin-bottom: 5px; }
                .menu-row-btn { background: transparent; border: none; padding: 5px; border-radius: 4px; }
                .menu-row-btn:hover { background: rgba(0,0,0,0.05); }

                /* СТИЛЬ ДЛЯ СООБЩЕНИЯ (TOAST) */
                .toast-msg {
                    background-color: #262626; /* Темно-серый фон */
                    color: #ffffff;            /* Белый текст */
                    border-radius: 20px;       /* Округлые края (таблетка) */
                    padding: 8px 16px;         /* Отступы внутри */
                    margin: 20px;              /* Отступы от краев */
                    font-size: 13px;
                    font-weight: bold;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3); /* Тень для читаемости */
                }
                """
        self.window_css_provider.load_from_data(css_data.encode())
        self.get_style_context().add_provider(
            self.window_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

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

        self.load_from_db()
        self._loading = False

        GLib.timeout_add(2000, self.save)
        self.connect("close-request", self._on_close_requested)
        # Подключаем событие отображения окна для восстановления размеров
        self.connect("map", self._on_map)
        self.buffer.connect("notify::cursor-position", self.on_cursor_moved)

    def show_toast(self, message):
        """Показывает красивое сообщение по центру окна"""
        lbl = Gtk.Label(label=message)
        lbl.add_css_class("toast-msg")

        lbl.set_halign(Gtk.Align.CENTER)
        lbl.set_valign(Gtk.Align.CENTER)

        self.overlay.add_overlay(lbl)

        def _remove():
            self.overlay.remove_overlay(lbl)
            return False

        GLib.timeout_add(2000, _remove)

    def set_keep_above(self, state: bool):
        self.is_pinned = state

    def _on_map(self, widget):
        """Вызывается, когда окно отображается на экране"""
        self.set_keep_above(self.is_pinned)

        # Применяем сохраненные размеры
        if self.saved_width > 0 and self.saved_height > 0:
            self.set_default_size(self.saved_width, self.saved_height)

    def setup_header(self):
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_size_request(-1, 24)
        self.header_box.add_css_class("compact-header")

        btn_add = Gtk.Button(label="+", has_frame=False)
        btn_add.add_css_class("header-btn-subtle")
        btn_add.connect("clicked", self._on_add_clicked)
        self.header_box.append(btn_add)

        spacer = Gtk.Box(hexpand=True)
        spacer.set_can_target(True)
        header_drag = Gtk.GestureDrag()
        header_drag.connect("drag-begin", self._on_header_drag_begin)
        spacer.add_controller(header_drag)
        self.header_box.append(spacer)

        btn_menu = Gtk.MenuButton(has_frame=False)
        btn_menu.set_icon_name("open-menu-symbolic")
        btn_menu.add_css_class("header-btn-subtle")
        self.setup_main_menu(btn_menu)
        self.header_box.append(btn_menu)

        btn_close = Gtk.Button(label="✕", has_frame=False)
        btn_close.add_css_class("header-btn-subtle")
        btn_close.connect("clicked", self._on_close_clicked)
        self.header_box.append(btn_close)

        self.main_box.append(self.header_box)

    def setup_main_menu(self, btn):
        popover = Gtk.Popover()
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_vbox.add_css_class("menu-box")

        lbl_color = Gtk.Label(label="Color", xalign=0)
        lbl_color.add_css_class("menu-label")
        main_vbox.append(lbl_color)

        grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        for i, color in enumerate(STICKY_COLORS):
            b = Gtk.Button()
            b.set_size_request(26, 26)
            cp = Gtk.CssProvider()
            cp.load_from_data(
                f"button {{ background-color: {color}; border-radius: 13px; border: 1px solid rgba(0,0,0,0.1); padding: 0; }}".encode())
            b.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            b.connect("clicked", lambda _, c=color: (self.apply_color(c), popover.popdown()))
            grid.attach(b, i % 4, i // 4, 1, 1)
        main_vbox.append(grid)

        main_vbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        self.box_pin_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.img_pin = Gtk.Image()
        self.lbl_pin = Gtk.Label()
        self.box_pin_content.append(self.img_pin)
        self.box_pin_content.append(self.lbl_pin)

        btn_pin = Gtk.Button(has_frame=False)
        btn_pin.set_child(self.box_pin_content)
        btn_pin.add_css_class("menu-row-btn")
        self.box_pin_content.set_halign(Gtk.Align.START)

        btn_pin.connect("clicked", lambda _,: (self.toggle_pin(), popover.popdown()))
        main_vbox.append(btn_pin)

        box_print = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_print.append(Gtk.Image.new_from_icon_name("printer-symbolic"))
        box_print.append(Gtk.Label(label="Print note"))
        box_print.set_halign(Gtk.Align.START)

        btn_print = Gtk.Button(has_frame=False)
        btn_print.set_child(box_print)
        btn_print.add_css_class("menu-row-btn")
        btn_print.connect("clicked", lambda _,: (self.on_print_clicked(None), popover.popdown()))
        main_vbox.append(btn_print)

        popover.set_child(main_vbox)
        btn.set_popover(popover)

        self.update_pin_ui()

    def update_pin_ui(self):
        if self.is_pinned:
            self.img_pin.set_from_icon_name("view-pin-remove-symbolic")
            self.lbl_pin.set_text("Unpin note")
        else:
            self.img_pin.set_from_icon_name("view-pin-symbolic")
            self.lbl_pin.set_text("Pin note")

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.update_pin_ui()
        if not self._loading:
            try:
                self.db.set_always_on_top(self.note_id, 1 if self.is_pinned else 0)
            except Exception:
                pass
        if self.is_pinned:
            self.show_toast("Wayland doesn't support pinning")

    def setup_text_area(self):
        self.text_view = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.text_view.add_css_class("sticky-text-edit")
        self.buffer = self.text_view.get_buffer()
        self.buffer.connect("changed", self._on_buffer_changed)
        self.scrolled = Gtk.ScrolledWindow(child=self.text_view, vexpand=True)
        self.main_box.append(self.scrolled)

    def _on_buffer_changed(self, buffer):
        if self.main_window:
            content = self._serialize_buffer()
            self.main_window.update_card_text(self.note_id, content)

    def _serialize_buffer(self):
        import json
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        segments = []
        while not start_iter.equal(end_iter):
            next_iter = start_iter.copy()
            if not next_iter.forward_to_tag_toggle(None): next_iter = end_iter
            text = self.buffer.get_text(start_iter, next_iter, True)
            active_tags = [t.get_property("name") for t in start_iter.get_tags()]
            if text: segments.append({"text": text, "tags": active_tags})
            start_iter = next_iter
        if not segments: segments = [{"text": "", "tags": []}]
        json_str = json.dumps(segments)
        return json_str.encode('utf-8').hex()

    def setup_formatting_bar(self):
        self.format_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.format_bar.add_css_class("compact-format-bar")
        formats = [("<b>B</b>", "bold"), ("<i>I</i>", "italic"), ("<u>U</u>", "underline"),
                   ("<s>S</s>", "strikethrough")]
        for label, tag_name in formats:
            btn = Gtk.Button(has_frame=False)
            lbl = Gtk.Label(label=label, use_markup=True)
            btn.set_child(lbl)
            btn.add_css_class("format-btn-tiny")
            btn.connect("clicked", lambda _, t=tag_name: self.apply_format(t))
            self.format_bar.append(btn)
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(4);
        sep.set_margin_end(4)
        self.format_bar.append(sep)

        btn_text_color = Gtk.MenuButton(has_frame=False)
        btn_text_color.set_child(Gtk.Label(label='<span foreground="#444">A</span>', use_markup=True))
        btn_text_color.add_css_class("format-btn-tiny")
        self.setup_text_color_popover(btn_text_color)
        self.format_bar.append(btn_text_color)

        self.btn_font_size = Gtk.MenuButton(label=str(self.default_font_size), has_frame=False)
        self.btn_font_size.add_css_class("format-btn-tiny")
        self.setup_font_size_popover(self.btn_font_size)
        self.format_bar.append(self.btn_font_size)
        self.main_box.append(self.format_bar)

    def on_cursor_moved(self, buffer, pspec):
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

    def setup_tags(self):
        self.tag_table = self.buffer.get_tag_table()
        self.buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.buffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        self.buffer.create_tag("strikethrough", strikethrough=True)
        for color in TEXT_COLORS: self.buffer.create_tag(f"text_color_{color}", foreground=color)
        for size in FONT_SIZES: self.buffer.create_tag(f"font_size_{size}", size=size * Pango.SCALE)

    def save(self):
        if self._loading: return True
        # Сохранение контента...
        segments = []
        iter_curr = self.buffer.get_start_iter()
        iter_end = self.buffer.get_end_iter()
        while not iter_curr.equal(iter_end):
            iter_next = iter_curr.copy()
            if not iter_next.forward_to_tag_toggle(None): iter_next = iter_end
            text = self.buffer.get_text(iter_curr, iter_next, False)
            if text:
                tags = iter_curr.get_tags()
                tag_names = [t.props.name for t in tags if t.props.name and (
                        t.props.name in ALLOWED_TAGS or t.props.name.startswith(("text_color_", "font_size_")))]
                segments.append({"text": text, "tags": tag_names})
            iter_curr = iter_next
        try:
            json_str = json.dumps(segments)
            hex_data = json_str.encode('utf-8').hex()

            # --- СОХРАНЕНИЕ РАЗМЕРОВ ---
            # Получаем текущие размеры окна
            current_width = self.get_width()
            current_height = self.get_height()

            # Обновляем запись в БД
            # Порядок аргументов update: note_id, content, x, y, w, h, color, always_on_top
            self.db.update(
                self.note_id,
                hex_data,
                0, 0,  # X, Y (пропускаем в Wayland)
                current_width,
                current_height,
                self.current_color,
                1 if self.is_pinned else 0
            )
        except Exception:
            pass
        return True

    def load_from_db(self):
        if self.note_id:
            row = self.db.get(self.note_id)
            if row:
                self._loading = True
                content = row["content"] or ""
                self.buffer.set_text("")
                try:
                    json_bytes = bytes.fromhex(content)
                    segments = json.loads(json_bytes.decode('utf-8'))
                    iter_pos = self.buffer.get_start_iter()
                    for seg in segments:
                        text = seg.get("text", "")
                        tags = seg.get("tags", [])
                        if tags:
                            self.buffer.insert_with_tags_by_name(iter_pos, text, *tags)
                        else:
                            self.buffer.insert(iter_pos, text)
                except Exception:
                    self.buffer.set_text(content.replace("<br>", "\n"))

                self.apply_color(row["color"] or "#FFF59D")

                # --- ИСПРАВЛЕННАЯ ЗАГРУЗКА РАЗМЕРОВ ---
                # Используем ключи 'w' и 'h' и безопасный доступ
                try:
                    w = row['w']
                    h = row['h']
                    self.saved_width = w if w and w > 0 else 300
                    self.saved_height = h if h and h > 0 else 380
                except (IndexError, KeyError):
                    self.saved_width = 300
                    self.saved_height = 380

                # Загрузка флага pinned
                try:
                    pinned = row["always_on_top"]
                    self.is_pinned = bool(pinned)
                except (IndexError, KeyError):
                    self.is_pinned = False

                self.update_pin_ui()
                self._loading = False

    def setup_text_color_popover(self, btn):
        popover = Gtk.Popover()
        grid = Gtk.Grid(column_spacing=2, row_spacing=2)
        grid.set_margin_top(4);
        grid.set_margin_bottom(4);
        grid.set_margin_start(4);
        grid.set_margin_end(4)
        for i, color in enumerate(TEXT_COLORS):
            b = Gtk.Button()
            b.set_size_request(20, 20)
            cp = Gtk.CssProvider()
            cp.load_from_data(
                f"button {{ background-color: {color}; border-radius: 3px; border: 1px solid rgba(0,0,0,0.2); min-height: 20px; min-width: 20px; padding: 0; }}".encode())
            b.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            b.connect("clicked", lambda _, c=color: (self.apply_text_color(c), popover.popdown()))
            grid.attach(b, i % 4, i // 4, 1, 1)
        popover.set_child(grid)
        btn.set_popover(popover)

    def apply_text_color(self, hex_color):
        res = self.buffer.get_selection_bounds()
        if res:
            start, end = res
            for color in TEXT_COLORS: self.buffer.remove_tag_by_name(f"text_color_{color}", start, end)
            self.buffer.apply_tag_by_name(f"text_color_{hex_color}", start, end)
        self.text_view.grab_focus()

    def apply_font_size(self, size):
        res = self.buffer.get_selection_bounds()
        if res:
            start, end = res
            for s in FONT_SIZES: self.buffer.remove_tag_by_name(f"font_size_{s}", start, end)
            self.buffer.apply_tag_by_name(f"font_size_{size}", start, end)
        self.btn_font_size.set_label(str(size))
        self.text_view.grab_focus()

    def setup_font_size_popover(self, btn):
        popover = Gtk.Popover()
        scrolled = Gtk.ScrolledWindow(max_content_height=200, propagate_natural_height=True)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        for size in FONT_SIZES:
            b = Gtk.Button(label=f"{size}", has_frame=False)
            b.add_css_class("format-btn-tiny")
            b.connect("clicked", lambda _, s=size: (self.apply_font_size(s), popover.popdown()))
            vbox.append(b)
        scrolled.set_child(vbox)
        popover.set_child(scrolled)
        btn.set_popover(popover)

    def apply_format(self, tag_name):
        res = self.buffer.get_selection_bounds()
        if res:
            start, end = res
            tag = self.tag_table.lookup(tag_name)
            if start.has_tag(tag):
                self.buffer.remove_tag(tag, start, end)
            else:
                self.buffer.apply_tag(tag, start, end)
        self.text_view.grab_focus()

    def apply_color(self, hex_color):
        self.current_color = hex_color
        css = f"""
            window.sticky-window {{ 
                background-color: {hex_color}; 
                border-radius: 12px; 
                border: 1px solid rgba(0,0,0,0.1); 
            }}
            .sticky-text-edit, .sticky-text-edit text, textview, text {{ 
                background-color: transparent; background-image: none; color: #1a1a1a; 
            }}
            scrolledwindow {{ background-color: transparent; border: none; }}
            .sticky-main-area {{ background-color: transparent; margin: 0; }}
        """
        self.window_css_provider.load_from_data(css.encode('utf-8'))
        if self.main_window:
            self.main_window.update_card_color_live(self.note_id, hex_color)

    def setup_resize_handle(self):
        self.resize_handle = Gtk.Box()
        self.resize_handle.set_size_request(15, 15)
        self.resize_handle.set_halign(Gtk.Align.END);
        self.resize_handle.set_valign(Gtk.Align.END)
        self.resize_handle.set_cursor(Gdk.Cursor.new_from_name("se-resize", None))
        resize_drag = Gtk.GestureDrag()
        resize_drag.connect("drag-begin", self._on_resize_drag_begin)
        self.resize_handle.add_controller(resize_drag)
        self.overlay.add_overlay(self.resize_handle)

    def _on_header_drag_begin(self, gesture, x, y):
        surface = self.get_native().get_surface()
        if surface: surface.begin_move(gesture.get_device(), Gdk.BUTTON_PRIMARY, x, y, Gdk.CURRENT_TIME)

    def _on_resize_drag_begin(self, gesture, x, y):
        surface = self.get_native().get_surface()
        if surface: surface.begin_resize(Gdk.SurfaceEdge.SOUTH_EAST, gesture.get_device(), Gdk.BUTTON_PRIMARY, x, y,
                                         Gdk.CURRENT_TIME)

    def _on_add_clicked(self, button):
        if self.main_window: self.main_window.create_note()

    def _on_close_clicked(self, button):
        self.close()

    def _on_close_requested(self, window):
        if self.main_window and self.note_id in self.main_window.stickies:
            del self.main_window.stickies[self.note_id]
        return False

    def on_print_clicked(self, _):
        print_op = Gtk.PrintOperation()
        print_op.connect("draw-page", self._draw_page)
        print_op.set_n_pages(1)
        print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

    def _draw_page(self, operation, context, page_nr):
        cr = context.get_cairo_context()
        layout = context.create_pango_layout()
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, False)
        layout.set_text(text, -1)
        layout.set_width(int(context.get_width() * Pango.SCALE))
        PangoCairo.show_layout(cr, layout)