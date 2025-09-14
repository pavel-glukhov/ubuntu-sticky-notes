import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from notes_db import NotesDB
from config import get_app_paths

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]


class TrashWindow(QtWidgets.QWidget):
    """
    Trash window for managing deleted sticky notes.

    Allows previewing deleted notes, restoring them, permanently deleting,
    and optionally opening them in the main window.

    Args:
        db (NotesDB): Database instance for accessing notes.
        main_window (Optional[QWidget]): Reference to the main window for opening/restoring notes.
    """

    def __init__(self, db: NotesDB, main_window=None):
        """
        Initialize the TrashWindow UI and setup context menu.

        Args:
            db (NotesDB): Database instance to access trash notes.
            main_window (Optional[QWidget]): Reference to the main window to open or refresh notes.
        """
        super().__init__()
        self.db = db
        self.main_window = main_window

        ui_path = os.path.join(UI_PATH, "trashwindow.ui")
        uic.loadUi(ui_path, self)

        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

    def refresh_list(self):
        """
        Refresh the list of trashed notes from the database.

        Loads deleted notes, generates a short text snippet for each,
        sets note color as an icon, and populates the QListWidget.
        """
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

            # Set color indicator icon
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
        """
        Show a context menu for the trash list item at the given position.

        Provides options to:
            - Restore the note from trash
            - Open the note in the main window
            - Delete the note permanently

        Args:
            pos (QPoint): Position to display the context menu relative to the list widget.
        """
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
