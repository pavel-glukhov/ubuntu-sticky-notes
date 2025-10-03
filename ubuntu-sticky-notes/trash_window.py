import os

from config import get_app_paths
from notes_db import NotesDB
from PyQt6 import QtCore, QtGui, QtWidgets, uic

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]


class TrashWindow(QtWidgets.QWidget):
    """
    Trash window for managing deleted sticky notes.

    Provides a list of deleted notes with options to restore,
    permanently delete, or reopen a note.
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
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete), self, self.delete_selected_notes)

    def refresh_list(self):
        """
        Refresh the trash list with all deleted notes from the database.

        - Uses the note title if available.
        - If the title is missing, extracts a plain text snippet from content.
        - Each note is displayed with its deletion timestamp and color marker.
        """
        self.list_widget.clear()
        for note in self.db.all_trash():
            doc = QtGui.QTextDocument()
            doc.setHtml(note["content"])
            plain_text = doc.toPlainText()
            snippet = plain_text[:15].replace("\n", " ")

            title = note["title"] if note["title"] else snippet

            item = QtWidgets.QListWidgetItem(f"{title} ({note['deleted_at']})")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, note["id"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, note["content"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 2, note["color"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 3, note["deleted_at"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 4, note["title"])

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
        Display the context menu for selected notes in the trash list.

        Args:
            pos (QPoint): Mouse position relative to the list widget.
        """
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        menu = QtWidgets.QMenu()
        restore_action = menu.addAction("🔙 Restore")
        open_action = menu.addAction("📂 Open (first selected)")
        delete_action = menu.addAction("❌ Delete Permanently (Del)")

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        note_ids = [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in selected_items]

        if action == restore_action:
            for note_id in note_ids:
                self.db.restore_from_trash(note_id)
            self.list_widget.clearSelection()
            if self.main_window:
                self.main_window.refresh_list()
            self.refresh_list()

        elif action == delete_action:
            self.delete_selected_notes()

        elif action == open_action and self.main_window and note_ids:
            self.main_window.open_note(note_ids[0])

    def delete_selected_notes(self):
        """
        Permanently delete all selected notes after confirmation.

        Prompts the user with a confirmation dialog.
        If confirmed, removes notes from the database and refreshes the list.
        """
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Notes",
            f"Are you sure you want to permanently delete {len(selected_items)} note(s)?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            for item in selected_items:
                note_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
                self.db.delete_permanently(note_id)

            self.refresh_list()
