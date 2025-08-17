# controller.py
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_logic import CustomerLogic, CustomerExistsError
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_view import CustomerInfoWidget
from features.Invoice_Page_GAS.workflow_manager.invoice_page_state_manager import WorkflowStateManager
from typing import List, Optional, Dict


class CustomerController:
    def __init__(self, state_manager: WorkflowStateManager):
        self._logic = CustomerLogic()
        self._view = CustomerInfoWidget()
        self.state_manager = state_manager

        # --- Initial Setup ---
        completer_data = self._logic.get_all_customer_info_for_completer()
        self._view.populate_completer(completer_data)

        # --- Connect the layers ---
        self.connect_signals()

    def connect_signals(self):
        self._view.populate_completer(self._logic.get_all_customer_info_for_completer())
        self._view.save_requested.connect(self._on_save_requested)
        self._view.fetch_customer_details_requested.connect(self._logic.get_customer_details)

    def _on_save_requested(self, raw_data: dict):
        try:
            # Tell the logic to process the data
            saved_customer = self._logic.save_customer(raw_data)

            # --- FIX #2: Update the central state manager ---
            self.state_manager.set_customer(saved_customer)

            # Tell the view to show a success message
            self._view.show_save_success("اطلاعات مشتری با موفقیت ذخیره شد!")
            self._view.populate_completer(self._logic.get_all_customer_info_for_completer())

            # Refresh the completer with the new data
            new_completer_data = self._logic.get_all_customer_info_for_completer()
            self._view.populate_completer(new_completer_data)

        except CustomerExistsError as e:
            # --- FIX #3: Handle the override case ---
            def rewrite_customer():
                updated_customer = e.customer
                self._logic.update_customer(updated_customer)
                self.state_manager.set_customer(updated_customer)
                self._view.show_save_success("اطلاعات مشتری با موفقیت بروزرسانی شد!")
                self._view.populate_completer(self._logic.get_all_customer_info_for_completer())

            self._view.show_edit_question(
                message=f"{e}\nمشتری با مشخصات وارد شده وجو دارد. آیا مایل به بازنویسی اطلاعات مشتری هستید؟",
                func=rewrite_customer)

        except ValueError as e:
            # On failure, tell the view to show the error
            self._view.show_error(str(e))

    def get_widget(self) -> CustomerInfoWidget:
        return self._view

    def get_all_customer_info_for_completer(self) -> List[Dict]:
        """Fetches customer data needed for the completer."""
        return self._logic.get_all_customer_info_for_completer()

    def get_customer_details(self, national_id: str) -> Optional[Customer]:
        """Fetches full details for a specific customer by integer ID."""
        return self._logic.get_customer_details(national_id)
