import os

from config import COLOR_MAP, get_app_paths
from notes_db import NotesDB
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from sticky_window import StickyWindow
from trash_window import TrashWindow

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]
ICONS_PATH = paths["ICONS_DIR"]


class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    """QStyledItemDelegate that prevents focus rectangle from appearing on QListWidget items."""

    def paint(self, painter, option, index):
        """Paints the item without focus rectangle.

        Args:
            painter (QtGui.QPainter): Painter used to draw the item.
            option (QtWidgets.QStyleOptionViewItem): Style options for the item.
            index (QtCore.QModelIndex): Index of the item.
        """
        option.state &= ~QtWidgets.QStyle.StateFlag.State_Selected
        super().paint(painter, option, index)


class ReorderableListWidget(QtWidgets.QListWidget):
    """QListWidget subclass that supports reordering items.

    Signals:
        orderChanged: Emitted when the order of items changes.
    """
    orderChanged = QtCore.pyqtSignal()


class MainWindow(QtWidgets.QMainWindow):
    """Main window for managing sticky notes.

    Attributes:
        db (NotesDB): Database interface for notes.
        stickies (dict): Mapping from note IDs to StickyWindow instances.
        trash_window (TrashWindow): Window for managing deleted notes.
    """

    def __init__(self):
        """Initializes the main window, loads UI, sets up signals and keyboard shortcuts."""
        super().__init__()
        self.db = NotesDB()
        ui_path = os.path.join(UI_PATH, "mainwindow.ui")
        uic.loadUi(ui_path, self)

        old_list_widget = self.list_widget
        self.list_widget = ReorderableListWidget()
        self.list_widget.setObjectName("list_widget")

        self._setup_list_widget()
        self._replace_old_list_widget(old_list_widget)
        self.setWindowTitle("Ubuntu Sticky Notes")
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        self._setup_toolbar_actions()
        self._setup_shortcuts()

        self.stickies = {}
        self.trash_window = TrashWindow(self.db, main_window=self)
        self.refresh_list()

    def _setup_list_widget(self):
        """Configures the QListWidget used to display sticky notes."""
        self.list_widget.setItemDelegate(NoFocusDelegate())
        self.list_widget.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.list_widget.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setWrapping(True)
        self.list_widget.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.list_widget.setGridSize(QtCore.QSize(150, 150))
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.open_note)
        self.list_widget.itemSelectionChanged.connect(self.refresh_selection)
        self.list_widget.setAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.list_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.list_widget.setStyleSheet("""
            QListWidget::item {
                background: transparent;
                border: none;
            }
            QListWidget::item:selected {
                background: transparent;
                border: none;
            }
        """)

    def _replace_old_list_widget(self, old_list_widget):
        """Replaces the old QListWidget in the UI with the new one.

        Args:
            old_list_widget (QtWidgets.QListWidget): The previous list widget to replace.
        """
        parent_layout = old_list_widget.parentWidget().layout()
        index = parent_layout.indexOf(old_list_widget)
        parent_layout.removeWidget(old_list_widget)
        old_list_widget.deleteLater()
        parent_layout.insertWidget(index, self.list_widget)

    def _setup_toolbar_actions(self):
        """Sets up toolbar actions with icons and connections."""
        self.new_action.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, "new.png")))
        self.bin_action.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, "bin.png")))
        self.new_action.triggered.connect(self.create_note)
        self.bin_action.triggered.connect(self.open_trash)

    def _setup_shortcuts(self):
        """Defines keyboard shortcuts for note operations."""
        QtGui.QShortcut(QtGui.QKeySequence("Shift+O"), self, self.open_selected_note)
        QtGui.QShortcut(QtGui.QKeySequence("Shift+N"), self, self.create_note)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete), self, self.delete_selected_notes)
        rename_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Shift+R"), self)
        rename_shortcut.activated.connect(self.rename_selected_note)

    def closeEvent(self, event):
        """Overrides the close event to hide the window instead of closing.

        Args:
            event (QtGui.QCloseEvent): Close event.
        """
        event.ignore()
        self.hide()

    def _create_list_item_widget(self, title: str, color: str) -> QtWidgets.QWidget:
        """Creates a card widget representing a sticky note.

        Args:
            title (str): Note title to display.
            color (str): Background color for the note card.

        Returns:
            QtWidgets.QWidget: A QWidget representing the sticky note card.
        """
        widget = QtWidgets.QWidget()
        widget.setFixedSize(130, 130)
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        color_frame = QtWidgets.QFrame()
        color_frame.setFixedSize(120, 120)
        color_frame.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
        widget._color_frame = color_frame

        selection_frame = QtWidgets.QFrame(color_frame)
        selection_frame.setGeometry(0, 0, 120, 120)
        selection_frame.setStyleSheet("border: 2px solid #0078d7; border-radius: 6px;")
        selection_frame.setVisible(False)
        widget._selection_frame = selection_frame

        frame_layout = QtWidgets.QVBoxLayout(color_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        title_label = QtWidgets.QLabel(title)
        title_label.setWordWrap(True)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #000000;")
        title_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)

        frame_layout.addWidget(title_label)
        layout.addWidget(color_frame, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        widget._title_label = title_label

        return widget

    def refresh_list(self):
        """Clears and repopulates the note list from the database."""
        self.list_widget.clear()
        notes = sorted(self.db.all_notes(full=True), key=lambda n: (n["title"] or "").lower())

        for note in notes:
            note_id = note["id"]
            title = note["title"] or "Untitled"
            color = note["color"] or "#FFF59D"

            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.UserRole, note_id)

            widget = self._create_list_item_widget(title, color)
            item.setSizeHint(widget.sizeHint())

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def refresh_selection(self):
        """Updates selection frames for all note widgets based on their selection state."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget and hasattr(widget, "_selection_frame"):
                widget._selection_frame.setVisible(item.isSelected())

    def create_note(self):
        """Creates a new sticky note, opens its window, and adds it to the list."""
        note_id = self.db.add()
        sticky = StickyWindow(self.db, note_id, always_on_top=False, main_window=self)
        sticky.newNoteRequested.connect(self.create_note)
        sticky.closed.connect(self.refresh_list)
        sticky.textChanged.connect(self.on_sticky_text_changed)
        sticky.colorChanged.connect(self.on_sticky_color_changed)
        self.stickies[note_id] = sticky
        sticky.show()
        self.refresh_list()

    def rename_selected_note(self):
        """Renames the first selected note if any."""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.rename_note(selected_items[0])

    def open_selected_note(self):
        """Opens all selected notes."""
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            self.open_note(item)

    def delete_selected_notes(self):
        """Deletes all selected notes after user confirmation."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        note_ids = [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in selected_items]

        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Notes",
            f"Are you sure you want to delete the selected {len(note_ids)} note(s)?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        for note_id in note_ids:
            if note_id in self.stickies:
                self.stickies[note_id].close()
                del self.stickies[note_id]
            self.db.move_to_trash(note_id)

        self.refresh_list()
        if self.trash_window.isVisible():
            self.trash_window.refresh_list()

    def filter_list(self):
        """Filters the notes displayed based on the search bar text."""
        query = self.search_bar.text().lower().strip()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            title = (item.data(QtCore.Qt.ItemDataRole.UserRole + 1) or "").lower()
            content_html = item.data(QtCore.Qt.ItemDataRole.UserRole + 3) or ""
            doc = QtGui.QTextDocument()
            doc.setHtml(content_html)
            content = doc.toPlainText().lower().strip()
            if not title and not content:
                item.setHidden(query != "")
                continue
            item.setHidden(query not in title and query not in content)

    def open_note(self, item_or_id):
        """Opens a sticky note window for a given item or note ID.

        If the sticky window is already open, brings it to front; otherwise,
        creates a new window.

        Args:
            item_or_id (QtWidgets.QListWidgetItem | int): The note item or note ID.
        """
        if isinstance(item_or_id, QtWidgets.QListWidgetItem):
            note_id = item_or_id.data(QtCore.Qt.ItemDataRole.UserRole)
        else:
            note_id = item_or_id

        sticky = self.stickies.get(note_id)
        if not sticky:
            sticky = StickyWindow(self.db, note_id, always_on_top=False, main_window=self)
            sticky.closed.connect(self.refresh_list)
            sticky.textChanged.connect(self.on_sticky_text_changed)
            sticky.colorChanged.connect(self.on_sticky_color_changed)
            self.stickies[note_id] = sticky

        sticky.load_from_db()
        sticky.showNormal()
        sticky.raise_()
        sticky.activateWindow()

    def on_sticky_text_changed(self, note_id, content):
        """Updates the list widget when a sticky note's text changes.

        Args:
            note_id (int): The note ID.
            content (str): Updated HTML content of the note.
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == note_id:
                item.setData(QtCore.Qt.ItemDataRole.UserRole + 3, content)
                title = item.data(QtCore.Qt.ItemDataRole.UserRole + 1)
                if not title:
                    doc = QtGui.QTextDocument()
                    doc.setHtml(content)
                    snippet = doc.toPlainText()[:15].replace("\n", " ")
                    widget = self.list_widget.itemWidget(item)
                    if widget and hasattr(widget, "_text_label"):
                        widget._text_label.setText(f"{snippet}...")
                break
        self.filter_list()

    def on_sticky_color_changed(self, note_id, color):
        """Updates the note color in the list when a sticky note changes.

        Args:
            note_id (int): Note ID.
            color (str): New color.
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == note_id:
                item.setData(QtCore.Qt.ItemDataRole.UserRole + 2, color)
                widget = self.list_widget.itemWidget(item)
                if widget and hasattr(widget, "_color_frame"):
                    widget._color_frame.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
                break

    def show_context_menu(self, pos):
        """Shows the context menu for the selected notes."""
        selected_items = self.list_widget.selectedItems()
        menu = QtWidgets.QMenu()

        rename_action = None
        open_action = None
        delete_action = None

        if selected_items:
            if len(selected_items) > 1:
                open_action = menu.addAction("📂 Open (Shift + O)")
                delete_action = menu.addAction("🗑 Delete (Del)")
            elif len(selected_items) == 1:
                open_action = menu.addAction("📂 Open (Shift + O)")
                rename_action = menu.addAction("✏️ Rename (Shift + R)")
                color_menu = menu.addMenu("🎨 Change Color")
                delete_action = menu.addAction("🗑 Delete (Del)")
                item = selected_items[0]
                for name, color in COLOR_MAP.items():
                    action = color_menu.addAction(name)
                    action.triggered.connect(
                        lambda checked, c=color, i=item: self.change_item_color(i, c)
                    )

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action is None:
            return
        if action == open_action:
            self.open_selected_note()
        elif rename_action and action == rename_action:
            self.rename_note(selected_items[0])
        elif action == delete_action:
            self.delete_selected_notes()

    def rename_note(self, item: QtWidgets.QListWidgetItem):
        """Renames a note.

        Args:
            item (QtWidgets.QListWidgetItem): The item to rename.
        """
        note_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        old_title = item.data(QtCore.Qt.ItemDataRole.UserRole + 1) or ""
        new_title, ok = QtWidgets.QInputDialog.getText(
            self, "Rename Note", "Enter new title:", text=old_title
        )
        if ok and new_title.strip():
            new_title = new_title.strip()
            self.db.update_title(note_id, new_title)
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, new_title)
            widget = self.list_widget.itemWidget(item)
            if widget and hasattr(widget, "_title_label"):
                widget._title_label.setText(new_title)
                widget._title_label.adjustSize()
            self.refresh_list()

    def set_always_on_top(self, flag: bool):
        """Sets all windows to stay on top.

        Args:
            flag (bool): True to stay on top.
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
        """Changes the color of a note.

        Args:
            item (QtWidgets.QListWidgetItem): Note item.
            color (str): New color.
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
        """Deletes a note with confirmation dialog.

        Args:
            item (QtWidgets.QListWidgetItem): The item to delete.
        """
        note_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete the selected note?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
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
        """Opens the trash window."""
        self.trash_window.refresh_list()
        self.trash_window.showNormal()

    def open_all_stickies(self):
        """Opens all sticky notes in the list."""
        for note_id in [
            item.data(QtCore.Qt.ItemDataRole.UserRole)
            for item in self.list_widget.findItems("", QtCore.Qt.MatchFlag.MatchContains)
        ]:
            self.open_note(note_id)
