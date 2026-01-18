from gi.repository import Gtk, Adw, Gdk, GObject
from views.main_view.note_card import NoteCard  # Импортируем нашу общую карточку


class TrashView(Gtk.Box):
    def __init__(self, db, on_back_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.db = db
        self.on_back_callback = on_back_callback

        # --- Верхняя панель ---
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_top(10)
        header_box.set_margin_bottom(10)
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)

        btn_back = Gtk.Button(label="<<- Back")
        btn_back.connect("clicked", self._on_back_clicked)
        header_box.append(btn_back)

        lbl_title = Gtk.Label(label="Trash Bin")
        lbl_title.add_css_class("title-2")
        lbl_title.set_hexpand(True)
        header_box.append(lbl_title)

        spacer = Gtk.Box()
        spacer.set_size_request(80, -1)
        header_box.append(spacer)

        self.append(header_box)
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Область со стикерами (FlowBox) ---
        self.flowbox = Gtk.FlowBox(
            valign=Gtk.Align.START,
            selection_mode=Gtk.SelectionMode.NONE
        )

        scrolled = Gtk.ScrolledWindow(child=self.flowbox, vexpand=True)
        # Убираем рамку скролла для чистого вида
        scrolled.set_has_frame(False)
        self.append(scrolled)

        # --- Кнопка очистки ---
        action_bar = Gtk.ActionBar()
        btn_clear = Gtk.Button(label="Empty Trash")
        btn_clear.add_css_class("destructive-action")
        btn_clear.connect("clicked", self.on_empty_trash)

        action_bar.pack_end(btn_clear)
        self.append(action_bar)

        self.refresh_list()

    def _on_back_clicked(self, btn):
        if self.on_back_callback:
            self.on_back_callback()

    def refresh_list(self):
        while child := self.flowbox.get_first_child():
            self.flowbox.remove(child)

        # Настраиваем FlowBox как список (одна колонка)
        self.flowbox.set_homogeneous(False)
        self.flowbox.set_max_children_per_line(1)
        self.flowbox.set_min_children_per_line(1)
        self.flowbox.set_halign(Gtk.Align.FILL)
        self.flowbox.set_valign(Gtk.Align.START)

        # Отступы
        self.flowbox.set_column_spacing(0)
        self.flowbox.set_row_spacing(10)
        self.flowbox.set_margin_top(10)
        self.flowbox.set_margin_bottom(10)
        self.flowbox.set_margin_start(10)
        self.flowbox.set_margin_end(10)

        trash_items = self.db.all_trash()

        if not trash_items:
            # Заглушка, если пусто
            placeholder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            placeholder_box.set_valign(Gtk.Align.CENTER)
            placeholder_box.set_halign(Gtk.Align.CENTER)
            placeholder_box.set_vexpand(True)

            lbl = Gtk.Label(label="Trash is empty")
            lbl.add_css_class("dim-label")
            lbl.add_css_class("title-3")

            icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
            icon.set_pixel_size(64)
            icon.add_css_class("dim-label")

            placeholder_box.append(icon)
            placeholder_box.append(lbl)

            # Добавляем во FlowBox как единственный элемент
            self.flowbox.append(placeholder_box)
            # Настраиваем обертку
            child = placeholder_box.get_parent()
            child.set_hexpand(True)
            child.set_halign(Gtk.Align.FILL)
            return

        for note in trash_items:
            # Создаем карточку, передаем self.show_context_menu как колбэк
            card = NoteCard(note, self.db, menu_callback=self.show_context_menu)
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

    def show_context_menu(self, note_id, target_widget):
        """Контекстное меню специально для корзины"""
        popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_top(5);
        vbox.set_margin_bottom(5)
        vbox.set_margin_start(5);
        vbox.set_margin_end(5)

        # Кнопка восстановить
        btn_restore = Gtk.Button(label="Restore Note", has_frame=False)
        btn_restore.set_icon_name("edit-undo-symbolic")
        btn_restore.connect("clicked", lambda _: (self.restore_note(note_id), popover.popdown()))
        vbox.append(btn_restore)

        vbox.append(Gtk.Separator())

        # Кнопка удалить навсегда
        btn_del = Gtk.Button(label="Delete Permanently", has_frame=False)
        btn_del.add_css_class("destructive-action")
        btn_del.connect("clicked", lambda _: (self.delete_permanently(note_id), popover.popdown()))
        vbox.append(btn_del)

        popover.set_child(vbox)
        popover.set_parent(target_widget)
        popover.popup()

    def restore_note(self, note_id):
        self.db.restore_from_trash(note_id)
        self.refresh_list()

    def delete_permanently(self, note_id):
        self.db.delete_permanently(note_id)
        self.refresh_list()

    def on_empty_trash(self, btn):
        for note in self.db.all_trash():
            self.db.delete_permanently(note['id'])
        self.refresh_list()