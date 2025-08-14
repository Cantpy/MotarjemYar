# document_selection/price_calculation_dialog.py
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QGraphicsDropShadowEffect,
    QLineEdit, QHBoxLayout, QCheckBox, QTextEdit, QFrame
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import Service, InvoiceItem, FixedPrice
from features.Invoice_Page_GAS.document_selection_GAS.documents_selection_qss_styles import DIALOG_STYLESHEET
from typing import Dict, List
from shared import to_persian_number
from shared.widgets.persian_spinbox import PersianSpinBox

CERTIFIED_COPY_KEY = "certified_copy"
OFFICIAL_TRANSLATION_KEY = "official_translation"
JUDICIARY_SEAL_KEY = "judiciary_seal"
FOREIGN_AFFAIRS_SEAL_KEY = "foreign_affairs_seal"
ADDITIONAL_ISSUES_KEY = "additional_issues"
SEALS_TOTAL_KEY = "seals_total_price"


class CalculationDialog(QDialog):
    def __init__(self, service: Service, fees: List[FixedPrice], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"محاسبه قیمت: {service.name}")
        self.setMinimumWidth(700)
        self.setStyleSheet(DIALOG_STYLESHEET)
        self.setFont(QFont("IranSANS", 11))

        self.service = service
        self.fees_map: Dict[str, FixedPrice] = {fee.name: fee for fee in fees}
        self.result_item = None
        self.calculated_prices: Dict[str, int] = {}

        self._user_manual_remarks = ""
        self._is_programmatically_updating_remarks = False

        # --- Create UI sections ---
        main_layout = QVBoxLayout(self)
        self._create_translation_price_group(main_layout)
        self._create_options_group(main_layout)
        main_layout.addWidget(QLabel("توضیحات (یادداشت دستی در انتها اضافه می‌شود):"))
        self.remarks_edit = QTextEdit()
        main_layout.addWidget(self.remarks_edit)
        self._create_price_breakdown_group(main_layout)

        # Add a visual separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("تایید")
        ok_button.setObjectName("PrimaryButton")
        cancel_button = button_box.button(QDialogButtonBox.ButtonRole.Cancel)
        cancel_button.setText("انصراف")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._connect_signals()
        self._update_totals()

    def _apply_shadow_effect(self, widget: QGroupBox):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

    def _create_translation_price_group(self, layout):
        group = QGroupBox("محاسبه قیمت ترجمه")
        self.dynamic_spinboxes = {}

        # --- FIX: Smart Horizontal/Vertical Layout ---
        num_dynamic = len(self.service.dynamic_prices)

        # Use a horizontal layout only if it makes sense (2 or 3 items)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)  # Spacing between dynamic price groups

        for i, dyn_price in enumerate(self.service.dynamic_prices):
            label_text = dyn_price.name
            if label_text.startswith("هر"):
                label_text = label_text.replace("هر", "تعداد", 1)

            label = QLabel(f"{label_text}:")
            # --- FIX: Use PersianSpinBox ---
            spinbox = PersianSpinBox()  # No suffix needed here
            spinbox.setRange(0, 9999)  # More reasonable range for these items
            self.dynamic_spinboxes[dyn_price.name] = spinbox

            # Add to the appropriate layout
            item_layout = QHBoxLayout()
            item_layout.addWidget(label)
            item_layout.addWidget(spinbox)
            content_layout.addLayout(item_layout)

        group.setLayout(content_layout)

        if not self.dynamic_spinboxes:
            group.setVisible(False)

        self._apply_shadow_effect(group)
        layout.addWidget(group)

    def _create_options_group(self, layout):
        group = QGroupBox("تنظیمات و تاییدات")
        grid = QGridLayout(group)
        grid.setSpacing(15)  # Increased spacing

        # --- FIX: Use PersianSpinBox ---
        self.quantity_spin = PersianSpinBox(suffix="نسخه")
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setValue(1)

        self.page_count_spin = PersianSpinBox(suffix="صفحه")
        self.page_count_spin.setMinimum(1)
        self.page_count_spin.setValue(1)

        self.extra_copies_spin = PersianSpinBox(suffix="نسخه")

        self.is_official_check = QCheckBox("ترجمه رسمی است")
        self.jud_seal_check = QCheckBox("مهر دادگستری")
        self.fa_seal_check = QCheckBox("مهر امور خارجه")

        grid.addWidget(QLabel("تعداد نسخه اصلی:"), 0, 0)
        grid.addWidget(self.quantity_spin, 0, 1)
        grid.addWidget(QLabel("تعداد صفحات:"), 0, 2)
        grid.addWidget(self.page_count_spin, 0, 3)

        grid.addWidget(QLabel("تعداد نسخه اضافی:"), 1, 0)
        grid.addWidget(self.extra_copies_spin, 1, 1)

        grid.addWidget(self.is_official_check, 2, 0)
        grid.addWidget(self.jud_seal_check, 2, 1)
        grid.addWidget(self.fa_seal_check, 2, 2)

        self._apply_shadow_effect(group)
        layout.addWidget(group)

    def _create_price_breakdown_group(self, layout):
        group = QGroupBox("ریز قیمت‌ها")
        grid = QGridLayout(group)
        grid.setSpacing(15)
        self.price_displays: Dict[str, QLabel] = {}

        def get_cleaned_label(key: str, default_text: str) -> str:
            fee_object = self.fees_map.get(key)
            if fee_object:
                return fee_object.label_name.split('(')[0].strip()
            return default_text

        # This list now controls the UI creation order and uses our constants
        fields_to_display = {
            'translation_price': "قیمت ترجمه",
            CERTIFIED_COPY_KEY: get_cleaned_label(CERTIFIED_COPY_KEY, 'کپی برابر اصل'),
            OFFICIAL_TRANSLATION_KEY: get_cleaned_label(OFFICIAL_TRANSLATION_KEY, 'ثبت رسمی'),
            SEALS_TOTAL_KEY: "هزینه تاییدات",
            ADDITIONAL_ISSUES_KEY: get_cleaned_label(ADDITIONAL_ISSUES_KEY, 'نسخه اضافی'),
            'total_price': "هزینه کل آیتم"
        }

        i = 0
        for key, label_text in fields_to_display.items():
            field_label = QLabel(f"{label_text}:")

            # --- FIX: Use QLabel for price display ---
            price_display_label = QLabel("0")
            self.price_displays[key] = price_display_label

            # Apply styling
            if key == 'total_price':
                self._style_cost_label(price_display_label)
            else:
                self._style_info_label(price_display_label)

            row, col = divmod(i, 2)
            grid.addWidget(field_label, row, col * 2)
            grid.addWidget(price_display_label, row, col * 2 + 1)
            i += 1

        self._apply_shadow_effect(group)
        layout.addWidget(group)

    def _get_fee(self, name: str) -> int:
        """Helper to safely get a fee price from the map using its key."""
        fee = self.fees_map.get(name)
        return fee.price if fee else 0

    def _connect_signals(self):
        """Connect all interactive widgets to the calculation method."""
        for spinbox in self.dynamic_spinboxes.values():
            spinbox.valueChanged.connect(self._update_totals)
            spinbox.valueChanged.connect(self._update_remarks_display)
        self.extra_copies_spin.valueChanged.connect(self._update_remarks_display)
        self.quantity_spin.valueChanged.connect(self._update_totals)
        self.page_count_spin.valueChanged.connect(self._update_totals)
        self.extra_copies_spin.valueChanged.connect(self._update_totals)
        self.is_official_check.stateChanged.connect(self._update_totals)

        # --- FIX: Connect the two separate checkboxes ---
        self.jud_seal_check.stateChanged.connect(self._update_totals)
        self.fa_seal_check.stateChanged.connect(self._update_totals)

        self.remarks_edit.textChanged.connect(self._on_user_remarks_changed)

    def _update_totals(self):
        """
        Calculates all prices using the safe _get_fee helper and constants.
        """
        quantity = self.quantity_spin.value()
        page_count = self.page_count_spin.value()

        # ... (translation price calculation is unchanged)
        translation_price_total = self.service.base_price
        for dyn_name, spinbox in self.dynamic_spinboxes.items():
            dyn_price = next(dp for dp in self.service.dynamic_prices if dp.name == dyn_name)
            translation_price_total += spinbox.value() * dyn_price.price

        # --- FIX: Use the constants to fetch the correct prices ---
        certified_copy_price = page_count * self._get_fee(CERTIFIED_COPY_KEY)
        registration_price = self._get_fee(OFFICIAL_TRANSLATION_KEY) if self.is_official_check.isChecked() else 0

        jud_price = self._get_fee(JUDICIARY_SEAL_KEY) if self.jud_seal_check.isChecked() else 0
        fa_price = self._get_fee(FOREIGN_AFFAIRS_SEAL_KEY) if self.fa_seal_check.isChecked() else 0
        jud_seal_cost = jud_price * quantity
        fa_seal_cost = fa_price * page_count
        total_seals_cost = jud_seal_cost + fa_seal_cost

        extra_copy_price = self.extra_copies_spin.value() * self._get_fee(ADDITIONAL_ISSUES_KEY)

        # Store calculated component prices
        self.calculated_prices['translation_price'] = translation_price_total * quantity
        self.calculated_prices[CERTIFIED_COPY_KEY] = certified_copy_price * quantity
        self.calculated_prices[OFFICIAL_TRANSLATION_KEY] = registration_price * quantity
        self.calculated_prices[JUDICIARY_SEAL_KEY] = jud_seal_cost  # Store individual seal cost
        self.calculated_prices[FOREIGN_AFFAIRS_SEAL_KEY] = fa_seal_cost  # Store individual seal cost
        self.calculated_prices[SEALS_TOTAL_KEY] = total_seals_cost  # Store the combined total for UI
        self.calculated_prices[ADDITIONAL_ISSUES_KEY] = extra_copy_price

        # Grand Total
        grand_total = (self.calculated_prices['translation_price'] +
                       self.calculated_prices[CERTIFIED_COPY_KEY] +
                       self.calculated_prices[OFFICIAL_TRANSLATION_KEY] +
                       total_seals_cost +  # Use the combined total here
                       extra_copy_price)
        self.calculated_prices['total_price'] = grand_total

        # Update the UI from the calculated values
        for key, price_display_label in self.price_displays.items():
            price = self.calculated_prices.get(key, 0)
            price_display_label.setText(f"{to_persian_number(f"{price:,}")} تومان")

    def _generate_auto_remarks(self) -> str:
        """Helper to generate the automatic part of the remarks string."""
        auto_remarks = []
        for name, spinbox in self.dynamic_spinboxes.items():
            if spinbox.value() > 0:
                clean_name = name.replace("تعداد", "").strip()
                if clean_name.startswith("هر"):
                    clean_name = clean_name.replace("هر", "").strip()
                auto_remarks.append(f"{spinbox.textFromValue(spinbox.value())} {clean_name}")

        extra_copies = self.extra_copies_spin.value()
        if extra_copies > 0:
            auto_remarks.append(f"{self.extra_copies_spin.textFromValue(extra_copies)} نسخه اضافی")

        return " و ".join(auto_remarks)

    def _update_remarks_display(self):
        """Generates and displays the full remarks string in the QTextEdit."""
        # This flag prevents the _on_user_remarks_changed method from firing
        # when we are setting the text programmatically.
        self._is_programmatically_updating_remarks = True

        auto_str = self._generate_auto_remarks()

        final_text = auto_str
        if auto_str and self._user_manual_remarks:
            final_text = f"{auto_str} ({self._user_manual_remarks})"
        elif not auto_str and self._user_manual_remarks:
            final_text = self._user_manual_remarks

        self.remarks_edit.setText(final_text)

        # Release the lock
        self._is_programmatically_updating_remarks = False

    def _on_user_remarks_changed(self):
        """
        This slot captures only the user's manual typing by parsing the
        full text and extracting the part that isn't auto-generated.
        """
        # If the program is updating the text, do nothing.
        if self._is_programmatically_updating_remarks:
            return

        full_text = self.remarks_edit.toPlainText()
        auto_str = self._generate_auto_remarks()

        # Logic to extract only the user's part
        if full_text.startswith(auto_str):
            user_part = full_text[len(auto_str):].strip()
            # Check if it's wrapped in parentheses
            if user_part.startswith('(') and user_part.endswith(')'):
                self._user_manual_remarks = user_part[1:-1]
            else:
                self._user_manual_remarks = user_part
        else:
            self._user_manual_remarks = full_text

    def _validate_inputs(self) -> bool:
        """Performs validation on crucial fields before accepting."""
        # --- FIX: Validate page count ---
        if self.page_count_spin.value() < 1:
            self.page_count_spin.show_error("تعداد صفحات نمی‌تواند کمتر از ۱ باشد.")
            return False
        else:
            self.page_count_spin.clear_error()

        if self.quantity_spin.value() < 1:
            self.quantity_spin.show_error("تعداد نسخه اصلی نمی‌تواند کمتر از ۱ باشد.")
            return False
        else:
            self.quantity_spin.clear_error()

        return True

    def accept(self):
        """
        Constructs the final InvoiceItem object using the robust, pre-calculated prices.
        """
        if not self._validate_inputs():
            return  # Stop the accept process if validation fails

        # 1. Generate remarks for dynamic quantities
        final_remarks = self.remarks_edit.toPlainText().strip()

        # 2. Extra copies
        extra_copies = self.extra_copies_spin.value()

        # Ensure calculations are up-to-date
        self._update_totals()

        dynamic_quantities = {name: spinbox.value() for name, spinbox in self.dynamic_spinboxes.items()}
        main_quantity = self.quantity_spin.value()
        total_quantity = main_quantity + extra_copies

        self.result_item = InvoiceItem(
            service=self.service,

            quantity=total_quantity,
            page_count=self.page_count_spin.value(),
            extra_copies=extra_copies,
            is_official=self.is_official_check.isChecked(),
            has_judiciary_seal=self.jud_seal_check.isChecked(),
            has_foreign_affairs_seal=self.fa_seal_check.isChecked(),
            dynamic_quantities=dynamic_quantities,
            remarks=final_remarks,  # Use the new structured remarks

            # Pre-calculated Prices
            translation_price=self.calculated_prices.get('translation_price', 0),
            certified_copy_price=self.calculated_prices.get(CERTIFIED_COPY_KEY, 0),
            registration_price=self.calculated_prices.get(OFFICIAL_TRANSLATION_KEY, 0),
            judiciary_seal_price=self.calculated_prices.get(JUDICIARY_SEAL_KEY, 0),
            foreign_affairs_seal_price=self.calculated_prices.get(FOREIGN_AFFAIRS_SEAL_KEY, 0),
            extra_copy_price=self.calculated_prices.get(ADDITIONAL_ISSUES_KEY, 0),
            total_price=self.calculated_prices.get('total_price', 0)
        )

        super().accept()

    @staticmethod
    def _style_info_label(label: QLabel):
        """Apply styling to info display labels."""
        label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    background-color: #f8f9fa;
                    color: #495057;
                    min-width: 150px;
                }
            """)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    @staticmethod
    def _style_cost_label(label: QLabel):
        """Apply styling to cost display labels."""
        label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    background-color: #e9ecef;
                    color: #212529;
                    font-weight: bold;
                    font-size: 11pt;
                    min-width: 150px;
                }
            """)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)