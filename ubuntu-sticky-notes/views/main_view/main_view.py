import builtins
from gi.repository import Gtk, Adw, Gio, Gdk, GLib
from views.main_view.note_card import NoteCard
from sticky.sticky_window import StickyWindow
from views.settings_view import SettingsView
from views.trash_view import TrashView

_ = builtins._

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, db, application, **kwargs):
        super().__init__(application=application,
                         title=_("Ubuntu Sticky Notes"),
                         default_width=200,
                         default_height=600, **kwargs)
        self.set_size_request(100, -1)
        self.app = application
        self.db = db
        self.config = application.config
        self.stickies = {}

        css_provider = Gtk.CssProvider()
        css = """
                flowbox { padding: 0px; background: transparent; }
                flowboxchild { padding: 0px; margin: 0px; border: none; min-width: 0px; outline: none; }
                window.background { background-color: #ffffff; } 
                """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.setup_actions()

        # === STACK ===
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        self.set_content(self.stack)

        # 2. (MAIN)
        self.main_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

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

        btn_settings = Gtk.Button(icon_name="emblem-system-symbolic")
        btn_settings.add_css_class("flat")
        btn_settings.connect("clicked", self.on_show_settings)
        header_bar.pack_end(btn_settings)

        self.main_page_box.append(header_bar)

        self.search_entry = Gtk.SearchEntry(placeholder_text=_("Search..."))
        self.search_entry.set_margin_start(10)
        self.search_entry.set_margin_end(10)
        self.search_entry.set_margin_top(10)
        self.search_entry.set_margin_bottom(10)
        self.search_entry.connect("search-changed", self.on_search)
        self.main_page_box.append(self.search_entry)

        self.flowbox = Gtk.FlowBox(
            valign=Gtk.Align.START,
            selection_mode=Gtk.SelectionMode.NONE
        )

        scrolled = Gtk.ScrolledWindow(child=self.flowbox, vexpand=True)
        scrolled.set_has_frame(False)
        self.main_page_box.append(scrolled)

        # Pages
        self.stack.add_named(self.main_page_box, "main")

        self.trash_view = TrashView(self.db, on_back_callback=self.go_back_to_main)
        self.stack.add_named(self.trash_view, "trash")

        self.settings_view = SettingsView(
            on_back_callback=self.go_back_to_main,
            on_settings_change_callback=self.on_settings_changed
        )
        self.stack.add_named(self.settings_view, "settings")

        self.stack.set_visible_child_name("main")
        self.refresh_list()

    def on_settings_changed(self):
        print("DEBUG: Applying settings live...")
        from config.config_manager import ConfigManager
        self.config = ConfigManager.load()

        for note_id, sticky_window in self.stickies.items():
            if hasattr(sticky_window, 'reload_config'):
                sticky_window.reload_config(self.config)

    def on_show_settings(self, btn):
        self.stack.set_visible_child_name("settings")

    def on_show_trash(self, btn):
        self.trash_view.refresh_list()
        self.stack.set_visible_child_name("trash")

    def go_back_to_main(self):
        self.refresh_list()
        self.stack.set_visible_child_name("main")

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
            card = NoteCard(note, self.db, refresh_callback=self.refresh_list)
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
        note_id = self.db.add(color=self.config.get("palette", ["#FFF59D"])[0])
        self.refresh_list()
        self.open_note(note_id)

    def open_note(self, note_id):
        if note_id in self.stickies:
            existing_win = self.stickies[note_id]
            # Check if the window is still valid (not destroyed)
            if existing_win.get_native():
                existing_win.present()
                return
            else:
                # Window is destroyed but still in the list, remove it
                del self.stickies[note_id]

        new_sticky = StickyWindow(self.db, note_id, self)
        self.stickies[note_id] = new_sticky
        new_sticky.present()

    def on_sticky_closed(self, note_id):
        """Called by StickyWindow when it is about to close."""
        if note_id in self.stickies:
            del self.stickies[note_id]

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
        child = self.flowbox.get_first_child()
        while child:
            card = child.get_child()
            if isinstance(card, NoteCard) and card.note_id == note_id:
                new_markup = card._generate_markup(serialized_content)
                card.label.set_markup(new_markup)
                break
            child = child.get_next_sibling()

    def update_card_color_live(self, note_id, color):
        child = self.flowbox.get_first_child()
        while child:
            card = child.get_child()
            if isinstance(card, NoteCard) and card.note_id == note_id:
                card.update_color(color)
                break
            child = child.get_next_sibling()

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
        
        # Use palette from config
        palette = self.config.get("palette", [])
        
        for i, color in enumerate(palette):
            b = Gtk.Button()
            b.set_size_request(28, 28)
            cp = Gtk.CssProvider()
            cp.load_from_data(
                f"button {{ background-color: {color}; border-radius: 14px; min-width: 28px; min-height: 28px; padding: 0; }}".encode())
            b.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            b.connect("clicked", lambda _, c=color: self.update_note_color(note_id, c, target_widget, popover))
            grid.attach(b, i % 4, i // 4, 1, 1)

        vbox.append(grid)
        vbox.append(Gtk.Separator())

        btn_del = Gtk.Button(label=_("Move to Trash"), has_frame=False)
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
