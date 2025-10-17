# features/Admin_Panel/admin_reports/advanced_search_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidgetItem,
                               QGridLayout, QLineEdit, QSpinBox, QTableWidget, QHeaderView, QRadioButton,
                               QGroupBox, QCompleter)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from shared.fonts.font_manager import FontManager
from shared import show_warning_message_box
from shared.utils.persian_tools import to_persian_numbers, to_persian_jalali_string
from datetime import date
from shared.widgets.persian_calendar import DataDatePicker
from features.Admin_Panel.admin_reports.admin_reports_qss_styles import ADVANCED_SEARCH_QSS


class AdvancedSearchView(QWidget):
    search_requested = Signal(dict)
    descriptive_search_requested = Signal(str)
    export_table_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AdvancedSearchView")
        self.setFont(FontManager.get_font(size=11))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Descriptive Search Box ---
        desc_groupbox = QGroupBox("جستجوی توصیفی (هوشمند)")
        desc_layout = QHBoxLayout(desc_groupbox)
        self.desc_search_edit = QLineEdit()
        self.desc_search_edit.setPlaceholderText("درخواست خود را به فارسی تایپ کنید... مثال: مشتریان بدهکار امسال /"
                                                 " مشتریان با سند شناسنامه / مشتریان با بیش از 5 مراجعه")
        self.desc_search_btn = QPushButton(icon=qta.icon('fa5s.search'))
        desc_layout.addWidget(self.desc_search_edit)
        desc_layout.addWidget(self.desc_search_btn)
        main_layout.addWidget(desc_groupbox)

        # --- Structured Search ---
        structured_groupbox = QGroupBox("جستجوی ساختاریافته")
        structured_layout = QVBoxLayout(structured_groupbox)
        structured_groupbox.setLayout(structured_layout)
        main_layout.addWidget(structured_groupbox)

        type_layout = QHBoxLayout()
        self.rb_unpaid = QRadioButton("مشتریان با پرداخت معوق")
        self.rb_docs = QRadioButton("مشتریان بر اساس نوع سند")
        self.rb_frequent = QRadioButton("مشتریان پرتکرار")
        self.rb_unpaid.setChecked(True)
        type_layout.addWidget(self.rb_unpaid)
        type_layout.addWidget(self.rb_docs)
        type_layout.addWidget(self.rb_frequent)
        structured_layout.addLayout(type_layout)

        # --- Create container widgets for each set of inputs ---
        self.unpaid_inputs = QWidget()
        unpaid_layout = QGridLayout(self.unpaid_inputs)
        self.start_date_edit = DataDatePicker()
        self.end_date_edit = DataDatePicker()
        unpaid_layout.addWidget(QLabel("از تاریخ:"), 0, 0)
        unpaid_layout.addWidget(self.start_date_edit, 0, 1)
        unpaid_layout.addWidget(QLabel("تا تاریخ:"), 0, 2)
        unpaid_layout.addWidget(self.end_date_edit, 0, 3)
        unpaid_layout.setColumnStretch(4, 1)

        self.docs_inputs = QWidget()
        docs_layout = QGridLayout(self.docs_inputs)
        self.doc_names_edit = QLineEdit()
        self.doc_names_edit.setPlaceholderText("شروع به تایپ کنید (مثال: شناسنامه, کارت ملی)")
        docs_layout.addWidget(QLabel("نام اسناد (با کاما جدا کنید):"), 0, 0)
        docs_layout.addWidget(self.doc_names_edit, 0, 1)

        self.frequent_inputs = QWidget()
        frequent_layout = QGridLayout(self.frequent_inputs)
        self.min_visits_spinbox = QSpinBox()
        self.min_visits_spinbox.setMinimum(2)
        self.min_visits_spinbox.setValue(3)
        self.min_visits_spinbox.setFixedWidth(80)
        frequent_layout.addWidget(QLabel("حداقل تعداد مراجعه:"), 0, 0)
        frequent_layout.addWidget(self.min_visits_spinbox, 0, 1)
        frequent_layout.setColumnStretch(2, 1)

        structured_layout.addWidget(self.unpaid_inputs)
        structured_layout.addWidget(self.docs_inputs)
        structured_layout.addWidget(self.frequent_inputs)

        self.search_btn = QPushButton(" جستجو")
        self.search_btn.setIcon(qta.icon('fa5s.search', color='white'))
        self.search_btn.setStyleSheet("""
            QPushButton { background-color: #0078D7; color: white; padding: 8px 20px; border-radius: 5px; }
            QPushButton:hover { background-color: #005A9E; }
        """)
        structured_layout.addWidget(self.search_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Action Buttons with QSS Object Names ---
        action_layout = QHBoxLayout()
        self.clear_btn = QPushButton(" پاک کردن فرم")
        self.clear_btn.setIcon(qta.icon('fa5s.eraser', color='white'))
        self.clear_btn.setObjectName("clearButton")
        self.export_btn = QPushButton(" خروجی اکسل")
        self.export_btn.setIcon(qta.icon('fa5s.file-excel', color='white'))
        self.export_btn.setObjectName("exportButton")
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.clear_btn)
        action_layout.addWidget(self.export_btn)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        # --- Results Table ---
        self.results_table = QTableWidget()  # ... (setup is the same)
        main_layout.addWidget(self.results_table, 1)

        # --- Connect Signals ---
        self.rb_unpaid.toggled.connect(self._update_input_visibility)
        self.rb_docs.toggled.connect(self._update_input_visibility)
        self.rb_frequent.toggled.connect(self._update_input_visibility)
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.desc_search_btn.clicked.connect(self._on_descriptive_search_clicked)
        self.desc_search_edit.returnPressed.connect(self._on_descriptive_search_clicked)  # Search on Enter
        self.clear_btn.clicked.connect(self.clear_form)
        self.export_btn.clicked.connect(self.export_table_requested)
        self._update_input_visibility()  # Set initial UI state

        self.setStyleSheet(ADVANCED_SEARCH_QSS)

    def _update_input_visibility(self):
        """Hides and shows input fields based on the selected search type."""
        self.unpaid_inputs.setVisible(self.rb_unpaid.isChecked())
        self.docs_inputs.setVisible(self.rb_docs.isChecked())
        self.frequent_inputs.setVisible(self.rb_frequent.isChecked())

    def set_document_completer(self, service_names: list[str]):
        """Sets up the auto-completer for the document names line edit."""
        completer = QCompleter(service_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.doc_names_edit.setCompleter(completer)

    def _update_input_states(self):
        """Enables/disables input fields based on the selected search type."""
        self.start_date_edit.setEnabled(self.rb_unpaid.isChecked())
        self.end_date_edit.setEnabled(self.rb_unpaid.isChecked())
        self.doc_names_edit.setEnabled(self.rb_docs.isChecked())
        self.min_visits_spinbox.setEnabled(self.rb_frequent.isChecked())

    def _on_search_clicked(self):
        """Gathers data from the structured search and emits a signal."""
        criteria = {}
        if self.rb_unpaid.isChecked():
            criteria['type'] = 'unpaid'

            start_date_obj = self.start_date_edit.get_date()
            end_date_obj = self.end_date_edit.get_date()

            # Add validation
            if start_date_obj and end_date_obj:
                # Convert the jdatetime object to a standard Python date for the _logic layer
                criteria['start_date'] = start_date_obj
                criteria['end_date'] = end_date_obj
            else:
                show_warning_message_box(self,
                                         "ورودی نامعتبر",
                                         "لطفا یک بازه زمانی معتبر برای جستجو انتخاب کنید.")
                return
        elif self.rb_docs.isChecked():
            criteria['type'] = 'docs'
            criteria['doc_names'] = [name.strip() for name in self.doc_names_edit.text().split(',') if name.strip()]
        elif self.rb_frequent.isChecked():
            criteria['type'] = 'frequent'
            criteria['min_visits'] = self.min_visits_spinbox.value()

        self.search_requested.emit(criteria)

    def _on_descriptive_search_clicked(self):
        """Emits the raw text from the descriptive search box."""
        query = self.desc_search_edit.text()
        if query:
            self.descriptive_search_requested.emit(query)

    def clear_form(self):
        """Resets all input fields, including the new date widgets."""
        self.desc_search_edit.clear()
        self.rb_unpaid.setChecked(True)

        # --- FIX: Call the clear method on your new widgets ---
        # Assuming your DataDatePicker has a .clear() method
        if hasattr(self.start_date_edit, 'clear'):
            self.start_date_edit.clear()
        if hasattr(self.end_date_edit, 'clear'):
            self.end_date_edit.clear()

        self.doc_names_edit.clear()
        self.min_visits_spinbox.setValue(3)
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.setHorizontalHeaderLabels([])
        self.export_btn.setEnabled(False)

    def display_results(self, data: list, headers: list):
        """
        Populates the results table, localizing dates and numbers for display.
        The underlying data remains in standard format.
        """
        self.results_table.clear()
        self.results_table.setRowCount(len(data))
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)

        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                # --- NEW: Apply localization before displaying ---
                display_text = ""
                if isinstance(col_data, date):
                    # If the data is a date object, format it to a Persian Jalali string
                    display_text = to_persian_jalali_string(col_data)
                else:
                    # For all other data (numbers, strings), convert to Persian numbers
                    display_text = to_persian_numbers(str(col_data))

                self.results_table.setItem(row_idx, col_idx, QTableWidgetItem(display_text))

        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.export_btn.setEnabled(len(data) > 0)
