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
        super().__init__()

        self.set_application(main_window.app)
        self.set_decorated(False)
        self.set_default_size(280, 350)
        self.add_css_class("sticky-window")
        self.set_title(f"Sticky Note {note_id}")
        self.set_name(f"sticky-note-{note_id}")

        self.db = db
        self.note_id = note_id
        self.main_window = main_window
        self.config = getattr(main_window, 'config', {})
        self._loading = True
        self.current_color = "#FFF59D"
        self.default_font_size = 12
        self.is_pinned = False
        self.saved_width = 300
        self.saved_height = 380

        # --- РАСЧЕТ МАСШТАБА ---
        try:
            raw_scale = self.config.get("ui_scale", 1.0)
            self.scale = float(str(raw_scale)[:4])
            if not (0.5 <= self.scale <= 3.0): self.scale = 1.0
        except:
            self.scale = 1.0

        # --- КОМПАКТНЫЕ РАЗМЕРЫ (-30%) ---
        scale = self.scale
        btn_size = int(18 * scale)
        header_h = int(22 * scale)
        font_tiny = int(9 * scale)
        handle_s = int(16 * scale)
        toast_pad_v = int(6 * scale)
        toast_pad_h = int(12 * scale)
        menu_pad = int(4 * scale)

        self.window_css_provider = Gtk.CssProvider()

        css_data = f"""
        .resize-handle {{
            background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.1) 50%);
            border-bottom-right-radius: 12px;
            min-width: {handle_s}px;
            min-height: {handle_s}px;
        }}
        .resize-handle:hover {{
            background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.2) 50%);
        }}
        .format-btn-tiny {{
            padding: 0px; margin: 0px;
            min-height: {btn_size}px; 
            min-width: {btn_size}px;
            border-radius: 2px;
            font-size: {font_tiny}px;
            background: transparent;
            color: rgba(0,0,0,0.7);
            border: none;
        }}
        .format-btn-tiny:hover {{ background: rgba(0,0,0,0.05); color: black; }}
        .compact-format-bar {{ padding: 1px; background: rgba(255,255,255,0.4); }}

        .compact-header {{
            min-height: {header_h}px;
        }}

        .header-btn-subtle {{
            opacity: 0; transition: opacity 0.2s ease;
            padding: 0 {int(3 * scale)}px; margin: 0 1px;
            min-height: {btn_size}px; min-width: {btn_size}px;
            background: transparent; border: none; color: rgba(0,0,0,0.5);
        }}
        .sticky-window:hover .header-btn-subtle {{ opacity: 1; }}
        .header-btn-subtle:hover {{ background: rgba(0,0,0,0.1); color: black; }}

        .menu-box {{ padding: {int(8 * scale)}px; }}
        .menu-label {{ font-size: {font_tiny}px; font-weight: bold; color: grey; margin-bottom: 4px; }}
        .menu-row-btn {{ background: transparent; border: none; padding: {menu_pad}px; border-radius: 4px; }}
        .menu-row-btn:hover {{ background: rgba(0,0,0,0.05); }}

        .toast-msg {{
            background-color: #262626;
            color: #ffffff;
            border-radius: 20px;
            padding: {toast_pad_v}px {toast_pad_h}px;
            margin: {int(20 * scale)}px;
            font-size: {int(12 * scale)}px;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
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

        # Контроллер для работы со списками
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.text_view.add_controller(key_controller)

        GLib.timeout_add(2000, self.save)
        self.connect("close-request", self._on_close_requested)
        self.connect("notify::default-width", lambda *_: self.save())
        self.connect("notify::default-height", lambda *_: self.save())
        self.connect("map", self._on_map)
        self.buffer.connect("notify::cursor-position", self.on_cursor_moved)

    def is_x11(self):
        display = Gdk.Display.get_default()
        return "X11" in display.__class__.__name__

    def _on_key_pressed(self, controller, keyval, keycode, state):
        BULLET_CHAR = " • "
        if keyval == Gdk.KEY_Return:
            cursor_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            line_start = cursor_iter.copy()
            line_start.set_line_offset(0)
            line_text = self.buffer.get_text(line_start, cursor_iter, False)

            if line_text.startswith(BULLET_CHAR):
                if line_text.strip() == BULLET_CHAR.strip():
                    self.buffer.delete(line_start, cursor_iter)
                    self.buffer.insert(cursor_iter, "\n")
                else:
                    self.buffer.insert(cursor_iter, f"\n{BULLET_CHAR}")
                return True
        return False

    def setup_formatting_bar(self):
        if hasattr(self, 'format_bar'):
            while child := self.format_bar.get_first_child():
                self.format_bar.remove(child)
        else:
            self.format_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            self.format_bar.add_css_class("compact-format-bar")
            self.main_box.append(self.format_bar)
        scale = self.scale
        icon_size = int(18 * scale)

        self.format_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.format_bar.add_css_class("compact-format-bar")

        # --- ПОЛУЧАЕМ НАСТРОЙКИ КНОПОК ---
        # Если ключа 'formatting' нет в конфиге, считаем все кнопки включенными (True)
        fmt_config = self.config.get("formatting", {})
        if not isinstance(fmt_config, dict): fmt_config = {}

        # 1. Основные кнопки (Bold, Italic, etc.)
        formats = [
            ("<b>B</b>", "bold"),
            ("<i>I</i>", "italic"),
            ("<u>U</u>", "underline"),
            ("<s>S</s>", "strikethrough")
        ]

        has_any_btn = False

        for label, tag_name in formats:
            # Проверяем конфиг для каждой кнопки
            if fmt_config.get(tag_name, True):
                btn = Gtk.Button(has_frame=False)
                lbl = Gtk.Label(label=label, use_markup=True)
                btn.set_child(lbl)
                btn.add_css_class("format-btn-tiny")
                btn.set_size_request(icon_size, icon_size)
                btn.connect("clicked", lambda _, t=tag_name: self.apply_format(t))
                self.format_bar.append(btn)
                has_any_btn = True

        # 2. Кнопка списка
        if fmt_config.get("list", True):
            btn_list = Gtk.Button(has_frame=False)
            btn_list.set_child(Gtk.Label(label="≡"))
            btn_list.add_css_class("format-btn-tiny")
            btn_list.set_size_request(icon_size, icon_size)
            btn_list.connect("clicked", lambda _: self.toggle_bullet_list())
            self.format_bar.append(btn_list)
            has_any_btn = True

        # 3. Разделитель (добавляем только если есть кнопки до и после)
        show_color = fmt_config.get("text_color", True)
        show_font = fmt_config.get("font_size", True)

        if has_any_btn and (show_color or show_font):
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep_margin = int(3 * scale)
            sep.set_margin_start(sep_margin)
            sep.set_margin_end(sep_margin)
            self.format_bar.append(sep)

        # 4. Цвет текста
        if show_color:
            btn_text_color = Gtk.MenuButton(has_frame=False)
            btn_text_color.set_child(Gtk.Label(label='<span foreground="#444">A</span>', use_markup=True))
            btn_text_color.add_css_class("format-btn-tiny")
            btn_text_color.set_size_request(icon_size, icon_size)
            self.setup_text_color_popover(btn_text_color)
            self.format_bar.append(btn_text_color)

        # 5. Размер шрифта
        if show_font:
            self.btn_font_size = Gtk.MenuButton(label=str(self.default_font_size), has_frame=False)
            self.btn_font_size.add_css_class("format-btn-tiny")
            self.btn_font_size.set_size_request(int(icon_size * 1.5), icon_size)
            self.setup_font_size_popover(self.btn_font_size)
            self.format_bar.append(self.btn_font_size)

        self.main_box.append(self.format_bar)

    def reload_config(self, new_config):
        self.config = new_config

        # Обновляем масштаб (если он изменился)
        try:
            raw_scale = self.config.get("ui_scale", 1.0)
            self.scale = float(str(raw_scale)[:4])
            if not (0.5 <= self.scale <= 3.0): self.scale = 1.0
        except:
            self.scale = 1.0

        # Пересоздаем панель кнопок с учетом новых галочек
        self.setup_formatting_bar()

        # Обновляем CSS (для применения нового масштаба шрифтов, если он изменился)
        # Применяем текущий цвет заново, чтобы перегенерировать CSS строку с новыми размерами
        self.apply_color(self.current_color)

    def toggle_bullet_list(self):
        BULLET_CHAR = " • "
        res = self.buffer.get_selection_bounds()
        if res:
            start, end = res
        else:
            start = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            end = start.copy()

        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()

        text = self.buffer.get_text(start, end, False)
        lines = text.split('\n')
        new_lines = []

        for line in lines:
            if line.startswith(BULLET_CHAR):
                new_lines.append(line[len(BULLET_CHAR):])
            else:
                new_lines.append(f"{BULLET_CHAR}{line}")

        self.buffer.begin_user_action()
        self.buffer.delete(start, end)
        self.buffer.insert(start, '\n'.join(new_lines))
        self.buffer.end_user_action()
        self.text_view.grab_focus()

    def on_cursor_moved(self, buffer, pspec):
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

    def show_toast(self, message):
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
        self.set_keep_above(self.is_pinned)

        # 1. Восстанавливаем размер (это работает везде)
        if self.saved_width > 0 and self.saved_height > 0:
            self.set_default_size(self.saved_width, self.saved_height)

        # 2. Восстанавливаем позицию (только X11)
        display = Gdk.Display.get_default()
        if "X11" in display.__class__.__name__:
            try:
                row = self.db.get(self.note_id)
                # X11 restore logic placeholder
                pass
            except Exception as e:
                print(f"Position restore error: {e}")

    def setup_header(self):
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # Компактный заголовок (22px base)
        self.header_box.set_size_request(-1, int(22 * self.scale))
        self.header_box.add_css_class("compact-header")

        btn_add = Gtk.Button(label="+", has_frame=False)
        btn_add.add_css_class("header-btn-subtle")
        btn_add.connect("clicked", self._on_add_clicked)
        self.header_box.append(btn_add)

        spacer = Gtk.Box(hexpand=True)
        spacer.set_can_target(True)
        header_drag = Gtk.GestureDrag()
        header_drag.connect("drag-begin", self._on_header_drag_begin)
        header_drag.connect("drag-update", self._on_header_drag_update)
        header_drag.connect("drag-end", self._on_header_drag_end)

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
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(4 * self.scale))
        main_vbox.add_css_class("menu-box")

        lbl_color = Gtk.Label(label="Color", xalign=0)
        lbl_color.add_css_class("menu-label")
        main_vbox.append(lbl_color)

        grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        btn_size = int(22 * self.scale)

        for i, color in enumerate(STICKY_COLORS):
            b = Gtk.Button()
            b.set_size_request(btn_size, btn_size)
            cp = Gtk.CssProvider()
            cp.load_from_data(
                f"button {{ background-color: {color}; border-radius: 50%; min-width: {btn_size}px; min-height: {btn_size}px; border: 1px solid rgba(0,0,0,0.1); padding: 0; }}".encode())
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
        return json.dumps(segments).encode('utf-8').hex()

    def setup_tags(self):
        self.tag_table = self.buffer.get_tag_table()
        self.buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.buffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        self.buffer.create_tag("strikethrough", strikethrough=True)
        for color in TEXT_COLORS: self.buffer.create_tag(f"text_color_{color}", foreground=color)
        for size in FONT_SIZES: self.buffer.create_tag(f"font_size_{size}", size=size * Pango.SCALE)

    def load_from_db(self):
        if self.note_id:
            row = self.db.get(self.note_id)
            if row:
                self._loading = True
                content = row["content"] or ""
                self.buffer.set_text("")
                try:
                    segments = json.loads(bytes.fromhex(content).decode('utf-8'))
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

                self.saved_width = row['w'] if row['w'] else 300
                self.saved_height = row['h'] if row['h'] else 380

                try:
                    self.is_pinned = bool(row["always_on_top"])
                except (IndexError, KeyError):
                    self.is_pinned = False

                self.update_pin_ui()
                self._loading = False

    def setup_text_color_popover(self, btn):
        popover = Gtk.Popover()
        grid = Gtk.Grid(column_spacing=2, row_spacing=2)
        grid.set_margin_top(4)
        grid.set_margin_bottom(4)
        grid.set_margin_start(4)
        grid.set_margin_end(4)

        btn_size = int(18 * self.scale)  # Компактные кнопки цвета

        for i, color in enumerate(TEXT_COLORS):
            b = Gtk.Button();
            b.set_size_request(btn_size, btn_size)
            cp = Gtk.CssProvider()
            cp.load_from_data(
                f"button {{ background-color: {color}; border-radius: 3px; border: 1px solid rgba(0,0,0,0.2); min-height: {btn_size}px; min-width: {btn_size}px; padding: 0; }}".encode())
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
        if hasattr(self, 'btn_font_size'): self.btn_font_size.set_label(str(size))
        self.text_view.grab_focus()

    def setup_font_size_popover(self, btn):
        popover = Gtk.Popover()
        scrolled = Gtk.ScrolledWindow(max_content_height=int(200 * self.scale), propagate_natural_height=True)
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
        css = f"window.sticky-window {{ background-color: {hex_color}; border-radius: 12px; border: 1px solid rgba(0,0,0,0.1); }} .sticky-text-edit, .sticky-text-edit text, textview, text {{ background-color: transparent; color: #1a1a1a; }} scrolledwindow {{ background-color: transparent; border: none; }} .sticky-main-area {{ background-color: transparent; margin: 0; }}"
        self.window_css_provider.load_from_data(css.encode('utf-8'))
        if self.main_window: self.main_window.update_card_color_live(self.note_id, hex_color)

    def setup_resize_handle(self):
        self.resize_handle = Gtk.Box()
        size = int(16 * self.scale)  # Компактная ручка
        self.resize_handle.set_size_request(size, size)
        self.resize_handle.set_halign(Gtk.Align.END)
        self.resize_handle.set_valign(Gtk.Align.END)
        self.resize_handle.add_css_class("resize-handle")

        self.resize_handle.set_cursor(Gdk.Cursor.new_from_name("se-resize", None))

        click_gest = Gtk.GestureClick()
        click_gest.connect("pressed", self._on_resize_pressed)
        self.resize_handle.add_controller(click_gest)

        self.overlay.add_overlay(self.resize_handle)

    def _on_resize_pressed(self, gesture, n_press, x, y):
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
        surface = self.get_native().get_surface()
        if not surface:
            return

        surface.begin_move(
            gesture.get_device(),
            Gdk.BUTTON_PRIMARY,
            x,
            y,
            Gdk.CURRENT_TIME
        )

        if self.is_x11():
            self._drag_offset_x = x
            self._drag_offset_y = y

    def _on_header_drag_update(self, gesture, dx, dy):
        if not self.is_x11():
            return

        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        pointer = seat.get_pointer()

        # X11 only
        screen, px, py = pointer.get_position()

        self.last_x = int(px - self._drag_offset_x)
        self.last_y = int(py - self._drag_offset_y)

    def _on_header_drag_end(self, gesture, dx, dy):
        if not self.is_x11():
            return

        self.saved_x = getattr(self, "last_x", 0)
        self.saved_y = getattr(self, "last_y", 0)

    def _on_resize_drag_begin(self, gesture, x, y):
        surface = self.get_native().get_surface()
        if surface: surface.begin_resize(Gdk.SurfaceEdge.SOUTH_EAST, gesture.get_device(), Gdk.BUTTON_PRIMARY, x, y,
                                         Gdk.CURRENT_TIME)

    def _on_add_clicked(self, button):
        if self.main_window: self.main_window.create_note()

    def _on_close_clicked(self, button):
        self.close()

    def _on_close_requested(self, window):
        if self.main_window and self.note_id in self.main_window.stickies: del self.main_window.stickies[self.note_id]
        return False

    def on_print_clicked(self, _):
        print_op = Gtk.PrintOperation()
        print_op.connect("draw-page", self._draw_page);
        print_op.set_n_pages(1)
        print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

    def _draw_page(self, operation, context, page_nr):
        cr = context.get_cairo_context()
        layout = context.create_pango_layout()
        start, end = self.buffer.get_bounds()
        layout.set_text(self.buffer.get_text(start, end, False), -1)
        layout.set_width(int(context.get_width() * Pango.SCALE))
        PangoCairo.show_layout(cr, layout)

    def save(self):
        if self._loading or not self.get_visible():
            return True

        try:
            hex_data = self._serialize_buffer()
            w = self.get_width()
            h = self.get_height()

            self.db.update(
                self.note_id,
                hex_data,
                0, 0,
                w, h,
                self.current_color,
                1 if self.is_pinned else 0
            )
        except Exception as e:
            print(f"DEBUG: Save minimized to content/size only: {e}")
        return True