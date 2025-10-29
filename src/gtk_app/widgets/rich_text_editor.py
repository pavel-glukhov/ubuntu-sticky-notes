"""Rich text editor widget with formatting support.

GTK4-based rich text editor with proper tag management:
- Only selected text is affected by formatting changes
- Tags are registered once and reused (not recreated)
- Preserves undo/redo functionality
- Supports bullet lists and checklists with Enter key continuation
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Pango
import time
from src.utils.error_logger import log_error, log_warning, log_performance, log_freeze_warning


class RichTextEditor:
    """Handles rich text editing and formatting for TextView."""
    
    def __init__(self, text_view: Gtk.TextView):
        self.text_view = text_view
        self.buffer = text_view.get_buffer()
        
        # Current formatting state (for next typed characters when no selection)
        self.current_font_size = 12
        self.current_text_color = "#ffffff"
        self.default_bg_color = "#2e3436"
        
        # Save cursor/selection position when focus is lost
        self._saved_selection_start = None
        self._saved_selection_end = None
        
        # Predefined tags for reuse
        self._tags = {}
        self._setup_tag_table()
        
        # Apply background color
        self.set_default_bg_color(self.default_bg_color)
        
        # Connect signals for smart paragraph behavior
        self.buffer.connect("insert-text", self._on_insert_text)
        
        # GTK4: Use EventControllerFocus for focus tracking
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("enter", self._on_focus_in)
        focus_controller.connect("leave", self._on_focus_out)
        self.text_view.add_controller(focus_controller)
        
    def _setup_tag_table(self):
        """Create reusable tags and register them in the tag table."""
        tag_table = self.buffer.get_tag_table()
        
        # Font size tags (8-72pt)
        for size in [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]:
            tag_name = f"size_{size}"
            tag = self.buffer.create_tag(tag_name, size=size * Pango.SCALE)
            self._tags[tag_name] = tag
        
        # Common color tags
        colors = {
            "white": "#ffffff",
            "black": "#000000", 
            "red": "#ff0000",
            "green": "#00ff00",
            "blue": "#0000ff",
            "yellow": "#ffff00",
            "orange": "#ff8800",
            "purple": "#800080",
            "pink": "#ff00ff",
            "gray": "#808080"
        }
        for name, hex_color in colors.items():
            tag_name = f"color_{name}"
            tag = self.buffer.create_tag(tag_name, foreground=hex_color)
            self._tags[tag_name] = tag
        
        # Bold, italic, underline, strikethrough
        self._tags["bold"] = self.buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self._tags["italic"] = self.buffer.create_tag("italic", style=Pango.Style.ITALIC)
        self._tags["underline"] = self.buffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        self._tags["strikethrough"] = self.buffer.create_tag("strikethrough", strikethrough=True)
        
        # Alignment tags
        self._tags["align_left"] = self.buffer.create_tag("align_left", justification=Gtk.Justification.LEFT)
        self._tags["align_center"] = self.buffer.create_tag("align_center", justification=Gtk.Justification.CENTER)
        self._tags["align_right"] = self.buffer.create_tag("align_right", justification=Gtk.Justification.RIGHT)
        self._tags["align_fill"] = self.buffer.create_tag("align_fill", justification=Gtk.Justification.FILL)
    
    def _get_or_create_color_tag(self, hex_color: str):
        """Get or create a color tag for any hex color."""
        tag_name = f"color_{hex_color}"
        if tag_name not in self._tags:
            self._tags[tag_name] = self.buffer.create_tag(tag_name, foreground=hex_color)
        return self._tags[tag_name]
    
    def _remove_tags_by_prefix(self, start, end, prefix: str):
        """Remove all tags starting with a specific prefix from a range."""
        for tag_name, tag in self._tags.items():
            if tag_name.startswith(prefix):
                self.buffer.remove_tag(tag, start, end)
    
    def set_default_bg_color(self, color: str):
        """Set background color via CSS."""
        self.default_bg_color = color
        css = f"textview {{ background-color: {color}; }}"
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode("utf-8"))
        self.text_view.get_style_context().add_provider(
            provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
    
    def apply_font_size(self, size: int):
        """Apply font size to selection only (or set for next typed characters)."""
        from src.utils.error_logger import log_info
        log_info("apply_font_size called", size=size)
        
        self.current_font_size = size
        tag_name = f"size_{size}"
        
        if tag_name not in self._tags:
            # Create tag if size is not predefined
            self._tags[tag_name] = self.buffer.create_tag(tag_name, size=size * Pango.SCALE)
        
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self.buffer.begin_user_action()
            
            # Remove all size tags from selection
            self._remove_tags_by_prefix(start, end, "size_")
            
            # Apply new size tag
            self.buffer.apply_tag(self._tags[tag_name], start, end)
            self.buffer.end_user_action()
        else:
            # No selection - will apply to next typed characters via insert mark
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            cursor_copy = cursor.copy()
            cursor_copy.forward_char()
            if cursor.compare(cursor_copy) != 0:
                self._remove_tags_by_prefix(cursor, cursor_copy, "size_")
                self.buffer.apply_tag(self._tags[tag_name], cursor, cursor_copy)
        
        log_info("apply_font_size complete", size=size)
    
    def apply_text_color(self, rgba: Gdk.RGBA):
        """Apply text color to selection only (or set for next typed characters)."""
        # Convert RGBA to hex
        hex_color = f"#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.current_text_color = hex_color
        
        tag = self._get_or_create_color_tag(hex_color)
        
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self.buffer.begin_user_action()
            
            # Remove all color tags from selection
            self._remove_tags_by_prefix(start, end, "color_")
            
            # Apply new color tag
            self.buffer.apply_tag(tag, start, end)
            self.buffer.end_user_action()
        else:
            # No selection - will apply to next typed characters
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            cursor_copy = cursor.copy()
            cursor_copy.forward_char()
            if cursor.compare(cursor_copy) != 0:
                self._remove_tags_by_prefix(cursor, cursor_copy, "color_")
                self.buffer.apply_tag(tag, cursor, cursor_copy)
    
    def apply_bold(self, active: bool):
        """Apply bold to selection only."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self.buffer.begin_user_action()
            
            if active:
                self.buffer.apply_tag(self._tags["bold"], start, end)
            else:
                self.buffer.remove_tag(self._tags["bold"], start, end)
            
            self.buffer.end_user_action()
    
    def apply_italic(self, active: bool):
        """Apply italic to selection only."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self.buffer.begin_user_action()
            
            if active:
                self.buffer.apply_tag(self._tags["italic"], start, end)
            else:
                self.buffer.remove_tag(self._tags["italic"], start, end)
            
            self.buffer.end_user_action()
    
    def apply_underline(self, active: bool):
        """Apply underline to selection only."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self.buffer.begin_user_action()
            
            if active:
                self.buffer.apply_tag(self._tags["underline"], start, end)
            else:
                self.buffer.remove_tag(self._tags["underline"], start, end)
            
            self.buffer.end_user_action()
    
    def apply_strikethrough(self, active: bool):
        """Apply strikethrough to selection only."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self.buffer.begin_user_action()
            
            if active:
                self.buffer.apply_tag(self._tags["strikethrough"], start, end)
            else:
                self.buffer.remove_tag(self._tags["strikethrough"], start, end)
            
            self.buffer.end_user_action()
    
    def apply_alignment(self, alignment: str):
        """Apply paragraph alignment to selection or current paragraph."""
        tag_name = f"align_{alignment}"
        if tag_name not in self._tags:
            return
        
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
        else:
            # No selection - apply to current paragraph
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            start = cursor.copy()
            start.set_line_offset(0)
            end = cursor.copy()
            if not end.ends_line():
                end.forward_to_line_end()
        
        self.buffer.begin_user_action()
        
        # Remove all alignment tags
        self._remove_tags_by_prefix(start, end, "align_")
        
        # Apply new alignment
        self.buffer.apply_tag(self._tags[tag_name], start, end)
        self.buffer.end_user_action()
    
    def insert_bullet(self, bullet_char: str):
        """Insert bullet point at cursor."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.begin_user_action()
        self.buffer.insert(cursor, f"{bullet_char} ")
        self.buffer.end_user_action()
    
    def insert_numbered_list(self, style: str):
        """Insert numbered list item at cursor."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.begin_user_action()
        if style == "arabic":
            self.buffer.insert(cursor, "1. ")
        elif style == "roman":
            self.buffer.insert(cursor, "I. ")
        elif style == "alpha":
            self.buffer.insert(cursor, "a. ")
        self.buffer.end_user_action()
    
    def insert_checklist_item(self):
        """Insert checklist item at cursor."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.begin_user_action()
        self.buffer.insert(cursor, "☐ ")
        self.buffer.end_user_action()
    
    def _on_insert_text(self, buffer, location, text, length):
        """Handle Enter key to continue bullet lists and checklists."""
        from src.utils.error_logger import log_info
        
        # Only log if it's a newline (to avoid spam)
        if text == "\n":
            log_info("_on_insert_text: newline detected")
        
        if text == "\n":
            # Get the line we just left
            line_iter = location.copy()
            line_iter.backward_char()
            
            if line_iter.get_line_offset() == 0:
                return  # At start of buffer
            
            # Get start of previous line
            line_start = line_iter.copy()
            line_start.set_line_offset(0)
            
            # Get text of previous line
            line_text = buffer.get_text(line_start, line_iter, False)
            
            log_info("_on_insert_text: checking line", line_text=line_text[:50])
            
            # Check for bullet patterns
            if line_text.strip().startswith("• "):
                # Continue bullet list
                log_info("_on_insert_text: continuing bullet list")
                Gdk.threads_add_idle(0, lambda: self._insert_at_cursor("• "))
            elif line_text.strip().startswith("- "):
                # Continue dash list
                log_info("_on_insert_text: continuing dash list")
                Gdk.threads_add_idle(0, lambda: self._insert_at_cursor("- "))
            elif line_text.strip().startswith("☐ "):
                # Continue checklist
                log_info("_on_insert_text: continuing checklist")
                Gdk.threads_add_idle(0, lambda: self._insert_at_cursor("☐ "))
            elif line_text.strip().startswith("✔ "):
                # Continue with unchecked
                log_info("_on_insert_text: continuing checklist (from checked)")
                Gdk.threads_add_idle(0, lambda: self._insert_at_cursor("☐ "))
            
            log_info("_on_insert_text: complete")
    
    def _insert_at_cursor(self, text: str):
        """Helper to insert text at cursor position."""
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.insert(cursor, text)
        return False  # Remove idle callback
    
    def _on_focus_out(self, controller):
        """Save cursor/selection position when focus is lost (GTK4)."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            # Save selection
            start, end = bounds
            self._saved_selection_start = start.get_offset()
            self._saved_selection_end = end.get_offset()
        else:
            # Save cursor position only
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            self._saved_selection_start = cursor.get_offset()
            self._saved_selection_end = None
    
    def _on_focus_in(self, controller):
        """Restore cursor/selection position when focus is regained (GTK4)."""
        if self._saved_selection_start is not None:
            start_iter = self.buffer.get_iter_at_offset(self._saved_selection_start)
            
            if self._saved_selection_end is not None:
                # Restore selection
                end_iter = self.buffer.get_iter_at_offset(self._saved_selection_end)
                self.buffer.select_range(start_iter, end_iter)
            else:
                # Restore cursor only
                self.buffer.place_cursor(start_iter)
            
            # Scroll to make cursor visible
            self.text_view.scroll_to_mark(self.buffer.get_insert(), 0.0, False, 0.0, 0.0)
        return False
    
    def save_selection(self):
        """Manually save current selection/cursor position."""
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self._saved_selection_start = start.get_offset()
            self._saved_selection_end = end.get_offset()
        else:
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            self._saved_selection_start = cursor.get_offset()
            self._saved_selection_end = None
    
    def restore_selection(self):
        """Manually restore saved selection/cursor position."""
        if self._saved_selection_start is not None:
            start_iter = self.buffer.get_iter_at_offset(self._saved_selection_start)
            
            if self._saved_selection_end is not None:
                end_iter = self.buffer.get_iter_at_offset(self._saved_selection_end)
                self.buffer.select_range(start_iter, end_iter)
            else:
                self.buffer.place_cursor(start_iter)
            
            self.text_view.scroll_to_mark(self.buffer.get_insert(), 0.0, False, 0.0, 0.0)
    
    def get_text(self) -> str:
        """Get plain text from buffer (without formatting)."""
        start, end = self.buffer.get_bounds()
        return self.buffer.get_text(start, end, True)
    
    def get_formatted_content(self) -> str:
        """Get content with formatting as JSON."""
        import json
        
        start_time = time.time()
        
        try:
            start, end = self.buffer.get_bounds()
            text = self.buffer.get_text(start, end, True)
            
            # Collect all tags and their ranges
            formatting_data = {
                "text": text,
                "tags": []
            }
            
            # If buffer is empty or very short (likely just placeholder), return early
            if not text or len(text.strip()) == 0:
                log_performance("get_formatted_content", time.time() - start_time, 
                              text_length=0, status="empty_buffer")
                return json.dumps(formatting_data)
            
            # Safety: Only process formatting for text with actual content
            # This prevents issues with newly created empty notes
            if len(text.strip()) < 2:
                log_performance("get_formatted_content", time.time() - start_time,
                              text_length=len(text), status="near_empty_buffer")
                return json.dumps(formatting_data)
            
            # Collect all unique tag applications  
            # Iterate character by character to be safe
            processed_tags = set()  # Track (tag_name, start, end) to avoid duplicates
            
            char_iter = start.copy()
            max_chars = len(text)
            char_count = 0
            
            # Safety limit: Don't process more than 10000 characters for tags
            # This prevents infinite loops in edge cases
            safety_limit = min(max_chars, 10000)
            
            # Track progress for freeze detection
            last_progress_log = 0
            
            while char_count < safety_limit and not char_iter.equal(end):
                tags = char_iter.get_tags()
                
                for tag in tags:
                    tag_name = tag.get_property("name")
                    if not tag_name:
                        continue
                    
                    # Find where this tag starts and ends
                    tag_start = char_iter.copy()
                    if not tag_start.starts_tag(tag):
                        tag_start.backward_to_tag_toggle(tag)
                    
                    tag_end = char_iter.copy()
                    if not tag_end.ends_tag(tag):
                        tag_end.forward_to_tag_toggle(tag)
                    
                    start_offset = tag_start.get_offset()
                    end_offset = tag_end.get_offset()
                    
                    # Add to set to avoid duplicates
                    tag_key = (tag_name, start_offset, end_offset)
                    if tag_key not in processed_tags:
                        processed_tags.add(tag_key)
                        formatting_data["tags"].append({
                            "name": tag_name,
                            "start": start_offset,
                            "end": end_offset
                        })
                
                # Move to next character
                if not char_iter.forward_char():
                    break
                char_count += 1
                
                # Log progress every 1000 chars to detect freezes
                if char_count - last_progress_log >= 1000:
                    elapsed = time.time() - start_time
                    if elapsed > 2.0:  # More than 2 seconds
                        log_freeze_warning(
                            "get_formatted_content slow",
                            {
                                "char_count": char_count,
                                "max_chars": max_chars,
                                "elapsed_seconds": f"{elapsed:.2f}",
                                "tags_found": len(processed_tags)
                            }
                        )
                    last_progress_log = char_count
                
                # Additional safety: break if we've been in the loop too long
                if char_count > safety_limit:
                    log_warning("Tag collection safety limit reached",
                              char_count=char_count,
                              safety_limit=safety_limit,
                              text_length=max_chars)
                    break
            
            duration = time.time() - start_time
            log_performance("get_formatted_content", duration,
                          text_length=max_chars,
                          tags_found=len(processed_tags),
                          chars_processed=char_count)
            
            return json.dumps(formatting_data)
            
        except Exception as e:
            log_error("Error in get_formatted_content", exception=e,
                     text_length=len(self.get_text()) if hasattr(self, 'buffer') else 0)
            # Return empty formatted data on error
            return json.dumps({"text": self.get_text() if hasattr(self, 'buffer') else "", "tags": []})
    
    def set_text(self, text: str):
        """Set plain text without any formatting."""
        self.buffer.set_text(text)
    
    def set_formatted_content(self, json_data: str):
        """Set formatted content from JSON data."""
        if not json_data:
            return
        
        import json
        
        start_time = time.time()
        
        try:
            data = json.loads(json_data)
            text = data.get("text", "")
            tags_data = data.get("tags", [])
            
            # Set plain text first
            self.buffer.set_text(text)
            
            # Apply tags
            tag_count = 0
            for tag_info in tags_data:
                tag_name = tag_info.get("name")
                start_offset = tag_info.get("start", 0)
                end_offset = tag_info.get("end", 0)
                
                if tag_name in self._tags:
                    start_iter = self.buffer.get_iter_at_offset(start_offset)
                    end_iter = self.buffer.get_iter_at_offset(end_offset)
                    self.buffer.apply_tag(self._tags[tag_name], start_iter, end_iter)
                    tag_count += 1
                elif tag_name.startswith("color_#"):
                    # Dynamic color tag
                    hex_color = tag_name.replace("color_", "")
                    tag = self._get_or_create_color_tag(hex_color)
                    start_iter = self.buffer.get_iter_at_offset(start_offset)
                    end_iter = self.buffer.get_iter_at_offset(end_offset)
                    self.buffer.apply_tag(tag, start_iter, end_iter)
                    tag_count += 1
            
            duration = time.time() - start_time
            log_performance("set_formatted_content", duration,
                          text_length=len(text),
                          tags_applied=tag_count,
                          tags_total=len(tags_data))
                    
        except json.JSONDecodeError as e:
            log_error("JSON decode error in set_formatted_content", exception=e,
                     json_length=len(json_data) if json_data else 0)
            # Fallback to treating as plain text
            if isinstance(json_data, str):
                try:
                    self.buffer.set_text(json_data)
                except Exception as fallback_error:
                    log_error("Fallback set_text failed", exception=fallback_error)
                    
        except Exception as e:
            log_error("Error in set_formatted_content", exception=e,
                     json_length=len(json_data) if json_data else 0)
            # Fallback to treating as plain text
            if isinstance(json_data, str):
                try:
                    self.buffer.set_text(json_data)
                except Exception as fallback_error:
                    log_error("Fallback set_text failed", exception=fallback_error)
