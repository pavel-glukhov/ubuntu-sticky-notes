import os

from config import COLOR_MAP, get_app_paths
from notes_db import NotesDB
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from sticky_window import StickyWindow
from trash_window import TrashWindow

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]
ICONS_PATH = paths["ICONS_DIR"]


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for managing sticky notes.

    Features:
        - Toolbar for creating new notes and accessing the trash.
        - Search bar for filtering notes by text.
        - List widget for displaying and managing saved notes.
        - Context menu with actions (open, recolor, delete).
        - Integration with StickyWindow for note editing.
        - Trash management via TrashWindow.
    """

    def __init__(self):
        """
        Initialize the main window, database connection, and UI components.
        """
        super().__init__()
        self.db = NotesDB()

        ui_path = os.path.join(UI_PATH, "mainwindow.ui")
        uic.loadUi(ui_path, self)

        self.setWindowTitle("Ubuntu Sticky Notes")
        self.resize(400, 500)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)

        self.new_action.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, "new.png")))
        self.bin_action.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, "bin.png")))

        self.new_action.triggered.connect(self.create_note)
        self.bin_action.triggered.connect(self.open_trash)

        self.list_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.open_note)

        self.search_bar.textChanged.connect(self.filter_list)

        self.stickies = {}
        self.trash_window = TrashWindow(self.db, main_window=self)
        self.refresh_list()

    def closeEvent(self, event):
        """
        Override close event to hide the window instead of quitting.
        """
        event.ignore()
        self.hide()

    def _create_list_item_widget(self, snippet_text: str, color: str) -> QtWidgets.QWidget:
        """
        Create a custom widget for displaying a note in the list.

        Args:
            snippet_text (str): Shortened preview text of the note.
            color (str): Background color of the note.

        Returns:
            QtWidgets.QWidget: A widget containing note preview and color indicator.
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)

        color_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setBrush(QtGui.QColor(color))
        painter.setPen(QtGui.QColor("#A0A0A0"))
        painter.drawEllipse(0, 0, 15, 15)
        painter.end()
        color_label.setPixmap(pixmap)
        color_label.setFixedSize(18, 18)
        layout.addWidget(color_label)

        text_label = QtWidgets.QLabel(snippet_text)
        text_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        layout.addWidget(text_label)

        check_label = QtWidgets.QLabel("✓")
        check_label.setVisible(False)
        layout.addWidget(check_label)

        widget._text_label = text_label
        widget._color_label = color_label
        widget._check_label = check_label
        return widget

    def refresh_list(self):
        """
        Reload the notes list from the database.
        """
        self.list_widget.clear()
        for note_id, content, color in self.db.all_notes():
            doc = QtGui.QTextDocument()
            doc.setHtml(content)
            snippet = doc.toPlainText()[:15].replace("\n", " ")

            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.UserRole, note_id)
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, content)
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 2, color)

            visual = self._create_list_item_widget(f"{snippet}...", color)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, visual)
        self.filter_list()

    def create_note(self):
        """
        Create a new sticky note and add it to the database and UI.
        """
        note_id = self.db.add()
        sticky = StickyWindow(self.db, note_id, always_on_top=False)
        sticky.closed.connect(self.refresh_list)
        sticky.textChanged.connect(self.on_sticky_text_changed)
        sticky.colorChanged.connect(self.on_sticky_color_changed)
        self.stickies[note_id] = sticky
        sticky.show()
        self.refresh_list()

    def filter_list(self):
        """
        Filter notes in the list by the search query.
        """
        query = self.search_bar.text().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            full_text = item.data(QtCore.Qt.ItemDataRole.UserRole + 1).lower()
            item.setHidden(query not in full_text)

    def open_note(self, item_or_id):
        """
        Open a sticky note in a new window.

        Args:
            item_or_id (QListWidgetItem | int): Note item or note ID.
        """
        if isinstance(item_or_id, QtWidgets.QListWidgetItem):
            note_id = item_or_id.data(QtCore.Qt.ItemDataRole.UserRole)
        else:
            note_id = item_or_id

        sticky = self.stickies.get(note_id)
        if not sticky:
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
        """
        Update note preview in the list when its content changes.

        Args:
            note_id (int): ID of the note.
            content (str): Updated note content.
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == note_id:
                doc = QtGui.QTextDocument()
                doc.setHtml(content)
                snippet = doc.toPlainText()[:15].replace("\n", " ")

                item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, content)
                widget = self.list_widget.itemWidget(item)
                if widget and hasattr(widget, "_text_label"):
                    widget._text_label.setText(f"{snippet}...")
                break
        self.filter_list()

    def on_sticky_color_changed(self, note_id, color):
        """
        Update note color indicator in the list when it changes.

        Args:
            note_id (int): ID of the note.
            color (str): New color hex code.
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == note_id:
                item.setData(QtCore.Qt.ItemDataRole.UserRole + 2, color)
                widget = self.list_widget.itemWidget(item)
                if widget and hasattr(widget, "_color_label"):
                    pixmap = QtGui.QPixmap(16, 16)
                    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
                    painter = QtGui.QPainter(pixmap)
                    painter.setBrush(QtGui.QColor(color))
                    painter.setPen(QtGui.QColor("#A0A0A0"))
                    painter.drawEllipse(0, 0, 15, 15)
                    painter.end()
                    widget._color_label.setPixmap(pixmap)
                break

    def show_context_menu(self, pos):
        """
        Show context menu for notes list with available actions.

        Args:
            pos (QPoint): Mouse position for context menu.
        """
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

        action = menu.exec(self.list_widget.mapToGlobal(pos))

        if item and action == open_action:
            self.open_note(item)
        elif item and action == delete_action:
            self.delete_note_with_confirmation(item)

    def set_always_on_top(self, flag: bool):
        """
        Toggle always-on-top mode for the main window and all stickies.

        Args:
            flag (bool): True to keep on top, False otherwise.
        """
        self.always_on_top = bool(flag)
        self.db.set_setting("always_on_top", "1" if self.always_on_top else "0")
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, self.always_on_top)
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
        """
        Change the color of a note from the list.

        Args:
            item (QListWidgetItem): Note item.
            color (str): New color hex code.
        """
        note_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if note_id in self.stickies:
            self.stickies[note_id].change_color(color)
        else:
            cur_content = item.data(QtCore.Qt.ItemDataRole.UserRole + 1)
            row = self.db.get(note_id)
            if row:
                x, y, w, h = row["x"] or 300, row["y"] or 200, row["w"] or 260, row["h"] or 200
                self.db.update(note_id, cur_content, x, y, w, h, color)
            self.refresh_list()

    def delete_note_with_confirmation(self, item):
        """
        Prompt user for confirmation before deleting a note.

        Args:
            item (QListWidgetItem): Note item to delete.
        """
        note_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Note",
            "Are you sure you want to delete the selected note?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            if note_id in self.stickies:
                self.stickies[note_id].close()
                del self.stickies[note_id]
            self.db.move_to_trash(note_id)
            self.refresh_list()
            if self.trash_window.isVisible():
                self.trash_window.refresh_list()

    def open_trash(self):
        """
        Open the trash window and refresh its content.
        """
        self.trash_window.refresh_list()
        self.trash_window.showNormal()

    def open_all_stickies(self):
        """
        Open all notes from the list as sticky windows.
        """
        for note_id in [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in
                        self.list_widget.findItems("", QtCore.Qt.MatchFlag.MatchContains)]:
            self.open_note(note_id)
