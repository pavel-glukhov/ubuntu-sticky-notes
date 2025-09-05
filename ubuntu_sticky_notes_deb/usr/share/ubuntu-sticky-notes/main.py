import sys
import sqlite3
import os
from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui

APP_INFO = {
    "name": "Ubuntu Sticky Notes",
    "version": "1.2.2",
    "author": "Pavel Glukhov",
    "email": "glukhov.p@gmail.com",
    "website": "https://github.com/pavel-glukhov/ubuntu_sticky_notes",
    "description": (
        "Ubuntu Sticky Notes is a lightweight desktop application for creating "
        "and managing sticky notes. Notes can be customized with colors, "
        "pinned on top, moved to trash and restored."
    ),
    "license": "MIT License"
}

DATA_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", APP_INFO.get('name').replace(' ', '-').lower())
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "stickies.db")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "resources", "gnomestickynotes.png")
AUTOSAVE_INTERVAL_MS = 2000
COLOR_MAP = {"Yellow": "#FFF59D", "Green": "#C8E6C9", "Blue": "#BBDEFB", "Pink": "#F8BBD0"}


class NotesDB:
    """SQLite database handler for sticky notes. Supports add, update, delete, restore and query operations."""

    def __init__(self, path=DB_PATH):
        """Initialize database connection and create the notes table if it does not exist."""
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
        if self.get_setting("always_on_top") is None:
            self.set_setting("always_on_top", "0")

    def _create_table(self):
        """Create the notes table schema and settings table if missing."""
        with self.conn:
            self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    content TEXT,
                    x INTEGER,
                    y INTEGER,
                    w INTEGER,
                    h INTEGER,
                    color TEXT DEFAULT '#FFF59D',
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    always_on_top INTEGER DEFAULT 0,
                    is_open INTEGER DEFAULT 0
                )

            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

    def add(self, content="", x=300, y=200, w=260, h=200, color="#FFF59D", always_on_top=0):
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO notes(content, x, y, w, h, color, always_on_top) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (content, x, y, w, h, color, always_on_top)
            )
            return cur.lastrowid

    def update(self, note_id, content, x, y, w, h, color, always_on_top=0):
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=?, always_on_top=? WHERE id=?",
                (content, x, y, w, h, color, always_on_top, note_id)
            )


    def get(self, note_id):
        """Retrieve a note by ID."""
        cur = self.conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    def all_notes(self):
        """Return all active notes (not deleted)."""
        cur = self.conn.execute("SELECT id, content, color FROM notes WHERE deleted=0")
        return cur.fetchall()

    def move_to_trash(self, note_id):
        """Mark a note as deleted and move it to trash."""
        deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=1, deleted_at=? WHERE id=?", (deleted_at, note_id))

    def all_trash(self):
        """Return all deleted notes in trash."""
        cur = self.conn.execute("SELECT * FROM notes WHERE deleted=1")
        return cur.fetchall()

    def restore_from_trash(self, note_id):
        """Restore a note from trash back to active notes."""
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=0, deleted_at=NULL WHERE id=?", (note_id,))

    def delete_permanently(self, note_id):
        """Remove a note permanently from the database."""
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def get_setting(self, key):
        """Return setting value for key or None if missing."""
        cur = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def set_setting(self, key, value):
        """Set or update a setting."""
        with self.conn:
            self.conn.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def set_open_state(self, note_id, state: int):
        """Saves whether the sticker is open (1) or closed (0)."""
        with self.conn:
            self.conn.execute("UPDATE notes SET is_open=? WHERE id=?", (state, note_id))

    def get_open_notes(self):
        """Returns all notes that were opened during the last session."""
        cur = self.conn.execute("SELECT id FROM notes WHERE is_open=1 AND deleted=0")
        return [row["id"] for row in cur.fetchall()]



class StickyWindow(QtWidgets.QWidget):
    """Sticky note window supporting text editing, formatting, autosave, drag and resize."""

    closed = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(int, str)
    colorChanged = QtCore.pyqtSignal(int, str)

    def __init__(self, db: NotesDB, note_id=None, always_on_top=False):
        super().__init__()
        self.db = db
        self.note_id = note_id
        self._always_on_top = bool(always_on_top)
        flags = QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint
        if self._always_on_top:
            flags |= QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setMinimumSize(200, 150)
        self._last_geo = None
        self._last_content = None
        self._last_color = None
        self.margin = 15
        self._loading = True
        self._drag_pos = None
        self.color = "#FFF59D"

        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+B"), self, self.toggle_bold)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+I"), self, self.toggle_italic)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+S"), self, self.toggle_strike)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+L"), self, self.toggle_list)

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setStyleSheet("background: transparent; border: none; font-size: 12pt;")
        self.text_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text_edit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)
        self.text_edit.textChanged.connect(self.on_text_changed)

        self.size_grip = QtWidgets.QSizeGrip(self)

        self.autosave_timer = QtCore.QTimer(self)
        self.autosave_timer.setInterval(AUTOSAVE_INTERVAL_MS)
        self.autosave_timer.timeout.connect(self.save)
        self.autosave_timer.start()

    def set_always_on_top(self, flag: bool):
        """Set/unset window always-on-top flag for this sticky."""
        self._always_on_top = bool(flag)
        flags = self.windowFlags()
        if self._always_on_top:
            flags |= QtCore.Qt.WindowStaysOnTopHint
        else:
            flags &= ~QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.raise_()
        self.activateWindow()

    def on_text_changed(self):
        """Emit signal when text changes and trigger autosave."""
        if not self._loading and self.note_id:
            content = self.text_edit.toPlainText()
            self.textChanged.emit(self.note_id, content)
            self.save()

    def show_context_menu(self, pos):
        """Show context menu for editing and formatting options."""
        menu = QtWidgets.QMenu(self)

        copy_action = menu.addAction("📋 Copy (Ctrl+C)")
        paste_action = menu.addAction("📥 Paste (Ctrl+V)")
        select_all_action = menu.addAction("🔲 Select All (Ctrl+A)")
        menu.addSeparator()

        bold_action = menu.addAction("Bold (Ctrl+B)")
        italic_action = menu.addAction("Italic (Ctrl+I)")
        strike_action = menu.addAction("Strike (Shift+S)")
        list_action = menu.addAction("Bullet List (Shift+L)")
        menu.addSeparator()

        if self._always_on_top:
            top_action = menu.addAction("📍 Unpin from Top")
        else:
            top_action = menu.addAction("📌 Pin to Top")
        menu.addSeparator()

        color_menu = menu.addMenu("🎨 Background Color")
        for name, color in COLOR_MAP.items():
            action = color_menu.addAction(name)
            action.triggered.connect(lambda checked, c=color: self.change_color(c))
        menu.addSeparator()

        close_action = menu.addAction("❌ Close Sticker")
        action = menu.exec_(self.text_edit.mapToGlobal(pos))

        if action == copy_action:
            self.text_edit.copy()
        elif action == paste_action:
            self.text_edit.paste()
        elif action == select_all_action:
            self.text_edit.selectAll()
        elif action == bold_action:
            self.toggle_bold()
        elif action == italic_action:
            self.toggle_italic()
        elif action == strike_action:
            self.toggle_strike()
        elif action == list_action:
            self.toggle_list()
        elif action == top_action:
            self.set_always_on_top(not self._always_on_top)
        elif action == close_action:
            self.close()

    def change_color(self, color):
        """Change sticky note background color and save it."""
        self.color = color
        self.update()
        self.save()
        if self.note_id:
            self.colorChanged.emit(self.note_id, color)

    def resizeEvent(self, event):
        """Resize text area and size grip, then save state."""
        offset = 10
        self.text_edit.setGeometry(
            self.margin,
            self.margin,
            self.width() - 2 * self.margin,
            self.height() - 2 * self.margin - offset
        )
        self.size_grip.setGeometry(self.width() - 20, self.height() - 20, 15, 15)
        super().resizeEvent(event)
        if not self._loading:
            self.save()

    def toggle_bold(self):
        """Toggle bold formatting on selected text."""
        cursor = self.text_edit.textCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontWeight(QtGui.QFont.Bold if cursor.charFormat().fontWeight() != QtGui.QFont.Bold else QtGui.QFont.Normal)
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_italic(self):
        """Toggle italic formatting on selected text."""
        cursor = self.text_edit.textCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_strike(self):
        """Toggle strike-through formatting on selected text."""
        cursor = self.text_edit.textCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontStrikeOut(not cursor.charFormat().fontStrikeOut())
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_list(self):
        """Toggle bullet list formatting on current paragraph."""
        cursor = self.text_edit.textCursor()
        if cursor.currentList():
            cursor.currentList().remove(cursor.block())
        else:
            list_fmt = QtGui.QTextListFormat()
            list_fmt.setStyle(QtGui.QTextListFormat.ListDisc)
            cursor.createList(list_fmt)

    def moveEvent(self, event):
        """Save state on window move."""
        super().moveEvent(event)
        if not self._loading:
            self.save()

    def paintEvent(self, event):
        """Draw note background and border."""
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QColor(self.color))
        pen = QtGui.QPen(QtGui.QColor("#A0A0A0"))
        pen.setWidth(1)
        painter.setPen(pen)
        rect = self.rect()
        rect.adjust(0, 0, -1, -1)
        painter.drawRect(rect)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        """Handle window drag start."""
        if event.button() == QtCore.Qt.LeftButton:
            platform = QtWidgets.QApplication.platformName()
            if platform == "wayland":
                handle = self.windowHandle()
                if handle:
                    handle.startSystemMove()
            else:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle dragging window with mouse."""
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            if QtWidgets.QApplication.platformName() in ["xcb", "windows"]:
                self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Save state after drag ends."""
        if event.button() == QtCore.Qt.LeftButton:
            if self._drag_pos:
                self.save()
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def load_from_db(self):
        if self.note_id:
            row = self.db.get(self.note_id)
            if row:
                self.text_edit.setHtml(row["content"])
                self.color = row["color"] or self.color
                self.setGeometry(row["x"] or 300, row["y"] or 200, row["w"] or 260, row["h"] or 200)
                self.set_always_on_top(bool(row["always_on_top"] or 0))



    def showEvent(self, event):
        super().showEvent(event)
        self._loading = True
        self.load_from_db()
        if self.note_id:
            self.db.set_open_state(self.note_id, 1)
        self._loading = False

    def save(self):
        x, y, w, h = self.x(), self.y(), self.width(), self.height()
        content = self.text_edit.toHtml()
        always_on_top_int = 1 if self._always_on_top else 0
        if self._last_geo == (x, y, w, h) and self._last_content == content \
        and self._last_color == self.color and self._last_always_on_top == always_on_top_int:
            return
        self._last_geo = (x, y, w, h)
        self._last_content = content
        self._last_color = self.color
        self._last_always_on_top = always_on_top_int
        if self.note_id:
            self.db.update(self.note_id, content, x, y, w, h, self.color, always_on_top_int)
        else:
            self.note_id = self.db.add(content, x, y, w, h, self.color, always_on_top_int)


    def closeEvent(self, event):
        """Intercept close event, save note and hide window instead."""
        self.save()
        if self.note_id:
            self.db.set_open_state(self.note_id, 0)
            self.closed.emit(self.note_id)
        event.ignore()
        self.hide()



class TrashWindow(QtWidgets.QWidget):
    """Trash window to manage deleted notes (restore, delete permanently, preview)."""

    def __init__(self, db: NotesDB, main_window=None):
        """Initialize trash view window."""
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.setWindowTitle("Trash")
        self.resize(300, 400)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

    def refresh_list(self):
        """Refresh trash list from database."""
        self.list_widget.clear()
        for note in self.db.all_trash():
            doc = QtGui.QTextDocument()
            doc.setHtml(note["content"])
            plain_text = doc.toPlainText()
            snippet = plain_text[:15].replace("\n", " ")

            item = QtWidgets.QListWidgetItem(f"{snippet}... ({note['deleted_at']})")
            item.setData(QtCore.Qt.UserRole, note["id"])
            item.setData(QtCore.Qt.UserRole + 1, note["content"])
            item.setData(QtCore.Qt.UserRole + 2, note["color"])
            item.setData(QtCore.Qt.UserRole + 3, note["deleted_at"])

            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setBrush(QtGui.QColor(note["color"]))
            painter.setPen(QtGui.QColor("#A0A0A0"))
            painter.drawEllipse(0, 0, 15, 15)
            painter.end()
            item.setIcon(QtGui.QIcon(pixmap))

            self.list_widget.addItem(item)


    def show_context_menu(self, pos):
        """Show context menu for trash items."""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        menu = QtWidgets.QMenu()
        restore_action = menu.addAction("Restore")
        open_action = menu.addAction("Open")
        delete_action = menu.addAction("Delete Permanently")

        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        note_id = item.data(QtCore.Qt.UserRole)

        if action == restore_action:
            self.db.restore_from_trash(note_id)
            if self.main_window:
                self.main_window.refresh_list()
        elif action == delete_action:
            self.db.delete_permanently(note_id)
        elif action == open_action and self.main_window:
            self.main_window.open_note(note_id)

        self.refresh_list()


class MainWindow(QtWidgets.QMainWindow):
    """Main application window showing a searchable list of all notes."""

    def __init__(self):
        """Initialize main window with list, search bar, toolbar and trash window."""
        super().__init__()
        self.db = NotesDB()
        self.setWindowTitle("Ubuntu Sticky Notes")
        self.resize(300, 400)
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_bar)

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.open_note)
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.setIconSize(QtCore.QSize(32, 32))
        new_icon_path = os.path.join(BASE_DIR, "resources", "new.png")
        new_action = QtWidgets.QAction(QtGui.QIcon(new_icon_path), "", self)
        new_action.triggered.connect(self.create_note)
        toolbar.addAction(new_action)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        bin_icon_path = os.path.join(BASE_DIR, "resources", "bin.png")
        bin_action = QtWidgets.QAction(QtGui.QIcon(bin_icon_path), "", self)
        bin_action.triggered.connect(self.open_trash)
        toolbar.addAction(bin_action)

        self.stickies = {}
        self.trash_window = TrashWindow(self.db, main_window=self)
        self.refresh_list()

    def closeEvent(self, event):
        """Hide main window instead of closing app."""
        event.ignore()
        self.hide()


    def _create_list_item_widget(self, snippet_text: str, color: str):
        """Create a QWidget used as the visual representation of a list item."""
        widget = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(widget)
        h.setContentsMargins(4, 2, 4, 2)

        color_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setBrush(QtGui.QColor(color))
        painter.setPen(QtGui.QColor("#A0A0A0"))
        painter.drawEllipse(0, 0, 15, 15)
        painter.end()
        color_label.setPixmap(pixmap)
        color_label.setFixedSize(18, 18)
        h.addWidget(color_label)

        text_label = QtWidgets.QLabel(snippet_text)
        text_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        h.addWidget(text_label)

        check_label = QtWidgets.QLabel("✓")
        check_label.setVisible(False)
        h.addWidget(check_label)

        widget._text_label = text_label
        widget._color_label = color_label
        return widget


    def refresh_list(self):
        """Refresh active notes list from database."""
        self.list_widget.clear()
        for note_id, content, color in self.db.all_notes():
            doc = QtGui.QTextDocument()
            doc.setHtml(content)
            plain_text = doc.toPlainText()
            snippet = plain_text[:15].replace("\n", " ")
            
            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.UserRole, note_id)
            item.setData(QtCore.Qt.UserRole + 1, content)
            item.setData(QtCore.Qt.UserRole + 2, color)

            visual = self._create_list_item_widget(f"{snippet}...", color)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, visual)
        self.filter_list()

    def create_note(self):
        """Create and open a new sticky note."""
        note_id = self.db.add()
        sticky = StickyWindow(self.db, note_id, always_on_top=False)
        sticky.closed.connect(self.refresh_list)
        sticky.textChanged.connect(self.on_sticky_text_changed)
        sticky.colorChanged.connect(self.on_sticky_color_changed)
        self.stickies[note_id] = sticky
        sticky.show()
        self.refresh_list()

    def filter_list(self):
        """Filter notes list based on search query."""
        query = self.search_bar.text().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            full_text = item.data(QtCore.Qt.UserRole + 1).lower()
            hidden = query not in full_text
            item.setHidden(hidden)

    def open_note(self, item_or_id):
        """Open a note window by list item or ID."""
        if isinstance(item_or_id, QtWidgets.QListWidgetItem):
            note_id = item_or_id.data(QtCore.Qt.UserRole)
        else:
            note_id = item_or_id
        if note_id in self.stickies:
            sticky = self.stickies[note_id]
        else:
            sticky = StickyWindow(self.db, note_id, always_on_top=False)
            sticky.closed.connect(self.refresh_list)
            sticky.textChanged.connect(self.on_sticky_text_changed)
            sticky.colorChanged.connect(self.on_sticky_color_changed)
            self.stickies[note_id] = sticky
        sticky.load_from_db()
        sticky.showNormal()
        sticky.raise_()
        sticky.activateWindow()

    def on_sticky_text_changed(self, note_id, content):
        """Update list entry text when sticky content changes."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.UserRole) == note_id:
                doc = QtGui.QTextDocument()
                doc.setHtml(content)
                plain_text = doc.toPlainText()
                snippet = plain_text[:15].replace("\n", " ")
                
                item.setData(QtCore.Qt.UserRole + 1, content)
                widget = self.list_widget.itemWidget(item)
                if widget and hasattr(widget, "_text_label"):
                    widget._text_label.setText(f"{snippet}...")
                break
        self.filter_list()

    def on_sticky_color_changed(self, note_id, color):
        """Update list item icon when sticky color changes."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.UserRole) == note_id:
                item.setData(QtCore.Qt.UserRole + 2, color)
                widget = self.list_widget.itemWidget(item)
                if widget and hasattr(widget, "_color_label"):
                    pixmap = QtGui.QPixmap(16, 16)
                    pixmap.fill(QtCore.Qt.transparent)
                    painter = QtGui.QPainter(pixmap)
                    painter.setBrush(QtGui.QColor(color))
                    painter.setPen(QtGui.QColor("#A0A0A0"))
                    painter.drawEllipse(0, 0, 15, 15)
                    painter.end()
                    widget._color_label.setPixmap(pixmap)
                break

    def show_context_menu(self, pos):
        """Show context menu for managing a note."""
        item = self.list_widget.itemAt(pos)
        menu = QtWidgets.QMenu()

        if item:
            open_action = menu.addAction("Open")
            color_menu = menu.addMenu("🎨 Change Color")
            delete_action = menu.addAction("Delete")
            for name, color in COLOR_MAP.items():
                action = color_menu.addAction(name)
                action.triggered.connect(lambda checked, c=color, i=item: self.change_item_color(i, c))
        else:
            open_action = delete_action = None

        action = menu.exec_(self.list_widget.mapToGlobal(pos))

        if item and action == open_action:
            self.open_note(item)
        elif item and action == delete_action:
            self.delete_note_with_confirmation(item)

    def set_always_on_top(self, flag: bool):
        """Set global always-on-top mode, save to DB, update main window and all stickies and UI check marks."""
        self.always_on_top = bool(flag)
        self.db.set_setting("always_on_top", "1" if self.always_on_top else "0")
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, self.always_on_top)
        self.show()
        self.raise_()
        self.activateWindow()
        for sticky in self.stickies.values():
            sticky.set_always_on_top(self.always_on_top)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget and hasattr(widget, "_check_label"):
                widget._check_label.setVisible(self.always_on_top)

    def change_item_color(self, item, color):
        """Change note color from main list."""
        note_id = item.data(QtCore.Qt.UserRole)
        if note_id in self.stickies:
            self.stickies[note_id].change_color(color)
        else:
            cur_content = item.data(QtCore.Qt.UserRole + 1)
            row = self.db.get(note_id)
            if row:
                x, y, w, h = row["x"] or 300, row["y"] or 200, row["w"] or 260, row["h"] or 200
                self.db.update(note_id, cur_content, x, y, w, h, color)
            self.refresh_list()

    def delete_note_with_confirmation(self, item):
        """Confirm deletion and move note to trash."""
        note_id = item.data(QtCore.Qt.UserRole)
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Note",
            "Are you sure you want to delete the selected note?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            if note_id in self.stickies:
                self.stickies[note_id].close()
                del self.stickies[note_id]
            self.db.move_to_trash(note_id)
            self.refresh_list()
            if self.trash_window.isVisible():
                self.trash_window.refresh_list()

    def open_trash(self):
        """Open trash window."""
        self.trash_window.refresh_list()
        self.trash_window.showNormal()

    def open_all_stickies(self):
        """Open all saved sticky notes at once."""
        for note_id in [item.data(QtCore.Qt.UserRole) for item in self.list_widget.findItems("", QtCore.Qt.MatchContains)]:
            self.open_note(note_id)


class AboutDialog(QtWidgets.QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_INFO['name']}")
        self.setIcon(QtWidgets.QMessageBox.Information)

        text = (
            f"<b>{APP_INFO['name']}</b><br>"
            f"Version: {APP_INFO['version']}<br>"
            f"Author: {APP_INFO['author']}<br>"
            f"Email: {APP_INFO['email']}<br>"
            f"<a href='{APP_INFO['website']}'>{APP_INFO['website']}</a><br><br>"
            f"{APP_INFO['description']}<br><br>"
            f"<i>{APP_INFO['license']}</i>"
        )

        self.setText(text)
        self.setStandardButtons(QtWidgets.QMessageBox.Ok)



def main():
    if sys.platform.startswith("linux") and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    def init_app():
        window = MainWindow()
        window.hide()

        tray_icon = QtWidgets.QSystemTrayIcon(
            QtGui.QIcon(ICON_PATH) if os.path.exists(ICON_PATH) else QtGui.QIcon.fromTheme("note"), app
        )

        tray_menu = QtWidgets.QMenu()

        def open_all_stickies():
            for i in range(window.list_widget.count()):
                item = window.list_widget.item(i)
                window.open_note(item)

        def hide_all_stickies():
            for sticky in window.stickies.values():
                sticky.hide()

        def open_previous_state():
            for note_id in window.db.get_open_notes():
                if note_id in window.stickies:
                    sticky = window.stickies[note_id]
                    if sticky.isVisible():
                        continue
                else:
                    sticky = StickyWindow(window.db, note_id)
                    sticky.closed.connect(window.refresh_list)
                    sticky.textChanged.connect(window.on_sticky_text_changed)
                    sticky.colorChanged.connect(window.on_sticky_color_changed)
                    window.stickies[note_id] = sticky
                sticky.load_from_db()
                sticky.show()
                sticky.raise_()
                sticky.activateWindow()

        def open_new_sticker():
            window.create_note()

        tray_menu.addAction("Open Previous State", open_previous_state)
        tray_menu.addAction("Open All Stickers", open_all_stickies)
        tray_menu.addAction("Hide All Stickers", hide_all_stickies)
        tray_menu.addSeparator()
        tray_menu.addAction("Show Notes List", window.showNormal)
        tray_menu.addAction("Open New Sticker", open_new_sticker)
        tray_menu.addSeparator()
        about_action = tray_menu.addAction("About")
        about_action.triggered.connect(lambda: AboutDialog().exec_())
        tray_menu.addSeparator()
        tray_menu.addAction("Exit", app.quit)

        tray_icon.setToolTip("Ubuntu Sticky Notes")
        tray_icon.setVisible(True)
        tray_icon.setContextMenu(tray_menu)

        tray_icon.activated.connect(
            lambda reason: window.showNormal() if reason == QtWidgets.QSystemTrayIcon.DoubleClick else None
        )

        tray_icon.show()


    QtCore.QTimer.singleShot(0, init_app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
