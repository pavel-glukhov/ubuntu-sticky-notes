from PyQt6 import QtCore, QtWidgets, QtGui


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
                        padding: 0px;
                        margin: 0px; 
                        text-align: center;
                    }
                    QPushButton:hover { background-color: rgba(0, 0, 0, 0.1); }
                """
        button_size = 28
        line_width = 18
        self.button_style_common = """
            QPushButton { 
                background: transparent; 
                border: none; 
                border-radius: 3px; 
                font-size: 16px; 
                color: #333; 
                padding: 0px;     
                margin: 0px; 
                qproperty-iconSize: 18px;
                text-align: center;
            }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.08); }
            QPushButton:checked { background-color: rgba(0, 0, 0, 0.15); }
            QPushButton::menu-indicator { image: none; }
        """
        # ---------------- Header Buttons ----------------

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

        self.text_edit = QtWidgets.QTextEdit(parent=StickyWindow)
        self.text_edit.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_edit.setStyleSheet("background: transparent; border: none; font-size: 12pt; padding: 10px;")
        self.text_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.verticalLayout.addWidget(self.text_edit)

        self.formatting_bar = QtWidgets.QWidget(parent=StickyWindow)
        self.formattingLayout = QtWidgets.QHBoxLayout(self.formatting_bar)
        self.formattingLayout.setContentsMargins(5, 2, 5, 5)
        self.formattingLayout.setSpacing(2)

        # ---------------- Formatting Buttons ----------------
        # Bold
        self.btn_bold = QtWidgets.QPushButton("𝐁")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(button_size, button_size)
        self.btn_bold.setStyleSheet(self.button_style_common + "font-weight: bold;")
        # Italic
        self.btn_italic = QtWidgets.QPushButton("𝑰")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(button_size, button_size)
        self.btn_italic.setStyleSheet(self.button_style_common)
        # Underline
        self.btn_underline = QtWidgets.QPushButton("U̲")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(button_size, button_size)
        self.btn_underline.setStyleSheet(self.button_style_common)
        # Strike-through
        self.btn_strike = QtWidgets.QPushButton("̶S̶")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setFixedSize(button_size, button_size)
        self.btn_strike.setStyleSheet(self.button_style_common)
        # List / Bullet
        self.btn_list = QtWidgets.QPushButton("☰")
        self.btn_list.setFixedSize(button_size, button_size)
        self.btn_list.setStyleSheet(self.button_style_common)
        # ---------------- Color Button ----------------
        self.btn_color = QtWidgets.QPushButton()
        self.btn_color.setFixedSize(button_size, button_size)
        self.btn_color.setStyleSheet(self.button_style_common)
        self.btn_color.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        layout_color = QtWidgets.QVBoxLayout(self.btn_color)
        layout_color.setContentsMargins(0, 0, 0, 0)
        layout_color.setSpacing(0)
        layout_color.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.label_a = QtWidgets.QLabel("A", parent=self.btn_color)
        self.label_a.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout_color.addWidget(self.label_a)

        line_container = QtWidgets.QWidget(self.btn_color)
        line_layout = QtWidgets.QHBoxLayout(line_container)
        line_layout.setContentsMargins(0, 0, 0, 0)
        line_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # line under color button
        self.color_indicator = QtWidgets.QFrame(line_container)
        self.color_indicator.setFixedSize(line_width, 3)
        self.color_indicator.setStyleSheet("background-color: black; border-radius: 1px;")
        line_layout.addWidget(self.color_indicator)

        layout_color.addWidget(line_container)

        self.color_menu = QtWidgets.QMenu(self.btn_color)
        self.color_menu.setStyleSheet("QMenu { border: 1px solid #ccc; background: white; padding: 0px; }")

        self.setup_color_palette()
        self.btn_color.setMenu(self.color_menu)

        # ---------------- Font Size ComboBox ----------------
        self.combo_font_size = QtWidgets.QComboBox(parent=self.formatting_bar)
        self.combo_font_size.setFixedSize(75, button_size)

        font_sizes = ["8", "10", "12", "14", "16", "18", "20", "24", "28", "32"]
        for size in font_sizes:
            self.combo_font_size.addItem(f"Font: {size}", size)

        self.combo_font_size.setCurrentIndex(2)  # Font 12

        self.combo_font_size.lineEdit = QtWidgets.QLineEdit()  # Создаем, но не включаем editable

        self.combo_font_size.setStyleSheet("""
                    QComboBox {
                        background: transparent;
                        border: none;
                        border-radius: 3px;
                        font-size: 13px;
                        color: #555;
                        padding-left: 5px;
                        text-align: center;
                    }
                    QComboBox:hover { 
                        background-color: rgba(0, 0, 0, 0.08); 
                        color: #000;
                    }
                    QComboBox::drop-down { border: 0px; width: 0px; }
                    QComboBox::down-arrow { image: none; }

                    QComboBox QAbstractItemView {
                        border: 1px solid #ccc;
                        background-color: white;
                        selection-background-color: rgba(0, 0, 0, 0.1);
                        selection-color: #000;
                        outline: none;
                    }
                """)
        for i in range(self.combo_font_size.count()):
            self.combo_font_size.setItemData(i, QtCore.Qt.AlignmentFlag.AlignCenter,
                                             QtCore.Qt.ItemDataRole.TextAlignmentRole)

        self.formattingLayout.addWidget(self.btn_bold)
        self.formattingLayout.addWidget(self.btn_italic)
        self.formattingLayout.addWidget(self.btn_underline)
        self.formattingLayout.addWidget(self.btn_strike)
        self.formattingLayout.addWidget(self.btn_list)
        self.formattingLayout.addWidget(self.btn_color)
        self.formattingLayout.addWidget(self.combo_font_size)
        self.formattingLayout.addStretch()

        self.verticalLayout.addWidget(self.formatting_bar)

    def setup_color_palette(self):
        color_widget = QtWidgets.QWidget()
        color_widget.setFixedSize(160, 160)
        color_widget.setStyleSheet("background: white; border: none;")

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
