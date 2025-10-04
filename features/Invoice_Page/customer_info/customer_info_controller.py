# features/Invoice_Page/customer_info/customer_info_controller.py

from features.Invoice_Page.customer_info.customer_info_logic import CustomerLogic, CustomerExistsError, ValidationError
from features.Invoice_Page.customer_info.customer_info_view import CustomerInfoWidget
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager


class CustomerInfoController:
    """
    The Controller in MVC.
    - Connects the View's signals to its slots.
    - Calls the Model (Logic) to perform business operations.
    - Updates the View based on the Model's responses.
    """
    def __init__(self, logic: CustomerLogic, view: CustomerInfoWidget, state_manager: WorkflowStateManager):
        self._logic = logic
        self._view = view
        self._state_manager = state_manager

        self._connect_signals()
        self._populate_all_completers()

    def get_view(self) -> CustomerInfoWidget:
        """Exposes the view widget for integration into a larger UI."""
        return self._view

    def _connect_signals(self):
        """Connects signals from the view to controller slots."""
        self._view.save_requested.connect(self._on_save_requested)
        self._view.fetch_customer_details_requested.connect(self._on_fetch_details_requested)

    def _populate_all_completers(self):
        """
        Fetches all completer data from logic and populates the view.
        """
        completer_data = self._logic.get_all_data_for_completers()
        self._view.populate_all_completers(completer_data)

    def _on_fetch_details_requested(self, national_id: str):
        """Handles the request to fetch and display customer details."""
        print(f"requesting details to fetch details for customer with national id: {national_id}")
        customer_dto = self._logic.get_customer_details(national_id)
        if customer_dto:
            self._view.display_customer_details(customer_dto)
            self._view.display_validation_results({})

    def _on_save_requested(self, raw_data: dict):
        """Orchestrates the validation and saving process."""
        try:
            saved_customer = self._logic.save_customer(raw_data)
            self._state_manager.set_customer(saved_customer)
            self._view.show_save_success("اطلاعات مشتری با موفقیت ذخیره شد!")
            self._view.clear_form()
            self._populate_all_completers()

        except ValidationError as e:
            self._view.display_validation_results(e.errors)
            self._view.show_error("لطفا خطاهای مشخص شده را برطرف کنید.")

        except CustomerExistsError as e:
            def on_confirm_update():
                updated_customer = self._logic.update_customer(e.customer)
                self._state_manager.set_customer(updated_customer)
                self._view.show_save_success("اطلاعات مشتری با موفقیت بروزرسانی شد!")
                self._populate_all_completers()

            self._view.show_edit_question(
                message="مشتری با این کد ملی وجود دارد. آیا مایل به بروزرسانی اطلاعات هستید؟",
                yes_callback=on_confirm_update
            )

        except Exception as e:
            self._view.show_error(f"یک خطای پیشبینی نشده رخ داد: {e}")

    def reset_view(self):
        """Clears all fields in the invoice details view."""
        self._view.clear_form()
