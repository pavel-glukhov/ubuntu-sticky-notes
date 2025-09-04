import sys
import sqlite3
import os
from PyQt5 import QtCore, QtWidgets, QtGui

DB_PATH = "stickies.db"
ICON_PATH = "gnomestickynotesapplet_93762.png"
AUTOSAVE_INTERVAL_MS = 2000


class NotesDB:
    """Class for managing the sticky notes database."""

    def __init__(self, path=DB_PATH):
        """Initialize the database and create the table if it does not exist."""
        self.conn = sqlite3.connect(path)
        self._create_table()

    def _create_table(self):
        """Create the 'notes' table if it does not exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    content TEXT,
                    x INTEGER,
                    y INTEGER,
                    w INTEGER,
                    h INTEGER,
                    color TEXT DEFAULT '#FFF59D'
                )
            """)

    def add(self, content="", x=300, y=200, w=260, h=200, color="#FFF59D"):
        """Add a new sticky note to the database and return its ID."""
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO notes(content, x, y, w, h, color) VALUES (?, ?, ?, ?, ?, ?)",
                (content, x, y, w, h, color)
            )
            return cur.lastrowid

    def update(self, note_id, content, x, y, w, h, color):
        """Update an existing sticky note by its ID."""
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET content=?, x=?, y=?, w=?, h=?, color=? WHERE id=?",
                (content, x, y, w, h, color, note_id)
            )

    def get(self, note_id):
        """Retrieve a sticky note's data by ID."""
        cur = self.conn.execute(
            "SELECT content, x, y, w, h, color FROM notes WHERE id=?", (note_id,)
        )
        return cur.fetchone()

    def all_notes(self):
        """Return a list of all sticky notes (ID and content)."""
        cur = self.conn.execute("SELECT id, content FROM notes")
        return cur.fetchall()


class StickyWindow(QtWidgets.QWidget):
    """A window representing a single sticky note."""

    closed = QtCore.pyqtSignal(int)

    def __init__(self, db: NotesDB, note_id=None):
        """Initialize the sticky note window."""
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

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setStyleSheet("background: transparent; border: none; font-size: 12pt;")
        self.text_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text_edit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)

        self.size_grip = QtWidgets.QSizeGrip(self)

        self.autosave_timer = QtCore.QTimer(self)
        self.autosave_timer.setInterval(AUTOSAVE_INTERVAL_MS)
        self.autosave_timer.timeout.connect(self.save)
        self.autosave_timer.start()

    def show_context_menu(self, pos):
        """Display the context menu for the sticky note."""
        menu = QtWidgets.QMenu(self)
        copy_action = menu.addAction("📋 Copy")
        paste_action = menu.addAction("📥 Paste")
        select_all_action = menu.addAction("🔲 Select All")
        menu.addSeparator()

        color_menu = menu.addMenu("🎨 Background Color")
        yellow_action = color_menu.addAction("Yellow")
        green_action = color_menu.addAction("Green")
        blue_action = color_menu.addAction("Blue")
        pink_action = color_menu.addAction("Pink")

        menu.addSeparator()
        close_action = menu.addAction("❌ Close Note")

        action = menu.exec_(self.text_edit.mapToGlobal(pos))
        if action == copy_action:
            self.text_edit.copy()
        elif action == paste_action:
            self.text_edit.paste()
        elif action == select_all_action:
            self.text_edit.selectAll()
        elif action == yellow_action:
            self.color = "#FFF59D"; self.update(); self.save()
        elif action == green_action:
            self.color = "#C8E6C9"; self.update(); self.save()
        elif action == blue_action:
            self.color = "#BBDEFB"; self.update(); self.save()
        elif action == pink_action:
            self.color = "#F8BBD0"; self.update(); self.save()
        elif action == close_action:
            self.close()

    def resizeEvent(self, event):
        """Handle the resize event and autosave the note."""
        self.text_edit.setGeometry(self.margin, self.margin,
                                   self.width() - 2*self.margin,
                                   self.height() - 2*self.margin)
        self.size_grip.setGeometry(self.width()-20, self.height()-20, 15, 15)
        super().resizeEvent(event)
        if not self._loading:
            self.save()

    def moveEvent(self, event):
        """Handle the move event and autosave the note."""
        super().moveEvent(event)
        if not self._loading:
            self.save()

    def paintEvent(self, event):
        """Draw the sticky note background and border."""
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
        """Start dragging the window on mouse press."""
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
        """Move the window during drag."""
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            if QtWidgets.QApplication.platformName() in ["xcb", "windows"]:
                self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Save the position when drag is released."""
        if event.button() == QtCore.Qt.LeftButton:
            if self._drag_pos:
                self.save()
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def load_from_db(self):
        """Load note data (content, color, geometry) from the database."""
        if self.note_id:
            row = self.db.get(self.note_id)
            if row:
                content, x, y, w, h, color = row
                self.text_edit.setText(content)
                self.color = color or self.color
                self.setGeometry(x or 300, y or 200, w or 260, h or 200)

    def showEvent(self, event):
        """Load note from database on show."""
        super().showEvent(event)
        self._loading = True
        self.load_from_db()
        self._loading = False

    def save(self):
        """Save the note content, geometry, and color to the database."""
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
        """Save the note before closing and emit the closed signal."""
        self.save()
        event.accept()
        if self.note_id:
            self.closed.emit(self.note_id)


class MainWindow(QtWidgets.QMainWindow):
    """Main window showing the list of sticky notes."""

    def __init__(self):
        """Initialize the main window and toolbar."""
        super().__init__()
        self.db = NotesDB()
        self.setWindowTitle("Sticky Notes")
        self.resize(400, 300)
        self.list_widget = QtWidgets.QListWidget()
        self.setCentralWidget(self.list_widget)

        toolbar = self.addToolBar("Toolbar")
        new_action = QtWidgets.QAction("New", self)
        new_action.triggered.connect(self.create_note)
        toolbar.addAction(new_action)

        delete_action = QtWidgets.QAction("Delete", self)
        delete_action.triggered.connect(self.delete_selected_note)
        toolbar.addAction(delete_action)

        self.stickies = {}
        self.list_widget.itemDoubleClicked.connect(self.open_note)

        self.refresh_list()

    def closeEvent(self, event):
        """Hide the main window instead of closing the app."""
        event.ignore()
        self.hide()

    def refresh_list(self):
        """Refresh the list of sticky notes."""
        self.list_widget.clear()
        for note_id, content in self.db.all_notes():
            item = QtWidgets.QListWidgetItem(f"Note {note_id}")
            item.setData(QtCore.Qt.UserRole, note_id)
            self.list_widget.addItem(item)

    def create_note(self):
        """Create a new sticky note and display it."""
        note_id = self.db.add("", 300, 200, 260, 200, "#FFF59D")
        sticky = StickyWindow(self.db, note_id)
        sticky.closed.connect(self.refresh_list)
        self.stickies[note_id] = sticky
        sticky.show()
        self.refresh_list()

    def open_note(self, item):
        """Open a sticky note from the list, loading its latest data."""
        note_id = item.data(QtCore.Qt.UserRole)
        if note_id in self.stickies:
            sticky = self.stickies[note_id]
        else:
            sticky = StickyWindow(self.db, note_id)
            sticky.closed.connect(self.refresh_list)
            self.stickies[note_id] = sticky
        sticky.load_from_db()
        sticky.showNormal()
        sticky.raise_()
        sticky.activateWindow()

    def delete_selected_note(self):
        """Delete the selected sticky note."""
        item = self.list_widget.currentItem()
        if not item:
            return
        note_id = item.data(QtCore.Qt.UserRole)
        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete the selected note?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            if note_id in self.stickies:
                self.stickies[note_id].close()
                del self.stickies[note_id]
            with self.db.conn:
                self.db.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
            self.refresh_list()


def main():
    if sys.platform.startswith("linux") and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.hide()
    if os.path.exists(ICON_PATH):
        tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(ICON_PATH), app)
    else:
        tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon.fromTheme("note"), app)

    tray_menu = QtWidgets.QMenu()
    tray_menu.addAction("Show Notes List", window.showNormal)
    tray_menu.addAction("Exit", app.quit)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Sticky Notes")
    tray_icon.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
