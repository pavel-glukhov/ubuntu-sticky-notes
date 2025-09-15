import os

from config import get_app_paths
from notes_db import NotesDB
from PyQt6 import QtCore, QtGui, QtWidgets, uic

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]


class TrashWindow(QtWidgets.QWidget):
    """
    Trash window for managing deleted sticky notes.

    Features:
        - Displays deleted notes with preview and deletion timestamp.
        - Allows restoring notes back to the main list.
        - Supports permanent deletion of notes.
        - Can open deleted notes in the main window for preview.
    """

    def __init__(self, db: NotesDB, main_window=None):
        """
        Initialize the TrashWindow.

        Args:
            db (NotesDB): Notes database instance.
            main_window (QWidget, optional): Reference to the main window
                for refreshing the list or opening restored notes.
        """
        super().__init__()
        self.db = db
        self.main_window = main_window

        ui_path = os.path.join(UI_PATH, "trashwindow.ui")
        uic.loadUi(ui_path, self)

        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

    def refresh_list(self):
        """
        Refresh the trash list with all deleted notes from the database.
        """
        self.list_widget.clear()
        for note in self.db.all_trash():
            doc = QtGui.QTextDocument()
            doc.setHtml(note["content"])
            plain_text = doc.toPlainText()
            snippet = plain_text[:15].replace("\n", " ")

            item = QtWidgets.QListWidgetItem(f"{snippet}... ({note['deleted_at']})")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, note["id"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, note["content"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 2, note["color"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 3, note["deleted_at"])

            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.GlobalColor.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setBrush(QtGui.QColor(note["color"]))
            painter.setPen(QtGui.QColor("#A0A0A0"))
            painter.drawEllipse(0, 0, 15, 15)
            painter.end()
            item.setIcon(QtGui.QIcon(pixmap))

            self.list_widget.addItem(item)

    def show_context_menu(self, pos):
        """
        Show context menu for a selected note in the trash list.

        Args:
            pos (QPoint): Mouse position where the context menu should appear.
        """
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        menu = QtWidgets.QMenu()
        restore_action = menu.addAction("🔙 Restore")
        open_action = menu.addAction("📂 Open")
        delete_action = menu.addAction("❌ Delete Permanently")

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        note_id = item.data(QtCore.Qt.ItemDataRole.UserRole)

        if action == restore_action:
            self.db.restore_from_trash(note_id)
            if self.main_window:
                self.main_window.refresh_list()
        elif action == delete_action:
            self.db.delete_permanently(note_id)
        elif action == open_action and self.main_window:
            self.main_window.open_note(note_id)

        self.refresh_list()
