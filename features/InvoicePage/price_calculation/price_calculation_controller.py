from typing import Optional
from PySide6.QtCore import QObject, Signal
from features.InvoicePage.price_calculation.price_calculation_view import PriceDialogView
from features.InvoicePage.price_calculation.price_calculation_models import (PriceDialogState, PriceDialogResult,
                                                                             DynamicPriceConfig, DynamicPriceMode,
                                                                             PriceDisplayData)
from features.InvoicePage.document_selection.document_selection_logic import DocumentLogic, PriceCalculationLogic
from features.InvoicePage.document_selection.document_selection_models import Service, PriceDialogData


class PriceDialogController(QObject):
    """Controller for price dialog"""

    # Signals
    dialog_accepted = Signal(object)
    dialog_rejected = Signal()

    def __init__(self, document_logic: DocumentLogic, price_logic: PriceCalculationLogic, parent=None):
        super().__init__(parent)
        self.document_logic = document_logic
        self.price_logic = price_logic
        self.view: Optional[PriceDialogView] = None
        self.state = PriceDialogState()
        self.current_service: Optional[Service] = None

    def show_dialog(self, document_name: str, parent_widget=None) -> PriceDialogResult:
        """Show the price dialog for a document"""
        # Initialize state
        self.state.reset()
        self.state.document_name = document_name

        # Get service details
        self.current_service = self.document_logic.get_service_details(document_name)

        # Create and setup view
        self.view = PriceDialogView(parent_widget, document_name)
        self._connect_view_signals()

        # Configure dynamic pricing
        self._configure_dynamic_pricing()

        # Initial price calculation
        self._update_all_prices()

        # Show dialog
        result = self.view.exec()

        if result == PriceDialogView.Accepted:
            return self._create_accepted_result()
        else:
            return PriceDialogResult(accepted=False)

    def _connect_view_signals(self):
        """Connect view signals to controller methods"""
        if not self.view:
            return

        # Value change signals
        self.view.document_count_changed.connect(self._on_document_count_changed)
        self.view.page_count_changed.connect(self._on_page_count_changed)
        self.view.additional_issues_changed.connect(self._on_additional_issues_changed)
        self.view.dynamic_price_1_changed.connect(self._on_dynamic_price_1_changed)
        self.view.dynamic_price_2_changed.connect(self._on_dynamic_price_2_changed)

        # Checkbox signals
        self.view.official_toggled.connect(self._on_official_toggled)
        self.view.unofficial_toggled.connect(self._on_unofficial_toggled)
        self.view.judiciary_toggled.connect(self._on_judiciary_toggled)
        self.view.foreign_affairs_toggled.connect(self._on_foreign_affairs_toggled)

        # Button signals
        self.view.accept_clicked.connect(self._on_accept_clicked)
        self.view.cancel_clicked.connect(self._on_cancel_clicked)

    def _configure_dynamic_pricing(self):
        """Configure dynamic pricing UI based on service"""
        if not self.view or not self.current_service:
            return

        config = DynamicPriceConfig(mode=DynamicPriceMode.NONE)

        if self.current_service:
            label1, label2 = self.price_logic.get_dynamic_price_labels(self.current_service)

            if label1 and label2:
                config = DynamicPriceConfig(
                    mode=DynamicPriceMode.DOUBLE,
                    label1=label1,
                    label2=label2
                )
            elif label1 or label2:
                config = DynamicPriceConfig(
                    mode=DynamicPriceMode.SINGLE,
                    label1=label1 or label2
                )

        self.view.configure_dynamic_pricing(config)

    def _update_all_prices(self):
        """Update all price displays"""
        if not self.view:
            return

        # Update state from view
        self._sync_state_from_view()

        # Calculate prices
        data = self.state.get_dialog_data()
        calculation, remarks = self.price_logic.calculate_price(data, self.current_service)

        # Update display
        display_data = PriceDisplayData(
            translation_price=self.price_logic.format_price_display(
                calculation.base_price + calculation.dynamic_price_1_total + calculation.dynamic_price_2_total
            ),
            page_price=self.price_logic.format_price_display(calculation.page_price),
            office_price=self.price_logic.format_price_display(calculation.office_price),
            judiciary_price=self.price_logic.format_price_display(calculation.judiciary_price),
            additional_price=self.price_logic.format_price_display(calculation.additional_issue_price),
            total_price=self.price_logic.format_price_display(calculation.total_price)
        )

        self.view.update_price_display(display_data)

    def _sync_state_from_view(self):
        """Synchronize state with view values"""
        if not self.view:
            return

        self.state.document_count = self.view.get_document_count()
        self.state.page_count = self.view.get_page_count()
        self.state.additional_issues = self.view.get_additional_issues()
        self.state.is_official = self.view.is_official()
        self.state.judiciary_seal = self.view.has_judiciary_seal()
        self.state.foreign_affairs_seal = self.view.has_foreign_affairs_seal()
        self.state.dynamic_price_1_count = self.view.get_dynamic_price_1_count()
        self.state.dynamic_price_2_count = self.view.get_dynamic_price_2_count()

    def _create_accepted_result(self) -> PriceDialogResult:
        """Create result for accepted dialog"""
        # Validate inputs
        validation = self.state.validate_inputs()
        if not validation.is_valid:
            return PriceDialogResult(
                accepted=False,
                error_message=validation.error_message
            )

        # Calculate final price and remarks
        data = self.state.get_dialog_data()
        calculation, remarks = self.price_logic.calculate_price(data, self.current_service)

        # Create document item
        document_item = data.to_document_item(calculation.total_price, remarks)

        return PriceDialogResult(
            accepted=True,
            document_item=document_item
        )

    # Event handlers
    def _on_document_count_changed(self, value: int):
        """Handle document count change"""
        if value == 0:
            self.view.show_validation_error("تعداد اسناد نمی‌تواند ۰ باشد")
            self.view.set_document_count(1)
            return

        self.state.document_count = value
        self._update_all_prices()

    def _on_page_count_changed(self, value: int):
        """Handle page count change"""
        if value == 0:
            self.view.show_validation_error("تعداد صفحات سند نمی‌تواند ۰ باشد")
            self.view.set_page_count(1)
            return

        self.state.page_count = value
        self._update_all_prices()

    def _on_additional_issues_changed(self, value: int):
        """Handle additional issues change"""
        self.state.additional_issues = value
        self._update_all_prices()

    def _on_dynamic_price_1_changed(self, value: int):
        """Handle dynamic price 1 change"""
        self.state.dynamic_price_1_count = value
        self._update_all_prices()

    def _on_dynamic_price_2_changed(self, value: int):
        """Handle dynamic price 2 change"""
        self.state.dynamic_price_2_count = value
        self._update_all_prices()

    def _on_official_toggled(self, checked: bool):
        """Handle official checkbox toggle"""
        if checked:
            self.state.is_official = True
        self._update_all_prices()

    def _on_unofficial_toggled(self, checked: bool):
        """Handle unofficial checkbox toggle"""
        if checked:
            self.state.is_official = False
        self._update_all_prices()

    def _on_judiciary_toggled(self, checked: bool):
        """Handle judiciary checkbox toggle"""
        self.state.judiciary_seal = checked
        self._update_all_prices()

    def _on_foreign_affairs_toggled(self, checked: bool):
        """Handle foreign affairs checkbox toggle"""
        self.state.foreign_affairs_seal = checked
        self._update_all_prices()

    def _on_accept_clicked(self):
        """Handle accept button click"""
        if not self.view:
            return

        # Validate inputs
        self._sync_state_from_view()
        validation = self.state.validate_inputs()

        if not validation.is_valid:
            self.view.show_validation_error(validation.error_message)
            return

        # Validate document exists
        if not self.document_logic.validate_document_name(self.state.document_name):
            self.view.show_validation_error("نام سند معتبر نیست")
            return

        self.view.accept()

    def _on_cancel_clicked(self):
        """Handle cancel button click"""
        if self.view:
            self.view.reject()
