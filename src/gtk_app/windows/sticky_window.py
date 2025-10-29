"""Sticky note window (GTK4/libadwaita).

Rich text editing with formatting toolbar and menu options.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

import os
import time
from core.config import AUTOSAVE_INTERVAL_MS, COLOR_MAP, PROJECT_ROOT
from core.i18n import _
from gtk_app.widgets.rich_text_editor import RichTextEditor
from src.utils.error_logger import log_error, log_info, log_performance, log_freeze_warning


class StickyWindow(Adw.ApplicationWindow):
    def __init__(self, transient_for, db, note_id=None, **kwargs):
        init_start_time = time.time()
        log_info("StickyWindow.__init__ starting", note_id=note_id)
        
        try:
            super().__init__(transient_for=transient_for, **kwargs)
            log_info("StickyWindow super().__init__ complete")
            
            # Load UI from file
            builder = Gtk.Builder()
            ui_file = os.path.join(PROJECT_ROOT, "resources", "gtk", "ui", "sticky_window.ui")
            log_info("Loading UI from file", ui_file=ui_file)
            builder.add_from_file(ui_file)
            log_info("UI loaded successfully")
        
            # Get widgets from builder
            self.text_view = builder.get_object("text_view")
            self.menu_button = builder.get_object("menu_button")
            self.btn_toggle_toolbar = builder.get_object("btn_toggle_toolbar")
            self.toolbar_revealer = builder.get_object("toolbar_revealer")
        
            # Format toolbar widgets
            self.font_size_dropdown = builder.get_object("font_size_dropdown")
            self.btn_bold = builder.get_object("btn_bold")
            self.btn_italic = builder.get_object("btn_italic")
            self.btn_underline = builder.get_object("btn_underline")
            self.btn_strikethrough = builder.get_object("btn_strikethrough")
            self.text_color_button = builder.get_object("text_color_button")
            self.alignment_button = builder.get_object("alignment_button")
            self.bullet_list_button = builder.get_object("bullet_list_button")
            self.numbered_list_button = builder.get_object("numbered_list_button")
            self.btn_checklist = builder.get_object("btn_checklist")
            
            # Get the UI window and extract its content
            ui_window = builder.get_object("StickyWindow")
            main_box = builder.get_object("main_box")
            
            # Remove main_box from ui_window before setting it to our window
            if ui_window and main_box:
                ui_window.set_child(None)
            
            # Set up the window content
            self.set_content(main_box)
            self.set_default_size(400, 300)
            
            # Apply custom CSS for rounded corners
            self._apply_custom_css()
            
            self.db = db
            self.note_id = note_id
            log_info("DB and note_id set", note_id=note_id)

            # Initialize rich text editor
            log_info("Creating RichTextEditor")
            editor_start = time.time()
            self.editor = RichTextEditor(self.text_view)
            log_performance("RichTextEditor creation", time.time() - editor_start)
            
            self._buffer: Gtk.TextBuffer = self.text_view.get_buffer()
            self._always_on_top = 0
            self._current_alignment = "left"  # Track current alignment
            self._updating_format_ui = False  # Flag to prevent recursive updates
            
            # Setup toolbar toggle
            log_info("Connecting toolbar signals")
            self.btn_toggle_toolbar.connect("toggled", self._on_toolbar_toggle)
            
            # Track cursor position to update format buttons
            self._buffer.connect("notify::cursor-position", self._on_cursor_moved)
            
            # Setup menu
            log_info("Setting up menu")
            self._setup_menu()
            
            # Setup toolbar
            log_info("Setting up toolbar")
            toolbar_start = time.time()
            self._setup_toolbar()
            log_performance("Toolbar setup", time.time() - toolbar_start)

            if self.note_id:
                log_info("Loading note from DB", note_id=note_id)
                load_start = time.time()
                self._load_from_db()
                log_performance("Note load from DB", time.time() - load_start, note_id=note_id)

            # Start autosave timer
            log_info("Starting autosave timer", interval_ms=AUTOSAVE_INTERVAL_MS)
            GLib.timeout_add(AUTOSAVE_INTERVAL_MS, self._autosave)

            # Mark open
            if self.note_id:
                log_info("Marking note as open", note_id=note_id)
                try:
                    self.db.set_open_state(self.note_id, 1)
                except Exception as e:
                    log_error("Failed to mark note as open", exception=e, note_id=note_id)
            
            init_duration = time.time() - init_start_time
            log_performance("StickyWindow.__init__ COMPLETE", init_duration, note_id=note_id)
            
            # Warn if initialization took too long
            if init_duration > 1.0:
                log_freeze_warning("StickyWindow initialization slow", {
                    "duration_seconds": f"{init_duration:.2f}",
                    "note_id": note_id
                })
        
        except Exception as e:
            log_error("Critical error in StickyWindow.__init__", exception=e, note_id=note_id)
            raise

    def _load_from_db(self):
        try:
            row = self.db.get(self.note_id)
        except Exception:
            row = None
        if row:
            # Set window title
            title = row["title"] or "Untitled"
            self.set_title(title)
            
            content = row["content"] or ""
            
            # Try to load as formatted JSON content
            if content and content.strip().startswith('{'):
                # Looks like JSON
                self.editor.set_formatted_content(content)
            elif content:
                # Plain text (legacy or new plain notes)
                self.editor.set_text(content)
            
            self._always_on_top = int(row["always_on_top"]) if "always_on_top" in row.keys() else 0

    def _setup_menu(self):
        """Setup window menu."""
        menu = Gio.Menu()
        menu.append(_("Keep on Top"), "win.keep_above")
        menu.append(_("Pin"), "win.pin_window")
        menu.append(_("Settings"), "win.settings")
        
        popover = Gtk.PopoverMenu.new_from_model(menu)
        self.menu_button.set_popover(popover)
        
        # Actions (placeholder - will be implemented later)
        a_keep_above = Gio.SimpleAction.new("keep_above", None)
        a_keep_above.connect("activate", self._on_keep_above)
        self.add_action(a_keep_above)
        
        a_pin = Gio.SimpleAction.new("pin_window", None)
        a_pin.connect("activate", self._on_pin_window)
        self.add_action(a_pin)
        
        a_settings = Gio.SimpleAction.new("settings", None)
        a_settings.connect("activate", self._on_settings)
        self.add_action(a_settings)
    
    def _setup_toolbar(self):
        """Setup formatting toolbar."""
        # Font sizes
        font_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]
        size_model = Gtk.StringList.new(font_sizes)
        self.font_size_dropdown.set_model(size_model)
        self.font_size_dropdown.set_selected(4)  # Default to 12
        self.font_size_dropdown.connect("notify::selected", self._on_font_size_changed)
        
        # Format buttons
        self.btn_bold.connect("toggled", self._on_bold_toggled)
        self.btn_italic.connect("toggled", self._on_italic_toggled)
        self.btn_underline.connect("toggled", self._on_underline_toggled)
        self.btn_strikethrough.connect("toggled", self._on_strikethrough_toggled)
        
        # Text color
        self.text_color_button.connect("color-set", self._on_text_color_changed)
        
        # Alignment menu
        self._setup_alignment_menu()
        
        # List menus
        self._setup_list_menus()
        
        # Checklist
        self.btn_checklist.connect("clicked", self._on_checklist_clicked)
    
    def _setup_alignment_menu(self):
        """Setup alignment menu button."""
        align_menu = Gio.Menu()
        align_menu.append(_("Align Left"), "win.align_left")
        align_menu.append(_("Center"), "win.align_center")
        align_menu.append(_("Align Right"), "win.align_right")
        align_menu.append(_("Justify"), "win.align_fill")
        align_popover = Gtk.PopoverMenu.new_from_model(align_menu)
        self.alignment_button.set_popover(align_popover)
        
        a_left = Gio.SimpleAction.new("align_left", None)
        a_left.connect("activate", lambda *_: self._on_alignment_changed("left"))
        self.add_action(a_left)
        
        a_center = Gio.SimpleAction.new("align_center", None)
        a_center.connect("activate", lambda *_: self._on_alignment_changed("center"))
        self.add_action(a_center)
        
        a_right = Gio.SimpleAction.new("align_right", None)
        a_right.connect("activate", lambda *_: self._on_alignment_changed("right"))
        self.add_action(a_right)
        
        a_fill = Gio.SimpleAction.new("align_fill", None)
        a_fill.connect("activate", lambda *_: self._on_alignment_changed("fill"))
        self.add_action(a_fill)

    def _setup_list_menus(self):
        """Setup bullet and numbered list menus."""
        # Bullet list menu
        bullet_menu = Gio.Menu()
        bullet_menu.append(_("• Disc"), "win.bullet_disc")
        bullet_menu.append(_("- Dash"), "win.bullet_dash")
        bullet_popover = Gtk.PopoverMenu.new_from_model(bullet_menu)
        self.bullet_list_button.set_popover(bullet_popover)
        
        a_disc = Gio.SimpleAction.new("bullet_disc", None)
        a_disc.connect("activate", lambda *_: self._insert_bullet("•"))
        self.add_action(a_disc)
        
        a_dash = Gio.SimpleAction.new("bullet_dash", None)
        a_dash.connect("activate", lambda *_: self._insert_bullet("-"))
        self.add_action(a_dash)
        
        # Numbered list menu
        numbered_menu = Gio.Menu()
        numbered_menu.append(_("1,2,3... Numbers"), "win.number_arabic")
        numbered_menu.append(_("I,II,III... Roman"), "win.number_roman")
        numbered_menu.append(_("a,b,c... Alphabetic"), "win.number_alpha")
        numbered_popover = Gtk.PopoverMenu.new_from_model(numbered_menu)
        self.numbered_list_button.set_popover(numbered_popover)
        
        a_arabic = Gio.SimpleAction.new("number_arabic", None)
        a_arabic.connect("activate", lambda *_: self._insert_numbered_list("arabic"))
        self.add_action(a_arabic)
        
        a_roman = Gio.SimpleAction.new("number_roman", None)
        a_roman.connect("activate", lambda *_: self._insert_numbered_list("roman"))
        self.add_action(a_roman)
        
        a_alpha = Gio.SimpleAction.new("number_alpha", None)
        a_alpha.connect("activate", lambda *_: self._insert_numbered_list("alpha"))
        self.add_action(a_alpha)

    def refresh_menus_for_language_change(self):
        """Refresh all menus with new translations when language changes."""
        # Rebuild all menus with new translations
        self._setup_menu()
        self._setup_alignment_menu()
        self._setup_list_menus()

    def _apply_custom_css(self):
        """Apply custom CSS for rounded corners on sticky note."""
        css_provider = Gtk.CssProvider()
        css = b"""
        scrolledwindow {
            border-radius: 8px;
        }
        textview {
            border-radius: 6px;
            padding: 12px;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_toolbar_toggle(self, button):
        """Toggle format toolbar visibility."""
        is_active = button.get_active()
        self.toolbar_revealer.set_reveal_child(is_active)
    
    def _on_cursor_moved(self, buffer, *args):
        """Update format buttons based on cursor position."""
        from src.utils.error_logger import log_info
        
        # Skip if we're updating programmatically
        if hasattr(self, '_updating_format_ui') and self._updating_format_ui:
            return
        
        log_info("_on_cursor_moved: starting")
        self._updating_format_ui = True
        
        try:
            # Get cursor position
            cursor_mark = buffer.get_insert()
            cursor_iter = buffer.get_iter_at_mark(cursor_mark)
            
            log_info("_on_cursor_moved: got cursor iter")
            
            # Check for tags at cursor position
            tags = cursor_iter.get_tags()
            
            log_info("_on_cursor_moved: got tags", tag_count=len(tags))
            
            # Update font size dropdown
            current_size = 12  # default
            for tag in tags:
                tag_name = tag.get_property("name")
                if tag_name and tag_name.startswith("size_"):
                    try:
                        current_size = int(tag_name.replace("size_", ""))
                    except ValueError:
                        pass
            
            log_info("_on_cursor_moved: updating font size dropdown", size=current_size)
            
            # Find matching size in dropdown
            font_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]
            try:
                size_index = font_sizes.index(current_size)
                self.font_size_dropdown.set_selected(size_index)
            except ValueError:
                self.font_size_dropdown.set_selected(4)  # default to 12
            
            log_info("_on_cursor_moved: font size updated")
            
            # Update text color button
            current_color = "#ffffff"  # default
            for tag in tags:
                tag_name = tag.get_property("name")
                if tag_name and tag_name.startswith("color_"):
                    color_str = tag_name.replace("color_", "")
                    # If it's a hex color
                    if color_str.startswith("#"):
                        current_color = color_str
                    # If it's a named color, get from tag
                    else:
                        foreground = tag.get_property("foreground")
                        if foreground:
                            current_color = foreground
            
            log_info("_on_cursor_moved: updating color button", color=current_color)
            
            rgba = Gdk.RGBA()
            rgba.parse(current_color)
            self.text_color_button.set_rgba(rgba)
            
            log_info("_on_cursor_moved: updating toggle buttons")
            
            # Update toggle buttons
            has_bold = any(tag.get_property("name") == "bold" for tag in tags)
            has_italic = any(tag.get_property("name") == "italic" for tag in tags)
            has_underline = any(tag.get_property("name") == "underline" for tag in tags)
            has_strikethrough = any(tag.get_property("name") == "strikethrough" for tag in tags)
            
            self.btn_bold.set_active(has_bold)
            self.btn_italic.set_active(has_italic)
            self.btn_underline.set_active(has_underline)
            self.btn_strikethrough.set_active(has_strikethrough)
            
            log_info("_on_cursor_moved: complete")
        
        except Exception as e:
            log_error("Error in _on_cursor_moved", exception=e)
        finally:
            self._updating_format_ui = False

    # Menu handlers
    def _on_keep_above(self, *_):
        """Keep window above others - placeholder."""
        print("Keep above - To be implemented")
    
    def _on_pin_window(self, *_):
        """Pin window position - placeholder."""
        self._always_on_top = 0 if self._always_on_top else 1
        self._save_now()
        print(f"Pin window: {self._always_on_top}")
    
    def _on_settings(self, *_):
        """Show settings - placeholder."""
        print("Settings - To be implemented")

    # Format toolbar handlers
    def _on_font_size_changed(self, dropdown, _param):
        """Apply font size to selection or set default."""
        if hasattr(self, '_updating_format_ui') and self._updating_format_ui:
            return
        
        # Save selection before dropdown interaction
        self.editor.save_selection()
        
        selected = dropdown.get_selected()
        font_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]
        size = int(font_sizes[selected])
        self.editor.apply_font_size(size)
        
        # Restore selection and focus
        self.editor.restore_selection()
        self.text_view.grab_focus()
    
    def _on_bold_toggled(self, button):
        """Apply bold formatting."""
        if hasattr(self, '_updating_format_ui') and self._updating_format_ui:
            return
        
        self.editor.save_selection()
        self.editor.apply_bold(button.get_active())
        self.editor.restore_selection()
        self.text_view.grab_focus()
    
    def _on_italic_toggled(self, button):
        """Apply italic formatting."""
        if hasattr(self, '_updating_format_ui') and self._updating_format_ui:
            return
        
        self.editor.save_selection()
        self.editor.apply_italic(button.get_active())
        self.editor.restore_selection()
        self.text_view.grab_focus()
    
    def _on_underline_toggled(self, button):
        """Apply underline formatting."""
        if hasattr(self, '_updating_format_ui') and self._updating_format_ui:
            return
        
        self.editor.save_selection()
        self.editor.apply_underline(button.get_active())
        self.editor.restore_selection()
        self.text_view.grab_focus()
    
    def _on_strikethrough_toggled(self, button):
        """Apply strikethrough formatting."""
        if hasattr(self, '_updating_format_ui') and self._updating_format_ui:
            return
        
        self.editor.save_selection()
        self.editor.apply_strikethrough(button.get_active())
        self.editor.restore_selection()
        self.text_view.grab_focus()
    
    def _on_text_color_changed(self, color_button):
        """Apply text color to selection or set default."""
        if hasattr(self, '_updating_format_ui') and self._updating_format_ui:
            return
        
        self.editor.save_selection()
        rgba = color_button.get_rgba()
        self.editor.apply_text_color(rgba)
        self.editor.restore_selection()
        self.text_view.grab_focus()
    
    def _on_alignment_changed(self, alignment):
        """Apply paragraph alignment and update button icon."""
        self._current_alignment = alignment
        
        # Update icon based on alignment
        icon_map = {
            "left": "format-justify-left-symbolic",
            "center": "format-justify-center-symbolic",
            "right": "format-justify-right-symbolic",
            "fill": "format-justify-fill-symbolic"
        }
        self.alignment_button.set_icon_name(icon_map[alignment])
        
        self.editor.save_selection()
        self.editor.apply_alignment(alignment)
        self.editor.restore_selection()
        self.text_view.grab_focus()
    
    def _insert_bullet(self, bullet_char):
        """Insert bullet point."""
        self.editor.insert_bullet(bullet_char)
        self.text_view.grab_focus()
    
    def _insert_numbered_list(self, style):
        """Insert numbered list item."""
        self.editor.insert_numbered_list(style)
        self.text_view.grab_focus()
    
    def _on_checklist_clicked(self, *_):
        """Insert checklist item."""
        self.editor.insert_checklist_item()
        self.text_view.grab_focus()

    def _autosave(self):
        try:
            self._save_now()
        except Exception as e:
            log_error("Autosave failed", exception=e, note_id=self.note_id)
        return True

    def _save_now(self):
        save_start = time.time()
        log_info("_save_now called", note_id=self.note_id)
        
        try:
            # Get formatted content as JSON string
            content_start = time.time()
            content = self.editor.get_formatted_content()
            content_duration = time.time() - content_start
            
            log_performance("get_formatted_content in _save_now", content_duration,
                          content_length=len(content), note_id=self.note_id)
            
            # Warn if getting content was slow
            if content_duration > 0.5:
                log_freeze_warning("get_formatted_content slow in _save_now", {
                    "duration_seconds": f"{content_duration:.2f}",
                    "content_length": len(content),
                    "note_id": self.note_id
                })
            
            if self.note_id:
                # We don't track x/y/w/h here yet; keep previous values
                row = self.db.get(self.note_id)
                if row:
                    x, y, w, h = row["x"], row["y"], row["w"], row["h"]
                    log_info("Updating existing note", note_id=self.note_id)
                    
                    db_start = time.time()
                    self.db.update(self.note_id, content, x, y, w, h, 
                                 self.editor.default_bg_color, self._always_on_top)
                    db_duration = time.time() - db_start
                    
                    log_performance("Database update", db_duration, note_id=self.note_id)
                    
            save_duration = time.time() - save_start
            log_performance("_save_now total", save_duration, note_id=self.note_id)
            
        except Exception as e:
            log_error("Error in _save_now", exception=e, note_id=self.note_id)
