import json
import html as html_lib
from gi.repository import Gtk, Pango


class NoteCard(Gtk.Box):
    def __init__(self, note, db, menu_callback=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.note_id = note["id"]
        self.menu_callback = menu_callback  # Функция для вызова меню (опционально)

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
        if not raw_content: return ""

        # 1. Пытаемся обработать как новый формат (HEX -> JSON)
        try:
            # Проверка: если это не HEX-строка, вызовет ValueError
            json_bytes = bytes.fromhex(raw_content)
            segments = json.loads(json_bytes.decode('utf-8'))

            full_markup = ""
            line_count = 0

            for seg in segments:
                text = seg.get("text", "")

                # Считаем строки для лимита
                lines_in_seg = text.split('\n')
                if line_count >= 5: break

                if line_count + len(lines_in_seg) - 1 >= 5:
                    allowed = 5 - line_count
                    text = "\n".join(lines_in_seg[:allowed])
                    line_count = 5
                else:
                    line_count += len(lines_in_seg) - 1

                # Экранируем текст, чтобы пользовательские < > не ломали разметку
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
            # 2. Если упали здесь - значит это СТАРЫЙ формат или простой текст
            # Сначала заменяем <br> на переносы строк (для старых заметок)
            text_content = str(raw_content).replace("<br>", "\n")

            # Обрезаем до 5 строк
            lines = text_content.split('\n')
            if len(lines) > 5:
                text_content = "\n".join(lines[:5])

            # ВАЖНО: Экранируем текст, чтобы теги не исполнялись, но были читаемыми,
            # но если в тексте были HTML теги (например <b>), мы хотим их видеть как текст?
            # Если вы хотите, чтобы старые HTML теги (если они есть) работали, уберите html_lib.escape.
            # Но безопаснее оставить escape, чтобы не ломать Pango.

            # Если проблема именно в том, что вы видите <b>текст</b>, значит
            # html_lib.escape превращает '<' в '&lt;'.

            # Попробуем вернуть просто экранированный текст:
            return html_lib.escape(text_content).rstrip()

    def update_color(self, hex_color):
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
        # Левый клик - открыть заметку (стандартно)
        click = Gtk.GestureClick()
        click.connect("released", lambda *args: self.get_native().open_note(self.note_id))
        self.add_controller(click)

        # Правый клик - контекстное меню
        menu = Gtk.GestureClick(button=3)
        menu.connect("pressed", self._on_right_click)
        self.add_controller(menu)

    def _on_right_click(self, gesture, n, x, y):
        # Если передан специальный колбэк (для корзины), используем его
        if self.menu_callback:
            self.menu_callback(self.note_id, self.card_canvas)
        else:
            # Иначе вызываем стандартное меню главного окна
            self.get_native().create_combined_context_menu(self.note_id, self.card_canvas)