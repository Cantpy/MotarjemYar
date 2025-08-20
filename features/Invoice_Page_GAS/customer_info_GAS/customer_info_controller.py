# controller.py
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_logic import CustomerLogic, CustomerExistsError
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_view import CustomerInfoWidget
from features.Invoice_Page_GAS.invoice_page_state_manager import WorkflowStateManager
from typing import List, Optional, Dict


class CustomerInfoController:
    def __init__(self, state_manager: WorkflowStateManager):
        self._logic = CustomerLogic()
        self._view = CustomerInfoWidget()
        self.state_manager = state_manager

        # --- This now calls the correct, unified method ---
        completer_data = self._logic.get_all_customer_and_companion_info()
        self._view.populate_completer(completer_data)

        # --- Connect the layers ---
        self._connect_signals()

    def _connect_signals(self):
        self._view.populate_completer(self._logic.get_all_customer_info_for_completer())
        self._view.save_requested.connect(self._on_save_requested)
        self._view.fetch_customer_details_requested.connect(self._logic.get_customer_details)
        self._view.fetch_customer_details_requested.connect(self._on_fetch_details_requested)

    def _on_fetch_details_requested(self, national_id: str):
        """
        Handles the request to autofill the form. The NID will always be the
        correct main customer NID, thanks to the logic layer.
        """
        customer = self._logic.get_customer_details(national_id)
        if customer:
            self._view.display_customer_details(customer)

    def check_status(self, raw_data: dict):
        """Exposes the logic's status check method."""
        return self._logic.check_customer_status(raw_data)

    def save_current_customer(self, raw_data: dict):
        """A public method for the MainWindow to call to force a save."""
        self._on_save_requested(raw_data)

    def _on_save_requested(self, raw_data: dict):
        try:
            saved_customer = self._logic.save_customer(raw_data)
            self.state_manager.set_customer(saved_customer)
            self._view.show_save_success("اطلاعات مشتری با موفقیت ذخیره شد!")

            # --- Refresh the completer with new data ---
            new_completer_data = self._logic.get_all_customer_and_companion_info()
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
