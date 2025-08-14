import sys

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFrame,
                               QLabel, QSpinBox, QCheckBox, QPushButton,
                               QSizePolicy, QSpacerItem, QMessageBox)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QKeyEvent
from InvoicePage.price_calculation.price_calculation_models import (PriceDisplayData, DynamicPriceConfig,
                                                                    DynamicPriceMode)


class PriceDialogView(QDialog):
    """Price dialog UI implementation"""

    # Signals
    document_count_changed = Signal(int)
    page_count_changed = Signal(int)
    additional_issues_changed = Signal(int)
    official_toggled = Signal(bool)
    unofficial_toggled = Signal(bool)
    judiciary_toggled = Signal(bool)
    foreign_affairs_toggled = Signal(bool)
    dynamic_price_1_changed = Signal(int)
    dynamic_price_2_changed = Signal(int)
    accept_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, parent=None, document_name: str = ""):
        super().__init__(parent)
        self.document_name = document_name
        self.setup_ui()
        self.setup_connections()
        self.setup_defaults()

    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("محاسبه قیمت")
        self.setFixedSize(550, 600)
        self.setStyleSheet("background-color: rgb(251, 251, 251);")

        # Main layout
        main_layout = QVBoxLayout(self)

        # First frame - main controls
        self.first_frame = self._create_first_frame()
        main_layout.addWidget(self.first_frame)

        # Second frame - dynamic pricing (initially hidden)
        self.second_frame = self._create_second_frame()
        main_layout.addWidget(self.second_frame)

        # Button frame
        button_frame = self._create_button_frame()
        main_layout.addWidget(button_frame)

        # Price display frame
        price_frame = self._create_price_frame()
        main_layout.addWidget(price_frame)

    def _create_first_frame(self) -> QFrame:
        """Create the first frame with main controls"""
        frame = QFrame()
        frame.setMinimumSize(QSize(0, 220))
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(frame)

        # Document and page count row
        count_layout = QHBoxLayout()

        # Page count
        page_layout = QHBoxLayout()
        page_layout.setContentsMargins(20, -1, -1, -1)

        page_label = QLabel("تعداد صفحات")
        page_label.setFont(self._get_font(11))
        page_layout.addWidget(page_label)

        self.page_count_spinbox = QSpinBox()
        self.page_count_spinbox.setMinimumSize(QSize(80, 35))
        self.page_count_spinbox.setMaximumSize(QSize(80, 35))
        self.page_count_spinbox.setMaximum(999)
        self.page_count_spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        page_layout.addWidget(self.page_count_spinbox)

        count_layout.addLayout(page_layout)

        # Document count
        doc_layout = QHBoxLayout()
        doc_layout.setContentsMargins(20, -1, -1, -1)

        doc_label = QLabel("تعداد اسناد")
        doc_label.setFont(self._get_font(11))
        doc_layout.addWidget(doc_label)

        self.document_count_spinbox = QSpinBox()
        self.document_count_spinbox.setMinimumSize(QSize(80, 35))
        self.document_count_spinbox.setMaximumSize(QSize(80, 35))
        self.document_count_spinbox.setMaximum(999)
        self.document_count_spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        doc_layout.addWidget(self.document_count_spinbox)

        count_layout.addLayout(doc_layout)
        layout.addLayout(count_layout)

        # Document type and additional issues row
        type_layout = QHBoxLayout()

        # Additional issues
        additional_layout = QHBoxLayout()
        additional_layout.setContentsMargins(20, -1, -1, -1)

        additional_label = QLabel("تعداد نسخه‌های اضافه")
        additional_label.setFont(self._get_font(11))
        additional_layout.addWidget(additional_label)

        self.additional_issues_spinbox = QSpinBox()
        self.additional_issues_spinbox.setMinimumSize(QSize(80, 35))
        self.additional_issues_spinbox.setMaximumSize(QSize(80, 35))
        self.additional_issues_spinbox.setMaximum(999)
        self.additional_issues_spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        additional_layout.addWidget(self.additional_issues_spinbox)

        type_layout.addLayout(additional_layout)
        layout.addLayout(type_layout)

        # Document type checkboxes
        checkbox_layout = QHBoxLayout()

        type_label = QLabel("نوع ترجمه: ")
        type_label.setFont(self._get_font(11))
        checkbox_layout.addWidget(type_label)

        self.official_checkbox = QCheckBox("رسمی")
        self.official_checkbox.setFont(self._get_font(11))
        self.official_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.official_checkbox)

        self.unofficial_checkbox = QCheckBox("غیر رسمی")
        self.unofficial_checkbox.setFont(self._get_font(11))
        checkbox_layout.addWidget(self.unofficial_checkbox)

        type_layout.addLayout(checkbox_layout)

        # Seals checkboxes
        seals_layout = QHBoxLayout()

        self.foreign_affairs_checkbox = QCheckBox("تصدیق وزارت امور خارجه")
        self.foreign_affairs_checkbox.setFont(self._get_font(11))
        self.foreign_affairs_checkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        seals_layout.addWidget(self.foreign_affairs_checkbox)

        self.judiciary_checkbox = QCheckBox("تصدیق وزارت دادگستری")
        self.judiciary_checkbox.setFont(self._get_font(11))
        self.judiciary_checkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        seals_layout.addWidget(self.judiciary_checkbox)

        layout.addLayout(seals_layout)

        return frame

    def _create_second_frame(self) -> QFrame:
        """Create the second frame for dynamic pricing"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        frame.hide()  # Initially hidden

        layout = QHBoxLayout(frame)

        # Price 1 frame
        self.price_1_frame = QFrame()
        self.price_1_frame.setMinimumSize(QSize(225, 76))
        self.price_1_frame.setMaximumSize(QSize(225, 75))
        self.price_1_frame.setFrameShape(QFrame.Shape.StyledPanel)

        price_1_layout = QVBoxLayout(self.price_1_frame)

        self.dynamic_price_1_label = QLabel("TextLabel")
        self.dynamic_price_1_label.setFont(self._get_font(10))
        self.dynamic_price_1_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.dynamic_price_1_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_1_layout.addWidget(self.dynamic_price_1_label)

        self.dynamic_price_1_spinbox = QSpinBox()
        self.dynamic_price_1_spinbox.setMaximum(999)
        price_1_layout.addWidget(self.dynamic_price_1_spinbox)

        layout.addWidget(self.price_1_frame)

        # Price 2 frame
        self.price_2_frame = QFrame()
        self.price_2_frame.setMinimumSize(QSize(225, 75))
        self.price_2_frame.setMaximumSize(QSize(225, 75))
        self.price_2_frame.setFrameShape(QFrame.Shape.StyledPanel)

        price_2_layout = QVBoxLayout(self.price_2_frame)

        self.dynamic_price_2_label = QLabel("TextLabel")
        self.dynamic_price_2_label.setFont(self._get_font(10))
        self.dynamic_price_2_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.dynamic_price_2_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_2_layout.addWidget(self.dynamic_price_2_label)

        self.dynamic_price_2_spinbox = QSpinBox()
        self.dynamic_price_2_spinbox.setMaximum(999)
        price_2_layout.addWidget(self.dynamic_price_2_spinbox)

        layout.addWidget(self.price_2_frame)

        return frame

    def _create_button_frame(self) -> QFrame:
        """Create the button frame"""
        frame = QFrame()
        frame.setMinimumSize(QSize(0, 50))
        frame.setMaximumSize(QSize(16777215, 50))
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(frame)
        layout.setSpacing(40)
        layout.setContentsMargins(70, -1, 70, -1)

        # Accept button
        self.accept_button = QPushButton("تایید")
        self.accept_button.setFont(self._get_font(12))
        layout.addWidget(self.accept_button)

        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Cancel button
        self.cancel_button = QPushButton("انصراف")
        self.cancel_button.setFont(self._get_font(12))
        layout.addWidget(self.cancel_button)

        return frame

    def _create_price_frame(self) -> QFrame:
        """Create the price display frame"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        # Translation and judiciary prices row
        tr_judiciary_layout = QHBoxLayout()

        # Judiciary price
        judiciary_text = QLabel("هزینه تاییدات")
        judiciary_text.setFont(self._get_font())
        tr_judiciary_layout.addWidget(judiciary_text)

        self.judiciary_price_label = QLabel("۰ تومان")
        self.judiciary_price_label.setFont(self._get_font())
        self.judiciary_price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tr_judiciary_layout.addWidget(self.judiciary_price_label)

        tr_judiciary_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Translation price
        translation_text = QLabel("هزینه ترجمه")
        translation_text.setFont(self._get_font())
        tr_judiciary_layout.addWidget(translation_text)

        self.translation_price_label = QLabel("۰ تومان")
        self.translation_price_label.setFont(self._get_font())
        self.translation_price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tr_judiciary_layout.addWidget(self.translation_price_label)

        layout.addLayout(tr_judiciary_layout)

        # Office and page prices row
        office_page_layout = QHBoxLayout()

        # Office price
        office_text = QLabel("هزینه امور دفتری")
        office_text.setFont(self._get_font())
        office_page_layout.addWidget(office_text)

        self.office_price_label = QLabel("۰ تومان")
        self.office_price_label.setFont(self._get_font())
        self.office_price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        office_page_layout.addWidget(self.office_price_label)

        office_page_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Page price
        page_text = QLabel("هزینه کپی برابر اصل")
        page_text.setFont(self._get_font())
        office_page_layout.addWidget(page_text)

        self.page_price_label = QLabel("۰ تومان")
        self.page_price_label.setFont(self._get_font())
        self.page_price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        office_page_layout.addWidget(self.page_price_label)

        layout.addLayout(office_page_layout)

        # Total and additional prices row
        total_additional_layout = QHBoxLayout()

        # Additional issues price
        additional_text = QLabel("هزینه نسخه اضافی")
        additional_text.setFont(self._get_font(9))
        total_additional_layout.addWidget(additional_text)

        self.additional_price_label = QLabel("۰ تومان")
        self.additional_price_label.setFont(self._get_font())
        self.additional_price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_additional_layout.addWidget(self.additional_price_label)

        total_additional_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        total_additional_layout.addStretch()

        # Total price
        total_text = QLabel("قیمت کل")
        total_text.setFont(self._get_font())
        total_additional_layout.addWidget(total_text)

        self.total_price_label = QLabel("۰ تومان")
        self.total_price_label.setFont(self._get_font())
        self.total_price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_additional_layout.addWidget(self.total_price_label)

        layout.addLayout(total_additional_layout)

        return frame

    @staticmethod
    def _get_font(size: int = 11, bold: bool = False) -> QFont:
        """Get font with specified parameters"""
        font = QFont()
        font.setFamilies(["IRANSans"])
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def setup_connections(self):
        """Setup signal connections"""
        # Spinbox connections
        self.document_count_spinbox.valueChanged.connect(self.document_count_changed.emit)
        self.page_count_spinbox.valueChanged.connect(self.page_count_changed.emit)
        self.additional_issues_spinbox.valueChanged.connect(self.additional_issues_changed.emit)
        self.dynamic_price_1_spinbox.valueChanged.connect(self.dynamic_price_1_changed.emit)
        self.dynamic_price_2_spinbox.valueChanged.connect(self.dynamic_price_2_changed.emit)

        # Checkbox connections
        self.official_checkbox.toggled.connect(self._on_official_toggled)
        self.unofficial_checkbox.toggled.connect(self._on_unofficial_toggled)
        self.judiciary_checkbox.toggled.connect(self.judiciary_toggled.emit)
        self.foreign_affairs_checkbox.toggled.connect(self.foreign_affairs_toggled.emit)

        # Button connections
        self.accept_button.clicked.connect(self.accept_clicked.emit)
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)

    def _on_official_toggled(self, checked: bool):
        """Handle official checkbox toggle"""
        if checked:
            self.unofficial_checkbox.setChecked(False)
        self.official_toggled.emit(checked)

    def _on_unofficial_toggled(self, checked: bool):
        """Handle unofficial checkbox toggle"""
        if checked:
            self.official_checkbox.setChecked(False)
        self.unofficial_toggled.emit(checked)

    def setup_defaults(self):
        """Setup default values"""
        self.document_count_spinbox.setValue(1)
        self.page_count_spinbox.setValue(1)
        self.additional_issues_spinbox.setValue(0)
        self.dynamic_price_1_spinbox.setValue(0)
        self.dynamic_price_2_spinbox.setValue(0)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept_clicked.emit()
        else:
            super().keyPressEvent(event)

    # Getters for current values
    def get_document_count(self) -> int:
        return self.document_count_spinbox.value()

    def get_page_count(self) -> int:
        return self.page_count_spinbox.value()

    def get_additional_issues(self) -> int:
        return self.additional_issues_spinbox.value()

    def get_dynamic_price_1_count(self) -> int:
        return self.dynamic_price_1_spinbox.value()

    def get_dynamic_price_2_count(self) -> int:
        return self.dynamic_price_2_spinbox.value()

    def is_official(self) -> bool:
        return self.official_checkbox.isChecked()

    def has_judiciary_seal(self) -> bool:
        return self.judiciary_checkbox.isChecked()

    def has_foreign_affairs_seal(self) -> bool:
        return self.foreign_affairs_checkbox.isChecked()

    # Setters for values
    def set_document_count(self, value: int):
        self.document_count_spinbox.setValue(value)

    def set_page_count(self, value: int):
        self.page_count_spinbox.setValue(value)

    def set_additional_issues(self, value: int):
        self.additional_issues_spinbox.setValue(value)

    def set_dynamic_price_1_count(self, value: int):
        self.dynamic_price_1_spinbox.setValue(value)

    def set_dynamic_price_2_count(self, value: int):
        self.dynamic_price_2_spinbox.setValue(value)

    def set_official(self, official: bool):
        self.official_checkbox.setChecked(official)
        self.unofficial_checkbox.setChecked(not official)

    def set_judiciary_seal(self, checked: bool):
        self.judiciary_checkbox.setChecked(checked)

    def set_foreign_affairs_seal(self, checked: bool):
        self.foreign_affairs_checkbox.setChecked(checked)

    # Display methods
    def update_price_display(self, data: PriceDisplayData):
        """Update price display labels"""
        self.translation_price_label.setText(data.translation_price)
        self.page_price_label.setText(data.page_price)
        self.office_price_label.setText(data.office_price)
        self.judiciary_price_label.setText(data.judiciary_price)
        self.additional_price_label.setText(data.additional_price)
        self.total_price_label.setText(data.total_price)

    def configure_dynamic_pricing(self, config: DynamicPriceConfig):
        """Configure dynamic pricing UI"""
        if config.mode == DynamicPriceMode.NONE:
            self.second_frame.hide()
        elif config.mode == DynamicPriceMode.SINGLE:
            self.second_frame.show()
            self.price_2_frame.hide()
            if config.label1:
                self.dynamic_price_1_label.setText(config.label1)
                self.dynamic_price_1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif config.mode == DynamicPriceMode.DOUBLE:
            self.second_frame.show()
            self.price_2_frame.show()
            if config.label1:
                self.dynamic_price_1_label.setText(config.label1)
                self.dynamic_price_1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if config.label2:
                self.dynamic_price_2_label.setText(config.label2)
                self.dynamic_price_2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def show_error_message(self, title: str, message: str):
        """Show error message box"""
        QMessageBox.warning(self, title, message)

    def show_validation_error(self, message: str):
        """Show validation error"""
        self.show_error_message("خطای ورودی", message)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    window = PriceDialogView()
    window.show()
    sys.exit(app.exec())
