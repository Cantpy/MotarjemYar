# document_selection/price_calculation_dialog.py

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QGraphicsDropShadowEffect, QHBoxLayout,
    QCheckBox, QTextEdit, QFrame
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from features.Invoice_Page.document_selection.document_selection_models import Service, InvoiceItem, FixedPrice
from features.Invoice_Page.document_selection.document_selection_qss_styles import DIALOG_STYLESHEET
from typing import Dict, List
from shared import to_persian_number
from shared.widgets.persian_tools import PersianSpinBox

CERTIFIED_COPY_KEY = "کپی برابر اصل"
OFFICIAL_TRANSLATION_KEY = "ثبت در سامانه"
JUDICIARY_SEAL_KEY = "مهر دادگستری"
FOREIGN_AFFAIRS_SEAL_KEY = "مهر امور خارجه"
ADDITIONAL_ISSUES_KEY = "نسخه اضافی"
SEALS_TOTAL_KEY = "هزینه تاییدات"


class CalculationDialog(QDialog):
    def __init__(self, service: Service, fees: List[FixedPrice], item_to_edit: InvoiceItem = None, parent=None):
        super().__init__(parent)
        self.setObjectName("CalculationDialog")

        self.setWindowTitle(f"محاسبه قیمت: {service.name}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(700)
        self.setStyleSheet(DIALOG_STYLESHEET)
        self.setFont(QFont("IranSANS", 11))

        self.service = service
        self.fees = fees
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
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("تایید")
        ok_button.setObjectName("PrimaryButton")
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("انصراف")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._connect_signals()
        self._update_totals()
        if item_to_edit:
            self._prepopulate_fields(item_to_edit)

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
        self.page_count_spin.setValue(self.service.default_page_count)

        self.extra_copies_spin = PersianSpinBox(suffix="نسخه")

        self.is_official_check = QCheckBox("ترجمه رسمی است")
        self.is_official_check.setChecked(True)
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

        # --- DYNAMIC UI CREATION ---
        # Start with the non-default fields
        fields_to_display = {
            'translation_price': "قیمت ترجمه",
            SEALS_TOTAL_KEY: "هزینه تاییدات"  # This is a calculated total, not a direct fee
        }

        # Now, add fields dynamically from the database defaults
        for fee in self.fees:
            # The key will be the fee's name (e.g., "کپی برابر اصل")
            # The value will be the display name (e.g., "کپی برابر اصل")
            cleaned_label = fee.name.split('(')[0].strip()
            fields_to_display[fee.name] = cleaned_label

        # Add the final total field at the end
        fields_to_display['total_price'] = "هزینه کل آیتم"
        # --- END DYNAMIC UI CREATION ---

        i = 0
        for key, label_text in fields_to_display.items():
            # Skip creating UI for individual seals as we show a combined total
            if key in [JUDICIARY_SEAL_KEY, FOREIGN_AFFAIRS_SEAL_KEY]:
                continue

            field_label = QLabel(f"{label_text}:")
            price_display_label = QLabel("0")
            self.price_displays[key] = price_display_label  # Use the fee name as the key

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
            translation_price_total += spinbox.value() * dyn_price.unit_price

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
            price_display_label.setText(f"{to_persian_number(f'{price:,}')} تومان")

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

    def _prepopulate_fields(self, item: InvoiceItem):
        """Sets the initial values of all widgets based on an existing item."""
        # Pre-fill dynamic price spinboxes
        for name, spinbox in self.dynamic_spinboxes.items():
            if name in item.dynamic_quantities:
                spinbox.setValue(item.dynamic_quantities[name])

        # Pre-fill option widgets
        self.quantity_spin.setValue(item.quantity - item.extra_copies)  # Show base quantity
        self.page_count_spin.setValue(item.page_count)
        self.extra_copies_spin.setValue(item.extra_copies)
        self.is_official_check.setChecked(item.is_official)
        self.jud_seal_check.setChecked(item.has_judiciary_seal)
        self.fa_seal_check.setChecked(item.has_foreign_affairs_seal)

        # --- FIX: Handle potential None value for remarks ---
        auto_remarks = self._generate_auto_remarks()
        full_remarks = item.remarks or ""  # Coalesce None to an empty string
        user_part = full_remarks

        if full_remarks.startswith(auto_remarks):
            user_part = full_remarks[len(auto_remarks):].strip()
            if user_part.startswith('(') and user_part.endswith(')'):
                user_part = user_part[1:-1]

        # Use _user_manual_remarks to store the extracted part
        self._user_manual_remarks = user_part
        # Then, trigger the display update logic which combines auto and manual parts
        self._update_remarks_display()


    def accept(self):
        """
        Constructs the final PreviewItem object using the robust, pre-calculated prices.
        """
        if not self._validate_inputs():
            return  # Stop the accept process if validation fails

        final_remarks = self.remarks_edit.toPlainText().strip()
        extra_copies = self.extra_copies_spin.value()
        self._update_totals() # Ensure calculations are up-to-date

        dynamic_quantities = {name: spinbox.value() for name, spinbox in self.dynamic_spinboxes.items()}
        main_quantity = self.quantity_spin.value()
        total_quantity = main_quantity + extra_copies

        # Calculate dynamic price details just like in the logic layer
        dynamic_price_details_list = []
        for dyn_name, dyn_quantity in dynamic_quantities.items():
            if dyn_quantity > 0:
                dyn_price_obj = next((dp for dp in self.service.dynamic_prices if dp.name == dyn_name), None)
                if dyn_price_obj:
                    total_amount = dyn_quantity * dyn_price_obj.unit_price
                    dynamic_price_details_list.append((dyn_name, dyn_quantity, total_amount))

        self.result_item = InvoiceItem(
            service=self.service,

            quantity=total_quantity,
            page_count=self.page_count_spin.value(),
            extra_copies=extra_copies,
            is_official=self.is_official_check.isChecked(),
            has_judiciary_seal=self.jud_seal_check.isChecked(),
            has_foreign_affairs_seal=self.fa_seal_check.isChecked(),
            dynamic_quantities=dynamic_quantities,
            remarks=final_remarks,

            dynamic_price_details=dynamic_price_details_list,

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
