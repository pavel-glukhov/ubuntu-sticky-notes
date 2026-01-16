from PyQt6 import QtCore, QtWidgets


class Ui_StickyWindow(object):
    def setupUi(self, StickyWindow):
        StickyWindow.setObjectName("StickyWindow")
        StickyWindow.resize(300, 400)

        self.verticalLayout = QtWidgets.QVBoxLayout(StickyWindow)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)

        self.header_bar_panel = QtWidgets.QWidget(parent=StickyWindow)
        self.header_bar_panel.setFixedHeight(24)
        self.headerBarLayout = QtWidgets.QHBoxLayout(self.header_bar_panel)
        self.headerBarLayout.setContentsMargins(5, 0, 5, 0)
        self.headerBarLayout.setSpacing(0)

        header_btn_style = """
            QPushButton { 
                background: transparent; 
                border: none; 
                font-size: 14px; 
                color: #555; 
            }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.1); }
        """

        self.btn_add = QtWidgets.QPushButton("+")
        self.btn_add.setFixedSize(24, 24)
        self.btn_add.setStyleSheet(header_btn_style + "font-size: 18px; font-weight: bold;")

        self.headerBarLayout.addWidget(self.btn_add)
        self.headerBarLayout.addStretch()

        self.btn_pin = QtWidgets.QPushButton("📌")
        self.btn_pin.setFixedSize(24, 24)
        self.btn_pin.setStyleSheet(header_btn_style + "font-size: 12px;")
        self.headerBarLayout.addWidget(self.btn_pin)

        self.btn_close = QtWidgets.QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet(header_btn_style + "font-size: 14px;")
        self.headerBarLayout.addWidget(self.btn_close)

        self.verticalLayout.addWidget(self.header_bar_panel)

        # --- ТЕКСТОВОЕ ПОЛЕ ---
        self.text_edit = QtWidgets.QTextEdit(parent=StickyWindow)
        self.text_edit.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_edit.setStyleSheet("background: transparent; border: none; font-size: 12pt; padding: 10px;")
        self.text_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.verticalLayout.addWidget(self.text_edit)

        # --- НИЖНЯЯ ПАНЕЛЬ ФОРМАТИРОВАНИЯ ---
        self.formatting_bar = QtWidgets.QWidget(parent=StickyWindow)
        self.formattingLayout = QtWidgets.QHBoxLayout(self.formatting_bar)
        self.formattingLayout.setContentsMargins(5, 2, 5, 5)
        self.formattingLayout.setSpacing(2)

        button_style = """
            QPushButton { background: transparent; border: none; border-radius: 3px; font-size: 14px; color: #333; }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.08); }
            QPushButton:checked { background-color: rgba(0, 0, 0, 0.15); }
            QPushButton::menu-indicator { image: none; }
        """

        self.btn_bold = QtWidgets.QPushButton("𝐁")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(28, 28)
        self.btn_bold.setStyleSheet(button_style + "font-weight: bold;")

        self.btn_italic = QtWidgets.QPushButton("𝑰")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(28, 28)
        self.btn_italic.setStyleSheet(button_style + "font-family: 'Serif'; font-size: 16px;")

        self.btn_underline = QtWidgets.QPushButton("U̲")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(28, 28)
        self.btn_underline.setStyleSheet(button_style)

        self.btn_strike = QtWidgets.QPushButton("̶S̶")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setFixedSize(28, 28)
        self.btn_strike.setStyleSheet(button_style)

        self.btn_list = QtWidgets.QPushButton("☰")
        self.btn_list.setFixedSize(28, 28)
        self.btn_list.setStyleSheet(button_style + "font-size: 18px;")

        self.btn_color = QtWidgets.QPushButton("🎨")
        self.btn_color.setFixedSize(28, 28)
        self.btn_color.setStyleSheet(button_style + "font-weight: bold; border-bottom: 3px solid #000;")

        self.color_menu = QtWidgets.QMenu(self.btn_color)
        self.color_menu.setStyleSheet("QMenu { border: 1px solid #ccc; background: white; padding: 0px; }")

        self.setup_color_palette()
        self.btn_color.setMenu(self.color_menu)

        self.formattingLayout.addWidget(self.btn_bold)
        self.formattingLayout.addWidget(self.btn_italic)
        self.formattingLayout.addWidget(self.btn_underline)
        self.formattingLayout.addWidget(self.btn_strike)
        self.formattingLayout.addWidget(self.btn_list)
        self.formattingLayout.addWidget(self.btn_color)
        self.formattingLayout.addStretch()

        self.verticalLayout.addWidget(self.formatting_bar)

    def setup_color_palette(self):
        color_widget = QtWidgets.QWidget()
        color_widget.setStyleSheet("background: white; border: none; outline: none;")

        grid = QtWidgets.QGridLayout(color_widget)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setSpacing(4)

        colors = [
            '#000000', '#434343', '#666666', '#999999', '#b7b7b7', '#ffffff',
            '#980000', '#ff0000', '#ff9900', '#ffff00', '#00ff00', '#00ffff',
            '#4a86e8', '#0000ff', '#9900ff', '#ff00ff', '#e6b8af', '#f4cccc',
            '#fce5cd', '#fff2cc', '#d9ead3', '#d0e0e3', '#c9daf8', '#cfe2f3',
            '#d9d2e9', '#ead1dc', '#dd7e6b', '#ea9999', '#f9cb9c', '#ffe599',
            '#b6d7a8', '#a2c4c9', '#a4c2f4', '#9fc5e8', '#b4a7d6', '#d5a6bd'
        ]

        row, col = 0, 0
        for hex_color in colors:
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(22, 22)
            btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #ddd; border-radius: 2px;")
            btn.setProperty("color_val", hex_color)

            grid.addWidget(btn, row, col)
            col += 1
            if col > 5:
                col = 0
                row += 1

        action = QtWidgets.QWidgetAction(self.color_menu)
        action.setDefaultWidget(color_widget)
        self.color_menu.addAction(action)

    def retranslateUi(self, StickyWindow):
        _translate = QtCore.QCoreApplication.translate
        StickyWindow.setWindowTitle(_translate("StickyWindow", "Sticky Note"))