import os
import sys

from about_window import AboutDialog
from config import get_app_paths
from main_window import MainWindow
from PyQt6 import QtCore, QtGui, QtWidgets
from sticky_window import StickyWindow

paths = get_app_paths()
APP_ICON_PATH = paths["APP_ICON_PATH"]
APP_INFO = paths["APP_INFO"]


def init_tray(window: MainWindow, app: QtWidgets.QApplication):
    """
    Initialize the system tray icon and context menu.

    Provides quick access to:
        - Restoring previous state.
        - Opening or hiding all sticky notes.
        - Showing notes list.
        - Creating a new sticky note.
        - About dialog.
        - Exiting the application.
    """
    tray_icon = QtWidgets.QSystemTrayIcon(
        QtGui.QIcon(APP_ICON_PATH) if os.path.exists(APP_ICON_PATH) else QtGui.QIcon.fromTheme("note"),
        app,
    )

    tray_menu = QtWidgets.QMenu()
    tray_menu.addAction("📘 Open Previous State", lambda: open_previous_state(window))
    tray_menu.addAction("📗 Open All Stickers", lambda: open_all_stickies(window))
    tray_menu.addAction("🗂 Hide All Stickers", lambda: hide_all_stickies(window))
    tray_menu.addSeparator()
    tray_menu.addAction("📒 Show Notes List", window.showNormal)
    tray_menu.addAction("🆕 Open New Sticker", window.create_note)
    tray_menu.addSeparator()

    about_action = tray_menu.addAction("About")
    about_action.triggered.connect(lambda: AboutDialog().exec())
    tray_menu.addSeparator()

    def exit_app():
        for sticky in window.stickies.values():
            if sticky.isVisible():
                sticky.save()
                if sticky.note_id:
                    window.db.set_open_state(sticky.note_id, 1)
            else:
                if sticky.note_id:
                    window.db.set_open_state(sticky.note_id, 0)

        if hasattr(window.db, "close"):
            window.db.close()
        app.quit()
        QtWidgets.QApplication.exit(0)

    tray_menu.addAction("Exit", exit_app)

    tray_icon.setToolTip("Ubuntu Sticky Notes")
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setVisible(True)

    def toggle_main_window():
        if window.isVisible() and not window.isMinimized():
            window.hide()
        else:
            window.showNormal()
            window.raise_()
            window.activateWindow()

    def on_tray_activated(reason):
        if reason in (
            QtWidgets.QSystemTrayIcon.ActivationReason.Trigger,
            QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            toggle_main_window()

    tray_icon.activated.connect(on_tray_activated)
    tray_icon.show()


def show_main_window(window: QtWidgets.QMainWindow):
    """
    Bring the main window to the foreground.

    Ensures the window is visible and active, restoring if minimized.
    """
    if window.isHidden() or window.isMinimized():
        window.showNormal()
    else:
        window.show()

    window.raise_()
    window.activateWindow()


def open_previous_state(window: MainWindow):
    """
    Restore and open all sticky notes that were previously open.
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
    Open all sticky notes from the main window's list.
    """
    for i in range(window.list_widget.count()):
        item = window.list_widget.item(i)
        window.open_note(item)


def hide_all_stickies(window: MainWindow):
    """
    Hide all currently open sticky notes.
    """
    for sticky in window.stickies.values():
        sticky.hide()


def main():
    """
    Application entry point.

    Handles platform quirks (e.g., Wayland vs X11),
    initializes QApplication, main window, and system tray.
    """
    if sys.platform.startswith("linux") and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_INFO.get("app_name", "Sticky Notes"))

    def init_app():
        window = MainWindow()
        window.hide()
        init_tray(window, app)

    QtCore.QTimer.singleShot(0, init_app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
