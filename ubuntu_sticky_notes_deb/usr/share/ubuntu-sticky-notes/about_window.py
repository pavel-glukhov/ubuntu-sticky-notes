import os
from PyQt5 import QtWidgets, uic
from config import get_app_paths

paths = get_app_paths()
APP_INFO = paths["APP_INFO"]
UI_PATH = paths["UI_DIR"]


class AboutDialog(QtWidgets.QDialog):
    """
    About dialog displaying application information.

    Shows the app's name, version, author, contact, website, description, and license.
    """

    def __init__(self, parent=None):
        """
        Initialize the AboutDialog UI.

        Loads the UI from `aboutdialog.ui`, sets the text labels with application info,
        and connects the OK/Close button.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        ui_path = os.path.join(UI_PATH, "aboutdialog.ui")
        uic.loadUi(ui_path, self)

        self.setWindowTitle(f"About {APP_INFO['name']}")
        self.label_title.setText(f"<h2>{APP_INFO['name']}</h2>")
        self.label_info.setText(
            f"Version: {APP_INFO['version']}<br>"
            f"Author: {APP_INFO['author']}<br>"
            f"Email: {APP_INFO['email']}<br>"
            f"<a href='{APP_INFO['website']}'>{APP_INFO['website']}</a>"
        )
        self.label_description.setText(APP_INFO['description'])
        self.label_license.setText(f"<i>{APP_INFO['license']}</i>")

        self.buttonBox.accepted.connect(self.accept)
