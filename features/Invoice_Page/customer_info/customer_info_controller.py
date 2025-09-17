# controller.py
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.customer_info.customer_info_logic import CustomerLogic, CustomerExistsError, ValidationError
from features.Invoice_Page.customer_info.customer_info_view import CustomerInfoWidget
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from typing import List, Optional, Dict


class CustomerInfoController:
    def __init__(self, view: CustomerInfoWidget, logic: CustomerLogic, state_manager: WorkflowStateManager):
        self._logic = logic
        self._view = view
        self._state_manager = state_manager

        # Initial setup
        self._populate_view_completer()
        self._connect_signals()

    def get_view(self) -> CustomerInfoWidget:
        """
        Exposes the _view widget for integration into a larger UI.
        """
        return self._view

    def _connect_signals(self):
        """Connects signals from the _view to controller slots."""
        self._view.save_requested.connect(self._on_save_requested)
        self._view.fetch_customer_details_requested.connect(self._on_fetch_details_requested)

    def _populate_view_completer(self):
        """Fetches completer data from _logic and populates the _view."""
        completer_data = self._logic.get_all_customer_and_companion_info()
        self._view.populate_completer(completer_data)

    def _on_fetch_details_requested(self, national_id: str):
        """
        Handles the request to fetch and display customer details.
        This is the single point of handling for this user action.
        """
        customer = self._logic.get_customer_details(national_id)
        if customer:
            self._view.display_customer_details(customer)
            # Clear any previous validation errors when loading a new customer
            self._view.display_validation_results({})

    def check_status(self, raw_data: dict):
        """Exposes the _logic's status check method."""
        return self._logic.check_customer_status(raw_data)

    def save_current_customer(self, raw_data: dict):
        """A public method for the MainWindow to call to force a save."""
        self._on_save_requested(raw_data)

    def _on_save_requested(self, raw_data: dict):
        """
        Handles the request to save the customer data from the form.
        This method orchestrates the validation and saving process.
        """
        try:
            # The _logic layer now handles all validation internally.
            saved_customer = self._logic.save_customer(raw_data)
            self._state_manager.set_customer(saved_customer)
            self._view.clear_form() # Clear form on success
            self._view.show_save_success("اطلاعات مشتری با موفقیت ذخیره شد!")
            self._populate_view_completer() # Refresh completer with the new data
            self._view.display_validation_results({}) # Clear all error highlights

        except ValidationError as e:
            # If validation fails, show specific errors on the _view.
            self._view.display_validation_results(e.errors)
            self._view.show_error("لطفا خطاهای مشخص شده را برطرف کنید.")

        except CustomerExistsError as e:
            # If customer exists, ask the user if they want to update.
            def on_confirm_update():
                # The _logic layer will handle the update.
                updated_customer = self._logic.update_customer(e.customer)
                self._state_manager.set_customer(updated_customer)
                self._view.show_save_success("اطلاعات مشتری با موفقیت بروزرسانی شد!")
                self._populate_view_completer()
                self._view.display_validation_results({}) # Clear errors after update

            self._view.show_edit_question(
                message="مشتری با این کد ملی وجود دارد. آیا مایل به بروزرسانی اطلاعات هستید؟",
                func=on_confirm_update
            )

        except Exception as e:
            # Catch any other unexpected errors from the _logic layer.
            self._view.show_error(f"یک خطای پیشبینی نشده رخ داد: {e}")

    def get_all_customer_info_for_completer(self) -> List[Dict]:
        """Fetches customer data needed for the completer."""
        return self._logic.get_all_customer_info_for_completer()

    def get_customer_details(self, national_id: str) -> Optional[Customer]:
        """Fetches full details for a specific customer by integer ID."""
        return self._logic.get_customer_details(national_id)
