import os
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from notes_db import NotesDB
from config import AUTOSAVE_INTERVAL_MS, COLOR_MAP, get_app_paths

paths = get_app_paths()
UI_PATH = paths["UI_DIR"]


class StickyWindow(QtWidgets.QWidget):
    """
    A sticky note window supporting text editing, formatting, autosave, drag, and resize.

    Signals:
        closed (int): Emitted when the sticky note is closed; provides the note ID.
        textChanged (int, str): Emitted when text content changes; provides the note ID and content.
        colorChanged (int, str): Emitted when background color changes; provides the note ID and new color.
    """

    closed = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(int, str)
    colorChanged = QtCore.pyqtSignal(int, str)

    def __init__(self, db: NotesDB, note_id=None, always_on_top=False):
        """
        Initialize a sticky note window.

        Args:
            db (NotesDB): The database instance for storing notes.
            note_id (int, optional): The ID of the note to load. Defaults to None for new notes.
            always_on_top (bool, optional): Whether the window should stay on top. Defaults to False.
        """
        super().__init__()
        self.db = db
        self.note_id = note_id
        self._always_on_top = bool(always_on_top)

        ui_path = os.path.join(UI_PATH, "stickywindow.ui")
        uic.loadUi(ui_path, self)

        flags = QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint
        if self._always_on_top:
            flags |= QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setMinimumSize(300, 300)

        self._last_geo = None
        self._last_content = None
        self._last_color = None
        self._last_always_on_top = 0
        self._loading = True
        self._drag_pos = None
        self.margin = 15
        self.color = "#FFF59D"

        shortcuts = {
            "Ctrl+B": self.toggle_bold,
            "Ctrl+I": self.toggle_italic,
            "Ctrl+Shift+S": self.toggle_strike,
            "Ctrl+Shift+L": self.toggle_list,
        }
        for key, slot in shortcuts.items():
            QtWidgets.QShortcut(QtGui.QKeySequence(key), self, slot)

        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)
        self.text_edit.textChanged.connect(self.on_text_changed)

        self.autosave_timer = QtCore.QTimer(self)
        self.autosave_timer.setInterval(AUTOSAVE_INTERVAL_MS)
        self.autosave_timer.timeout.connect(self.save)
        self.autosave_timer.start()

    def set_always_on_top(self, flag: bool):
        """
        Set or unset the always-on-top property for the sticky window.

        Args:
            flag (bool): True to keep window on top, False otherwise.
        """
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
        """
        Emit the textChanged signal when the content changes and trigger autosave.

        This is only executed if the note is not in loading state.
        """
        if not self._loading and self.note_id:
            content = self.text_edit.toPlainText()
            self.textChanged.emit(self.note_id, content)
            self.save()

    def show_context_menu(self, pos):
        """
        Show the context menu at the given position.

        Args:
            pos (QPoint): Position where the menu should appear.
        """
        menu = QtWidgets.QMenu(self)

        # Actions
        copy_action = menu.addAction("📋 Copy (Ctrl+C)")
        paste_action = menu.addAction("📥 Paste (Ctrl+V)")
        select_all_action = menu.addAction("🔲 Select All (Ctrl+A)")
        menu.addSeparator()

        bold_action = menu.addAction("Bold (Ctrl+B)")
        italic_action = menu.addAction("Italic (Ctrl+I)")
        strike_action = menu.addAction("Strike (Shift+S)")
        list_action = menu.addAction("Bullet List (Shift+L)")
        menu.addSeparator()

        top_action = menu.addAction("📍 Unpin from Top" if self._always_on_top else "📌 Pin to Top")
        menu.addSeparator()

        color_menu = menu.addMenu("🎨 Background Color")
        for name, color in COLOR_MAP.items():
            action = color_menu.addAction(name)
            action.triggered.connect(lambda checked, c=color: self.change_color(c))
        menu.addSeparator()

        close_action = menu.addAction("❌ Close Sticker")
        action = menu.exec_(self.text_edit.mapToGlobal(pos))

        # Execute selected action
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
        """
        Change the background color of the sticky note.

        Args:
            color (str): Hex color code to apply.
        """
        self.color = color
        self.update()
        self.save()
        if self.note_id:
            self.colorChanged.emit(self.note_id, color)

    def resizeEvent(self, event):
        """
        Handle window resize events.

        Adjusts the text edit area and size grip, then triggers save if not loading.
        """
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
        if not cursor.hasSelection():
            return
        fmt = QtGui.QTextCharFormat()
        fmt.setFontWeight(QtGui.QFont.Normal if cursor.charFormat().fontWeight() > QtGui.QFont.Normal else QtGui.QFont.Bold)
        cursor.mergeCharFormat(fmt)

    def toggle_italic(self):
        """Toggle italic formatting on selected text."""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QtGui.QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)

    def toggle_strike(self):
        """Toggle strike-through formatting on selected text."""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QtGui.QTextCharFormat()
        fmt.setFontStrikeOut(not cursor.charFormat().fontStrikeOut())
        cursor.mergeCharFormat(fmt)

    def toggle_list(self):
        """Toggle bullet list for the selected paragraph(s)."""
        cursor = self.text_edit.textCursor()
        if cursor.currentList():
            block_fmt = cursor.blockFormat()
            block_fmt.setObjectIndex(-1)
            cursor.setBlockFormat(block_fmt)
        else:
            cursor.createList(QtGui.QTextListFormat.ListDisc)

    def moveEvent(self, event):
        """Save state when the window is moved."""
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
        """Handle the start of window dragging with the mouse."""
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
        """Handle window dragging with the mouse."""
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            if QtWidgets.QApplication.platformName() in ["xcb", "windows"]:
                self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle end of window dragging and save state."""
        if event.button() == QtCore.Qt.LeftButton:
            if self._drag_pos:
                self.save()
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def load_from_db(self):
        """Load note content, geometry, color, and always-on-top state from the database."""
        if self.note_id:
            row = self.db.get(self.note_id)
            if row:
                self.text_edit.setHtml(row["content"])
                self.color = row["color"] or self.color
                self.setGeometry(row["x"] or 300, row["y"] or 200, row["w"] or 260, row["h"] or 200)
                self.set_always_on_top(bool(row["always_on_top"] or 0))

    def showEvent(self, event):
        """Handle show event; mark as loading, load data from DB, set open state, then stop loading."""
        super().showEvent(event)
        self._loading = True
        self.load_from_db()
        if self.note_id:
            self.db.set_open_state(self.note_id, 1)
        self._loading = False

    def save(self):
        """Save note geometry, content, color, and always-on-top state to the database."""
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
        """
        Intercept the close event to save the note and hide the window instead of destroying it.

        Emits:
            closed signal with the note ID.
        """
        self.save()
        if self.note_id:
            self.db.set_open_state(self.note_id, 0)
            self.closed.emit(self.note_id)
        event.ignore()
        self.hide()
