# document_selection/view.py
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QDialog,
    QVBoxLayout, QHBoxLayout, QGroupBox, QHeaderView, QCompleter, QSpinBox, QCheckBox
)
from PySide6.QtCore import Signal, QStringListModel, Qt, QSize
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_controller import DocumentSelectionController
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import (Service, InvoiceItem,
                                                                                        DynamicPrice, FixedPrice)
from features.Invoice_Page_GAS.document_selection_GAS.price_calculation_dialog import CalculationDialog


class DocumentSelectionWidget(QWidget):
    # --- The communication signal ---
    invoice_items_changed = Signal(list)

    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self._controller = DocumentSelectionController()
        self._services_map = {s.name: s for s in self._controller.get_all_services()}
        self._calculation_fees = self._controller.get_calculation_fees()
        self._current_invoice_items = []

        main_layout = QVBoxLayout(self)
        self._setup_ui(main_layout)
        self._populate_completer()

    def _setup_ui(self, main_layout):
        service_input_group = QGroupBox("افزودن خدمات به فاکتور")
        input_layout = QHBoxLayout(service_input_group)
        self.service_edit = QLineEdit()
        self.service_edit.setPlaceholderText("نام سند یا خدمات را جستجو کنید...")
        add_button = QPushButton("افزودن به لیست")
        add_button.setObjectName("PrimaryButton")
        input_layout.addWidget(QLabel("انتخاب سند:"))
        input_layout.addWidget(self.service_edit)
        input_layout.addWidget(add_button)

        invoice_table_group = QGroupBox("لیست خدمات انتخاب شده")
        table_layout = QVBoxLayout(invoice_table_group)
        self.table = QTableWidget()
        # NEW: Read-only table with updated columns
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "شرح خدمات", "تعداد", "تعداد صفحات", "مهر دادگستری", "مهر امورخارجه",
            "قیمت کل", "توضیحات", ""
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        table_layout.addWidget(self.table)

        buttons_layout = QHBoxLayout()
        clear_button = QPushButton("پاک کردن کل لیست")
        delete_button = QPushButton("حذف آیتم انتخاب شده")
        delete_button.setObjectName("RemoveButton")
        buttons_layout.addStretch()
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(clear_button)

        main_layout.addWidget(service_input_group)
        main_layout.addWidget(invoice_table_group)
        main_layout.addLayout(buttons_layout)

        add_button.clicked.connect(self._add_service_item)
        clear_button.clicked.connect(self._clear_all)
        delete_button.clicked.connect(self._delete_table_row)

    def _populate_completer(self):
        completer = QCompleter(list(self._services_map.keys()), self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.service_edit.setCompleter(completer)

    def _create_option_widget(self, service: Service, option_name: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checkbox = QCheckBox()

        option_found = False
        for dyn_price in service.dynamic_prices:
            if dyn_price.name == option_name:
                checkbox.setProperty("option_price", dyn_price.price)
                option_found = True
                break

        checkbox.setEnabled(option_found)
        layout.addWidget(checkbox)
        return container

    # def _on_item_changed(self):
    #     invoice_items = []
    #     total_invoice_price = 0
    #     for row in range(self.table.rowCount()):
    #         service: Service = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
    #         quantity = self.table.cellWidget(row, 2).value()
    #
    #         row_total = service.base_price
    #         selected_options = []
    #
    #         for col in [3, 4]:  # Judiciary and Foreign Affairs columns
    #             checkbox = self.table.cellWidget(row, col).findChild(QCheckBox)
    #             if checkbox.isChecked():
    #                 price = checkbox.property("option_price")
    #                 option_name = self.table.horizontalHeaderItem(col).text()
    #                 row_total += price
    #                 selected_options.append(DynamicPrice(name=option_name, price=price))
    #
    #         row_total *= quantity
    #         self.table.item(row, 5).setText(f"{row_total:,}")
    #
    #         notes_item = self.table.item(row, 6)
    #         item = InvoiceItem(
    #             service_name=service.name,
    #             service_type=service.type,
    #             quantity=quantity,
    #             base_price=service.base_price,
    #             selected_options=selected_options,
    #             notes=notes_item.text() if notes_item else "",
    #             total_price=row_total
    #         )
    #         invoice_items.append(item)
    #         total_invoice_price += row_total
    #
    #     self.invoice_items_changed.emit(invoice_items)

    def _add_service_item(self):
        service = self._services_map.get(self.service_edit.text())
        if not service: return

        # --- OPEN THE DIALOG ---
        dialog = CalculationDialog(service, self._calculation_fees, self)
        if dialog.exec() == QDialog.Accepted:
            new_item = dialog.result_item
            self._current_invoice_items.append(new_item)
            self._display_item_in_table(new_item)
            self.invoice_items_changed.emit(self._current_invoice_items)
            self.service_edit.clear()

    def _display_item_in_table(self, item: InvoiceItem):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(item.service.name))
        self.table.setItem(row, 1, QTableWidgetItem(str(item.quantity)))
        self.table.setItem(row, 2, QTableWidgetItem(str(item.page_count)))

        # Display checkmarks or dashes for seals
        jud_seal_item = QTableWidgetItem("✔" if item.has_judiciary_seal else "-")
        jud_seal_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, jud_seal_item)

        fa_seal_item = QTableWidgetItem("✔" if item.has_foreign_affairs_seal else "-")
        fa_seal_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, fa_seal_item)

        self.table.setItem(row, 5, QTableWidgetItem(f"{item.total_price:,}"))
        self.table.setItem(row, 6, QTableWidgetItem(item.remarks))

        # We store the full object on the delete button for easy removal
        delete_button = QPushButton("حذف")
        delete_button.setObjectName("RemoveButton")
        delete_button.setProperty("invoice_item", item)
        delete_button.clicked.connect(self._delete_table_row)
        self.table.setCellWidget(row, 7, delete_button)

    def _delete_table_row(self):
        button = self.sender()
        item_to_remove = button.property("invoice_item")

        # Find the row corresponding to this button
        for row in range(self.table.rowCount()):
            cell_widget = self.table.cellWidget(row, 7)
            if cell_widget == button:
                self.table.removeRow(row)
                self._current_invoice_items.remove(item_to_remove)
                self.invoice_items_changed.emit(self._current_invoice_items)
                break

    def _clear_all(self):
        self.table.setRowCount(0)
        self._current_invoice_items.clear()
        self.invoice_items_changed.emit(self._current_invoice_items)
