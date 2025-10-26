import os

from config import get_app_paths
from PyQt6 import QtWidgets
from resources.ui_py.aboutdialog import Ui_AboutDialog

paths = get_app_paths()
APP_INFO = paths["APP_INFO"]
UI_PATH = paths["UI_DIR"]


class AboutDialog(QtWidgets.QDialog):
    """
    Dialog window displaying information about the application.

    Features:
        - Shows application name and version.
        - Displays author information, contact email, and website link.
        - Provides a short description and license details.
        - Contains a close button to dismiss the dialog.
    """

    def __init__(self, parent=None):
        """
        Initialize the AboutDialog.

        Args:
            parent (QWidget, optional): Parent widget for the dialog.
        """
        super().__init__(parent)

        ui_path = os.path.join(UI_PATH, "aboutdialog.ui_qt")
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

        self.setWindowTitle(f"About {APP_INFO['app_name']}")
        self.label_title.setText(f"<h2>{APP_INFO['app_name']}</h2>")
        self.label_info.setText(
            f"Version: {APP_INFO['version']}<br>"
            f"Author: {APP_INFO['author']}<br>"
            f"Email: {APP_INFO['email']}<br>"
            f"<a href='{APP_INFO['website']}'>{APP_INFO['website']}</a>"
        )
        self.label_description.setText(APP_INFO["description"])
        self.label_license.setText(f"<i>{APP_INFO['license']}</i>")

        self.buttonBox.accepted.connect(self.accept)
