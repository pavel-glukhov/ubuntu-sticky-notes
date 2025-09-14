import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from config import COLOR_MAP, get_app_paths
from trash_window import TrashWindow
from sticky_window import StickyWindow
from notes_db import NotesDB

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]
ICONS_PATH = paths["ICONS_DIR"]


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for managing sticky notes.

    Displays a searchable list of all active notes, allows creating new notes,
    opening, deleting (moving to trash), and changing colors. Supports global
    always-on-top mode and interaction with the TrashWindow.
    """

    def __init__(self):
        """
        Initialize the main window UI, load notes from database,
        and set up toolbar, list, search, and trash window.
        """
        super().__init__()
        self.db = NotesDB()

        # Load UI from Qt Designer file
        ui_path = os.path.join(UI_PATH, "mainwindow.ui")
        uic.loadUi(ui_path, self)

        self.setWindowTitle("Ubuntu Sticky Notes")
        self.resize(400, 500)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        # --- Toolbar icons ---
        self.new_action.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, "new.png")))
        self.bin_action.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, "bin.png")))

        # Connect toolbar actions
        self.new_action.triggered.connect(self.create_note)
        self.bin_action.triggered.connect(self.open_trash)

        # --- List widget setup ---
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.open_note)

        # --- Search bar ---
        self.search_bar.textChanged.connect(self.filter_list)

        # Initialize stickies and trash window
        self.stickies = {}
        self.trash_window = TrashWindow(self.db, main_window=self)
        self.refresh_list()

    def closeEvent(self, event):
        """Hide the main window instead of exiting the application."""
        event.ignore()
        self.hide()

    def _create_list_item_widget(self, snippet_text: str, color: str) -> QtWidgets.QWidget:
        """
        Create a QWidget representing a note in the list with color icon and text.

        Args:
            snippet_text (str): Short text snippet of the note content.
            color (str): Background color for the note indicator.

        Returns:
            QWidget: Custom widget for display in QListWidget.
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)

        # Color indicator
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
        layout.addWidget(color_label)

        # Text snippet
        text_label = QtWidgets.QLabel(snippet_text)
        text_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout.addWidget(text_label)

        # Always-on-top indicator (hidden by default)
        check_label = QtWidgets.QLabel("✓")
        check_label.setVisible(False)
        layout.addWidget(check_label)

        widget._text_label = text_label
        widget._color_label = color_label
        widget._check_label = check_label
        return widget

    def refresh_list(self):
        """
        Refresh the main list of active notes.

        Fetches notes from the database, generates snippets,
        and updates the list widget with custom item widgets.
        """
        self.list_widget.clear()
        for note_id, content, color in self.db.all_notes():
            doc = QtGui.QTextDocument()
            doc.setHtml(content)
            snippet = doc.toPlainText()[:15].replace("\n", " ")

            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.UserRole, note_id)
            item.setData(QtCore.Qt.UserRole + 1, content)
            item.setData(QtCore.Qt.UserRole + 2, color)

            visual = self._create_list_item_widget(f"{snippet}...", color)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, visual)
        self.filter_list()

    def create_note(self):
        """Create a new sticky note, add it to the database, and show it."""
        note_id = self.db.add()
        sticky = StickyWindow(self.db, note_id, always_on_top=False)
        sticky.closed.connect(self.refresh_list)
        sticky.textChanged.connect(self.on_sticky_text_changed)
        sticky.colorChanged.connect(self.on_sticky_color_changed)
        self.stickies[note_id] = sticky
        sticky.show()
        self.refresh_list()

    def filter_list(self):
        """Filter displayed notes based on the current search query."""
        query = self.search_bar.text().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            full_text = item.data(QtCore.Qt.UserRole + 1).lower()
            item.setHidden(query not in full_text)

    def open_note(self, item_or_id):
        """
        Open a sticky note by QListWidgetItem or note ID.

        Ensures the sticky window exists and is shown with latest content.

        Args:
            item_or_id (QListWidgetItem | int): List item or note ID.
        """
        if isinstance(item_or_id, QtWidgets.QListWidgetItem):
            note_id = item_or_id.data(QtCore.Qt.UserRole)
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
        Update the list display when a sticky note's text changes.

        Args:
            note_id (int): ID of the changed note.
            content (str): New content of the sticky note.
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.UserRole) == note_id:
                doc = QtGui.QTextDocument()
                doc.setHtml(content)
                snippet = doc.toPlainText()[:15].replace("\n", " ")

                item.setData(QtCore.Qt.UserRole + 1, content)
                widget = self.list_widget.itemWidget(item)
                if widget and hasattr(widget, "_text_label"):
                    widget._text_label.setText(f"{snippet}...")
                break
        self.filter_list()

    def on_sticky_color_changed(self, note_id, color):
        """
        Update the list display when a sticky note's color changes.

        Args:
            note_id (int): ID of the note.
            color (str): New color of the sticky note.
        """
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
        """
        Show a context menu for managing a selected note in the list.

        Allows opening, changing color, or deleting the note.
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

        action = menu.exec_(self.list_widget.mapToGlobal(pos))

        if item and action == open_action:
            self.open_note(item)
        elif item and action == delete_action:
            self.delete_note_with_confirmation(item)

    def set_always_on_top(self, flag: bool):
        """
        Enable or disable always-on-top mode globally.

        Updates main window, all sticky windows, UI indicators, and database setting.

        Args:
            flag (bool): True to set always-on-top, False to unset.
        """
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
        """
        Change the color of a note from the main list.

        Args:
            item (QListWidgetItem): Item representing the note.
            color (str): New color to apply.
        """
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
        """
        Prompt the user to confirm deletion and move the note to trash.

        Args:
            item (QListWidgetItem): Item representing the note to delete.
        """
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
        """Open the TrashWindow and refresh its contents."""
        self.trash_window.refresh_list()
        self.trash_window.showNormal()

    def open_all_stickies(self):
        """Open all active sticky notes at once."""
        for note_id in [item.data(QtCore.Qt.UserRole) for item in
                        self.list_widget.findItems("", QtCore.Qt.MatchContains)]:
            self.open_note(note_id)
