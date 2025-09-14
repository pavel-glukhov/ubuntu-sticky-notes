import sys
import os
from PyQt5 import QtCore, QtWidgets, QtGui
from main_window import MainWindow
from sticky_window import StickyWindow
from about_window import AboutDialog
from config import get_app_paths

paths = get_app_paths()
APP_ICON_PATH = paths["APP_ICON_PATH"]


def init_tray(window: MainWindow, app: QtWidgets.QApplication):
    """
    Initialize the system tray icon and context menu for the application.

    Args:
        window (MainWindow): The main window instance of the application.
        app (QtWidgets.QApplication): The QApplication instance.

    Behavior:
        - Sets the tray icon (uses default theme icon if APP_ICON_PATH does not exist).
        - Creates a context menu with actions:
            - Open Previous State
            - Open All Stickers
            - Hide All Stickers
            - Show Notes List
            - Open New Sticker
            - About dialog
            - Exit application
        - Does not handle icon double-click activation (only context menu is available).
    """
    tray_icon = QtWidgets.QSystemTrayIcon(
        QtGui.QIcon(APP_ICON_PATH) if os.path.exists(APP_ICON_PATH) else QtGui.QIcon.fromTheme("note"),
        app
    )

    tray_menu = QtWidgets.QMenu()

    # --- Actions ---
    tray_menu.addAction("📘 Open Previous State", lambda: open_previous_state(window))
    tray_menu.addAction("📗 Open All Stickers", lambda: open_all_stickies(window))
    tray_menu.addAction("🗂 Hide All Stickers", lambda: hide_all_stickies(window))
    tray_menu.addSeparator()
    tray_menu.addAction("📒 Show Notes List", window.showNormal)
    tray_menu.addAction("🆕 Open New Sticker", window.create_note)
    tray_menu.addSeparator()
    about_action = tray_menu.addAction("About")
    about_action.triggered.connect(lambda: AboutDialog().exec_())
    tray_menu.addSeparator()
    tray_menu.addAction("Exit", app.quit)

    tray_icon.setToolTip("Ubuntu Sticky Notes")
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setVisible(True)
    tray_icon.show()


def open_previous_state(window: MainWindow):
    """
    Open all sticky notes that were previously opened.

    Args:
        window (MainWindow): The main window instance containing the list of notes and sticky windows.

    Behavior:
        - Iterates over the list of note IDs retrieved from the database.
        - Checks if a sticky window is already open and visible.
        - If not, creates a new StickyWindow instance.
        - Connects signals for closed, textChanged, and colorChanged.
        - Loads content from the database and displays the sticky window.
    """
    for note_id in window.db.get_open_notes():
        sticky = window.stickies.get(note_id)
        if sticky and sticky.isVisible():
            continue
        if not sticky:
            sticky = StickyWindow(window.db, note_id)
            sticky.closed.connect(window.refresh_list)
            sticky.textChanged.connect(window.on_sticky_text_changed)
            sticky.colorChanged.connect(window.on_sticky_color_changed)
            window.stickies[note_id] = sticky
        sticky.load_from_db()
        sticky.show()
        sticky.raise_()
        sticky.activateWindow()


def open_all_stickies(window: MainWindow):
    """
    Open all sticky notes listed in the main window's list widget.

    Args:
        window (MainWindow): The main window instance containing the list of notes.

    Behavior:
        - Iterates over all items in the list widget.
        - Opens each note using the `open_note` method of MainWindow.
    """
    for i in range(window.list_widget.count()):
        item = window.list_widget.item(i)
        window.open_note(item)


def hide_all_stickies(window: MainWindow):
    """
    Hide all currently open sticky note windows.

    Args:
        window (MainWindow): The main window instance containing references to sticky windows.

    Behavior:
        - Iterates over all sticky windows stored in `window.stickies`.
        - Calls the `hide()` method on each sticky window.
    """
    for sticky in window.stickies.values():
        sticky.hide()


# ========================
# Main function
# ========================
def main():
    """
    Entry point of the application.

    Behavior:
        - Adjusts the Qt platform plugin for Linux Wayland if necessary.
        - Creates a QApplication instance.
        - Initializes the main window and system tray icon asynchronously using QTimer.
        - Starts the Qt event loop.
    """
    if sys.platform.startswith("linux") and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    def init_app():
        """
        Initialize the main application window and system tray icon.
        """
        window = MainWindow()
        window.hide()
        init_tray(window, app)

    QtCore.QTimer.singleShot(0, init_app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
