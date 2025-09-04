import sys
import sqlite3
import os
from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui

APP_NAME = "ubuntu-sticky-notes"

DATA_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", APP_NAME)
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "stickies.db")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "resources", "gnomestickynotes.png")
AUTOSAVE_INTERVAL_MS = 2000
COLOR_MAP = {"Yellow": "#FFF59D", "Green": "#C8E6C9", "Blue": "#BBDEFB", "Pink": "#F8BBD0"}


class NotesDB:
    """Handles SQLite database operations for sticky notes."""

    def __init__(self, path=DB_PATH):
        """Initialize database connection and create table if not exists."""
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        """Create the notes table if it doesn't exist."""
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
                    deleted_at TEXT
                )
            """)

    def add(self, content="", x=300, y=200, w=260, h=200, color="#FFF59D"):
        """Add a new note to the database."""
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO notes(content, x, y, w, h, color) VALUES (?, ?, ?, ?, ?, ?)",
                (content, x, y, w, h, color)
            )
            return cur.lastrowid

    def update(self, note_id, content, x, y, w, h, color):
        """Update an existing note in the database."""
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=? WHERE id=?",
                (content, x, y, w, h, color, note_id)
            )

    def get(self, note_id):
        """Retrieve a note by its ID."""
        cur = self.conn.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return cur.fetchone()

    def all_notes(self):
        """Return all active (non-deleted) notes."""
        cur = self.conn.execute("SELECT id, content, color FROM notes WHERE deleted=0")
        return cur.fetchall()

    def move_to_trash(self, note_id):
        """Move a note to the trash."""
        deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=1, deleted_at=? WHERE id=?", (deleted_at, note_id))

    def all_trash(self):
        """Return all deleted notes."""
        cur = self.conn.execute("SELECT * FROM notes WHERE deleted=1")
        return cur.fetchall()

    def restore_from_trash(self, note_id):
        """Restore a note from trash."""
        with self.conn:
            self.conn.execute("UPDATE notes SET deleted=0, deleted_at=NULL WHERE id=?", (note_id,))

    def delete_permanently(self, note_id):
        """Delete a note permanently from the database."""
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))


class StickyWindow(QtWidgets.QWidget):
    """Represents an individual sticky note window."""

    closed = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(int, str)
    colorChanged = QtCore.pyqtSignal(int, str)

    def __init__(self, db: NotesDB, note_id=None):
        """Initialize a sticky note window."""
        super().__init__()
        self.db = db
        self.note_id = note_id
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.setMinimumSize(200, 150)
        self._last_geo = None
        self._last_content = None
        self._last_color = None
        self.margin = 15
        self._loading = True
        self._drag_pos = None
        self.color = "#FFF59D"

        self.format_bar = QtWidgets.QToolBar(self)
        self.format_bar.setIconSize(QtCore.QSize(64, 64))
        self.format_bar.setStyleSheet("background: transparent; border: none;")
        bold_action = QtWidgets.QAction("B", self)
        bold_action.triggered.connect(self.toggle_bold)
        italic_action = QtWidgets.QAction("I", self)
        italic_action.triggered.connect(self.toggle_italic)
        strike_action = QtWidgets.QAction("S", self)
        strike_action.triggered.connect(self.toggle_strike)
        list_action = QtWidgets.QAction("⋮", self)
        list_action.triggered.connect(self.toggle_list)
        self.format_bar.addAction(bold_action)
        self.format_bar.addAction(italic_action)
        self.format_bar.addAction(strike_action)
        self.format_bar.addAction(list_action)

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

    def on_text_changed(self):
        """Handle text changes and emit signal."""
        if not self._loading and self.note_id:
            content = self.text_edit.toPlainText()
            self.textChanged.emit(self.note_id, content)
            self.save()

    def show_context_menu(self, pos):
        """Show the context menu for a sticky note."""
        menu = QtWidgets.QMenu(self)
        copy_action = menu.addAction("📋 Copy")
        paste_action = menu.addAction("📥 Paste")
        select_all_action = menu.addAction("🔲 Select All")
        menu.addSeparator()
        color_menu = menu.addMenu("🎨 Background Color")
        for name, color in COLOR_MAP.items():
            action = color_menu.addAction(name)
            action.triggered.connect(lambda checked, c=color: self.change_color(c))
        menu.addSeparator()
        close_action = menu.addAction("❌ Close Note")
        action = menu.exec_(self.text_edit.mapToGlobal(pos))
        if action == copy_action:
            self.text_edit.copy()
        elif action == paste_action:
            self.text_edit.paste()
        elif action == select_all_action:
            self.text_edit.selectAll()
        elif action == close_action:
            self.hide()

    def change_color(self, color):
        """Change the background color of the sticky note."""
        self.color = color
        self.update()
        self.save()
        if self.note_id:
            self.colorChanged.emit(self.note_id, color)

    def resizeEvent(self, event):
        """Handle resizing of sticky window and its components."""
        bar_height = 40
        offset = 10
        self.text_edit.setGeometry(self.margin, self.margin,
                                   self.width() - 2*self.margin,
                                   self.height() - 2*self.margin - bar_height - offset - 5)
        self.format_bar.setGeometry(self.margin, self.height() - bar_height - self.margin - offset,
                                    self.width() - 2*self.margin, bar_height)
        self.size_grip.setGeometry(self.width()-20, self.height()-20, 15, 15)
        super().resizeEvent(event)
        if not self._loading:
            self.save()

    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        cursor = self.text_edit.textCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontWeight(QtGui.QFont.Bold if cursor.charFormat().fontWeight() != QtGui.QFont.Bold else QtGui.QFont.Normal)
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_italic(self):
        """Toggle italic formatting for selected text."""
        cursor = self.text_edit.textCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_strike(self):
        """Toggle strike-through formatting for selected text."""
        cursor = self.text_edit.textCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontStrikeOut(not cursor.charFormat().fontStrikeOut())
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_list(self):
        """Toggle bullet list formatting for the current paragraph."""
        cursor = self.text_edit.textCursor()
        if cursor.currentList():
            cursor.currentList().remove(cursor.block())
        else:
            list_fmt = QtGui.QTextListFormat()
            list_fmt.setStyle(QtGui.QTextListFormat.ListDisc)
            cursor.createList(list_fmt)

    def moveEvent(self, event):
        """Handle window movement event."""
        super().moveEvent(event)
        if not self._loading:
            self.save()

    def paintEvent(self, event):
        """Paint the sticky note background and line separator."""
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QColor(self.color))
        pen = QtGui.QPen(QtGui.QColor("#A0A0A0"))
        pen.setWidth(1)
        painter.setPen(pen)
        rect = self.rect()
        rect.adjust(0, 0, -1, -1)
        painter.drawRect(rect)
        painter.drawLine(self.margin, self.height() - 45 - 10, self.width() - self.margin, self.height() - 45 - 10)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
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
        """Handle mouse move for dragging."""
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            if QtWidgets.QApplication.platformName() in ["xcb", "windows"]:
                self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging."""
        if event.button() == QtCore.Qt.LeftButton:
            if self._drag_pos:
                self.save()
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def load_from_db(self):
        """Load sticky note content and geometry from database."""
        if self.note_id:
            row = self.db.get(self.note_id)
            if row:
                self.text_edit.setText(row["content"])
                self.color = row["color"] or self.color
                self.setGeometry(row["x"] or 300, row["y"] or 200, row["w"] or 260, row["h"] or 200)

    def showEvent(self, event):
        """Load note from DB when window is shown."""
        super().showEvent(event)
        self._loading = True
        self.load_from_db()
        self._loading = False

    def save(self):
        """Save sticky note content and geometry to database."""
        x, y, w, h = self.x(), self.y(), self.width(), self.height()
        content = self.text_edit.toPlainText()
        if self._last_geo == (x, y, w, h) and self._last_content == content and self._last_color == self.color:
            return
        self._last_geo = (x, y, w, h)
        self._last_content = content
        self._last_color = self.color
        if self.note_id:
            self.db.update(self.note_id, content, x, y, w, h, self.color)
        else:
            self.note_id = self.db.add(content, x, y, w, h, self.color)

    def closeEvent(self, event):
        """Intercept close event to hide window instead of closing."""
        self.save()
        event.ignore()
        self.hide()
        if self.note_id:
            self.closed.emit(self.note_id)


class TrashWindow(QtWidgets.QWidget):
    """Window displaying deleted notes."""

    def __init__(self, db: NotesDB, main_window=None):
        """Initialize trash window."""
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.setWindowTitle("Trash")
        self.resize(300, 400)
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

    def refresh_list(self):
        """Refresh the list of deleted notes."""
        self.list_widget.clear()
        for note in self.db.all_trash():
            snippet = note["content"][:15].replace("\n", " ")
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
    """Main application window showing all sticky notes."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.db = NotesDB()
        self.setWindowTitle("Sticky Notes")
        self.resize(300, 400)
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

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
        new_action = QtWidgets.QAction("New", self)
        new_action.triggered.connect(self.create_note)
        toolbar.addAction(new_action)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        bin_action = QtWidgets.QAction("Bin", self)
        bin_action.triggered.connect(self.open_trash)
        toolbar.addAction(bin_action)

        self.stickies = {}
        self.trash_window = TrashWindow(self.db, main_window=self)
        self.refresh_list()

    def closeEvent(self, event):
        """Hide main window instead of closing."""
        event.ignore()
        self.hide()

    def refresh_list(self):
        """Refresh the list of active notes."""
        self.list_widget.clear()
        for note_id, content, color in self.db.all_notes():
            snippet = content[:15].replace("\n", " ")
            item = QtWidgets.QListWidgetItem(f"{snippet}...")
            item.setData(QtCore.Qt.UserRole, note_id)
            item.setData(QtCore.Qt.UserRole + 1, content)
            item.setData(QtCore.Qt.UserRole + 2, color)
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setBrush(QtGui.QColor(color))
            painter.setPen(QtGui.QColor("#A0A0A0"))
            painter.drawEllipse(0, 0, 15, 15)
            painter.end()
            item.setIcon(QtGui.QIcon(pixmap))
            self.list_widget.addItem(item)
        self.filter_list()

    def filter_list(self):
        """Filter notes in the list based on search query."""
        query = self.search_bar.text().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            full_text = item.data(QtCore.Qt.UserRole + 1).lower()
            item.setHidden(query not in full_text)

    def create_note(self):
        """Create a new sticky note."""
        note_id = self.db.add()
        sticky = StickyWindow(self.db, note_id)
        sticky.closed.connect(self.refresh_list)
        sticky.textChanged.connect(self.on_sticky_text_changed)
        sticky.colorChanged.connect(self.on_sticky_color_changed)
        self.stickies[note_id] = sticky
        sticky.show()
        self.refresh_list()

    def open_note(self, item_or_id):
        """Open a sticky note window."""
        if isinstance(item_or_id, QtWidgets.QListWidgetItem):
            note_id = item_or_id.data(QtCore.Qt.UserRole)
        else:
            note_id = item_or_id
        if note_id in self.stickies:
            sticky = self.stickies[note_id]
        else:
            sticky = StickyWindow(self.db, note_id)
            sticky.closed.connect(self.refresh_list)
            sticky.textChanged.connect(self.on_sticky_text_changed)
            sticky.colorChanged.connect(self.on_sticky_color_changed)
            self.stickies[note_id] = sticky
        sticky.load_from_db()
        sticky.showNormal()
        sticky.raise_()
        sticky.activateWindow()

    def on_sticky_text_changed(self, note_id, content):
        """Update list item text when sticky content changes."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.UserRole) == note_id:
                snippet = content[:15].replace("\n", " ")
                item.setText(f"{snippet}...")
                item.setData(QtCore.Qt.UserRole + 1, content)
                break
        self.filter_list()

    def on_sticky_color_changed(self, note_id, color):
        """Update list item icon when sticky color changes."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.UserRole) == note_id:
                item.setData(QtCore.Qt.UserRole + 2, color)
                pixmap = QtGui.QPixmap(16, 16)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                painter.setBrush(QtGui.QColor(color))
                painter.setPen(QtGui.QColor("#A0A0A0"))
                painter.drawEllipse(0, 0, 15, 15)
                painter.end()
                item.setIcon(QtGui.QIcon(pixmap))
                break

    def show_context_menu(self, pos):
        """Show context menu for a note in the main list."""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        menu = QtWidgets.QMenu()
        open_action = menu.addAction("Open")
        color_menu = menu.addMenu("🎨 Change Color")
        delete_action = menu.addAction("Delete")
        for name, color in COLOR_MAP.items():
            action = color_menu.addAction(name)
            action.triggered.connect(lambda checked, c=color, i=item: self.change_item_color(i, c))
        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        if action == open_action:
            self.open_note(item)
        elif action == delete_action:
            self.delete_note_with_confirmation(item)

    def change_item_color(self, item, color):
        """Change color of a note from the main list."""
        note_id = item.data(QtCore.Qt.UserRole)
        if note_id in self.stickies:
            self.stickies[note_id].change_color(color)

    def delete_note_with_confirmation(self, item):
        """Move a note to trash after confirmation."""
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
        """Open the trash window."""
        self.trash_window.refresh_list()
        self.trash_window.show()

    def open_all_stickies(self):
        """Open all sticky notes."""
        for note_id in [item.data(QtCore.Qt.UserRole) for item in self.list_widget.findItems("", QtCore.Qt.MatchContains)]:
            self.open_note(note_id)


def main():
    """Launch the Sticky Notes application."""
    if sys.platform.startswith("linux") and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = QtWidgets.QApplication(sys.argv)
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

    tray_menu.addAction("Open All Stickers", open_all_stickies)
    tray_menu.addSeparator()
    tray_menu.addAction("Show Notes List", window.showNormal)
    tray_menu.addAction("Exit", app.quit)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Sticky Notes")
    tray_icon.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
