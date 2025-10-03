import os

from config import AUTOSAVE_INTERVAL_MS, COLOR_MAP, get_app_paths
from notes_db import NotesDB
from PyQt6 import QtCore, QtGui, QtWidgets, uic

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]


class StickyWindow(QtWidgets.QWidget):
    """
    A sticky note window with rich text editing, formatting, autosave, drag & resize,
    custom context menu, and persistent database storage.

    Signals:
        closed (int): Emitted when the sticky note is closed with its note ID.
        textChanged (int, str): Emitted when note content changes (ID, content).
        colorChanged (int, str): Emitted when background color changes (ID, hex color).
        newNoteRequested (): Emitted when the user clicks the add button to create a new note.
    """

    closed = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(int, str)
    colorChanged = QtCore.pyqtSignal(int, str)
    newNoteRequested = QtCore.pyqtSignal()  # Signal for "➕" button

    def __init__(self, db: NotesDB, note_id=None, always_on_top=False, main_window=None):
        """
        Initialize the sticky note window.

        Args:
            db (NotesDB): Database instance for storing and retrieving note data.
            note_id (int, optional): ID of the note. If None, a new note will be created.
            always_on_top (bool, optional): Whether the sticky is always on top.
            main_window (QWidget, optional): Reference to main window for creating new notes.
        """
        super().__init__()
        self.db = db
        self.note_id = note_id
        self._always_on_top = bool(always_on_top)
        self.main_window = main_window

        ui_path = os.path.join(UI_PATH, "stickywindow.ui")
        uic.loadUi(ui_path, self)

        self.size_grip = QtWidgets.QSizeGrip(self)
        self.size_grip.setFixedSize(15, 15)

        flags = QtCore.Qt.WindowType.Window | QtCore.Qt.WindowType.FramelessWindowHint
        if self._always_on_top:
            flags |= QtCore.Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        # Internal state tracking
        self._last_geo = None
        self._last_content = None
        self._last_color = None
        self._last_always_on_top = 0
        self._loading = True
        self._drag_pos = None
        self.margin = 15
        self.color = "#FFF59D"

        # Keyboard shortcuts for formatting
        shortcuts = {
            "Ctrl+B": self.toggle_bold,
            "Ctrl+I": self.toggle_italic,
            "Ctrl+Shift+S": self.toggle_strike,
            "Ctrl+Shift+L": self.toggle_list,
        }
        for key, slot in shortcuts.items():
            QtGui.QShortcut(QtGui.QKeySequence(key), self, slot)

        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)
        self.text_edit.textChanged.connect(self.on_text_changed)

        self.btn_close.clicked.connect(self.close)
        self.btn_close.setText("✖")
        self.btn_add.clicked.connect(self.on_add_clicked)
        self.btn_add.setText("➕")
        self.btn_pin.clicked.connect(self.on_pin_clicked)

        self.update_pin_button()

        self.autosave_timer = QtCore.QTimer(self)
        self.autosave_timer.setInterval(AUTOSAVE_INTERVAL_MS)
        self.autosave_timer.timeout.connect(self.save)
        self.autosave_timer.start()

    def update_pin_button(self):
        """
        Update the display of the pin button according to always-on-top state.
        """
        if self._always_on_top:
            self.btn_pin.setText("📍")
        else:
            self.btn_pin.setText("📌")

    def on_add_clicked(self):
        """
        Create a new sticky note via the main window.
        """
        if self.main_window and hasattr(self.main_window, "create_note"):
            self.main_window.create_note()

    def on_pin_clicked(self):
        """
        Toggle pinning the sticky note on top.
        """
        self.set_always_on_top(not self._always_on_top)
        self.update_pin_button()

    def set_always_on_top(self, flag: bool):
        """
        Set the sticky note to always-on-top or normal mode.

        Args:
            flag (bool): True to keep the sticky on top, False to remove.
        """
        self._always_on_top = bool(flag)
        current = int(self.windowFlags())
        top_hint = int(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        if self._always_on_top:
            new_flags = current | top_hint
        else:
            new_flags = current & ~top_hint
        self.setWindowFlags(QtCore.Qt.WindowType(new_flags))
        self.show()
        self.raise_()
        self.activateWindow()

    def on_text_changed(self):
        """
        Handle text changes: emit textChanged signal and save to database if not loading.
        """
        if not self._loading and self.note_id:
            content = self.text_edit.toPlainText()
            self.textChanged.emit(self.note_id, content)
            self.save()

    def show_context_menu(self, pos):
        """
        Show a custom context menu with editing and note actions.

        Args:
            pos (QPoint): Position relative to text_edit where menu is opened.
        """
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

        top_action = menu.addAction(
            "📍 Unpin from Top" if self._always_on_top else "📌 Pin to Top"
        )
        menu.addSeparator()

        color_menu = menu.addMenu("🎨 Background Color")
        for name, color in COLOR_MAP.items():
            action = color_menu.addAction(name)
            action.triggered.connect(lambda checked, c=color: self.change_color(c))
        menu.addSeparator()

        close_action = menu.addAction("❌ Close Sticker")
        action = menu.exec(self.text_edit.mapToGlobal(pos))

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

    def change_color(self, color: str):
        """
        Change the background color of the sticky note.

        Args:
            color (str): New hex color code.
        """
        self.color = color
        self.text_edit.setStyleSheet(
            f"background-color: {color}; border: none; font-size: 12pt;"
        )

        header_color = self.darken_color(color, 0.06)
        self.header_bar_panel.setStyleSheet(f"background-color: {header_color};")

        self.update()

        if not self._loading:
            self.save()
            if self.note_id:
                self.colorChanged.emit(self.note_id, color)

    @staticmethod
    def darken_color(hex_color: str, factor: float = 0.1) -> str:
        """
        Darken a color by a given factor.

        Args:
            hex_color (str): Original hex color code.
            factor (float): Proportion to darken (0.1 = 10%).

        Returns:
            str: Darkened color hex code.
        """
        color = QtGui.QColor(hex_color)
        h, s, v, a = color.getHsv()
        v = max(0, int(v * (1 - factor)))
        darker = QtGui.QColor()
        darker.setHsv(h, s, v, a)
        return darker.name()

    def resizeEvent(self, event):
        """
        Handle resize events: adjust the size grip and save state.
        """
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height(),
        )
        super().resizeEvent(event)
        if not self._loading:
            self.save()

    def toggle_bold(self):
        """
        Toggle bold formatting for selected text.
        """
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QtGui.QTextCharFormat()
        current_weight = cursor.charFormat().fontWeight()
        fmt.setFontWeight(
            QtGui.QFont.Weight.Normal
            if current_weight > QtGui.QFont.Weight.Normal
            else QtGui.QFont.Weight.Bold
        )
        cursor.mergeCharFormat(fmt)

    def toggle_italic(self):
        """
        Toggle italic formatting for selected text.
        """
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QtGui.QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)

    def toggle_strike(self):
        """
        Toggle strikethrough formatting for selected text.
        """
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QtGui.QTextCharFormat()
        fmt.setFontStrikeOut(not cursor.charFormat().fontStrikeOut())
        cursor.mergeCharFormat(fmt)

    def toggle_list(self):
        """
        Toggle bullet list formatting for the current paragraph.
        """
        cursor = self.text_edit.textCursor()
        if cursor.currentList():
            block_fmt = cursor.blockFormat()
            block_fmt.setObjectIndex(-1)
            cursor.setBlockFormat(block_fmt)
        else:
            cursor.createList(QtGui.QTextListFormat.Style.ListDisc)

    def moveEvent(self, event):
        """
        Save note position when moved.
        """
        super().moveEvent(event)
        if not self._loading:
            self.save()

    def paintEvent(self, event):
        """
        Paint the sticky note background color and border.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)

        painter.setBrush(QtGui.QColor(self.color))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

        pen = QtGui.QPen(QtGui.QColor(160, 160, 160, 60))  # серый с прозрачностью 60/255
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def mousePressEvent(self, event):
        """
        Handle mouse press for moving the sticky note window.
        Supports Wayland system move if available.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            platform = QtWidgets.QApplication.platformName()
            if platform == "wayland":
                handle = self.windowHandle()
                if handle:
                    handle.startSystemMove()
            else:
                self._drag_pos = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Handle mouse dragging to move the sticky window.
        """
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton and self._drag_pos:
            if QtWidgets.QApplication.platformName() in ["xcb", "windows"]:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Save window position when mouse is released after dragging.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self._drag_pos:
                self.save()
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def load_from_db(self):
        """
        Load note content, geometry, background color, and top state from the database.
        """
        if self.note_id:
            row = self.db.get(self.note_id)
            if row:
                self.text_edit.setHtml(row["content"])
                self.color = row["color"] or self.color
                self.change_color(self.color)
                self.setGeometry(
                    row["x"] or 300,
                    row["y"] or 200,
                    row["w"] or 260,
                    row["h"] or 200,
                )
                self.set_always_on_top(bool(row["always_on_top"] or 0))
                self.update_pin_button()

    def showEvent(self, event):
        """
        Handle widget show: load from database and mark as open.
        """
        super().showEvent(event)
        self._loading = True
        self.load_from_db()
        if self.note_id:
            self.db.set_open_state(self.note_id, 1)
        self._loading = False

    def save(self):
        """
        Save current state (content, geometry, color, top flag) to the database.
        Avoids saving if nothing changed.
        """
        x, y, w, h = self.x(), self.y(), self.width(), self.height()
        content = self.text_edit.toHtml()
        always_on_top_int = 1 if self._always_on_top else 0
        if (
            self._last_geo == (x, y, w, h)
            and self._last_content == content
            and self._last_color == self.color
            and self._last_always_on_top == always_on_top_int
        ):
            return
        self._last_geo = (x, y, w, h)
        self._last_content = content
        self._last_color = self.color
        self._last_always_on_top = always_on_top_int
        if self.note_id:
            self.db.update(
                self.note_id, content, x, y, w, h, self.color, always_on_top_int
            )
        else:
            self.note_id = self.db.add(
                content, x, y, w, h, self.color, always_on_top_int
            )

    def closeEvent(self, event):
        """
        Save note state and mark as closed in the database when the window is closed.

        Args:
            event (QCloseEvent): Close event triggered by the window.
        """
        self.save()
        if self.note_id:
            self.db.set_open_state(self.note_id, 0)
            self.closed.emit(self.note_id)
        event.ignore()
        self.hide()
