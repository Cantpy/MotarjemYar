# logic.py
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_repo import CustomerRepository

from typing import List, Optional

from shared.utils.validation_utils import validate_national_id, validate_email, validate_phone_number


class CustomerLogic:
    def __init__(self):
        self.repository = CustomerRepository()

    def save_customer(self, customer: Customer) -> None:
        """Performs validation and saves a customer."""
        # --- Main Customer Validation ---
        if not all([customer.national_id, customer.name, customer.phone]):
            raise ValueError("فیلدهای کدملی، نام و نام و خانوادگی، و شماره تماس باید پر شوند.")

        if not validate_email(str(customer.national_id)):
            raise ValueError(f"کد ملی مشتری نامعتبر است.\n{customer.national_id}")

        if not validate_phone_number(customer.phone):
            raise ValueError(f"شماره تماس مشتری نامعتیر است.\n {customer.phone}")

        if not validate_email(customer.email):
            raise ValueError(f"ایمیل مشتری نامعتیر است.\n {customer.phone}")

        # --- Companion Validation ---
        for companion in customer.companions:
            if not validate_national_id(str(companion.national_id)):
                raise ValueError(f"کد ملی همراه مشتری نامعتبر است.\n {companion.national_id}")

        self.repository.add_customer(customer)

    def get_customer(self, national_id: int) -> Optional[Customer]:
        """Retrieves a customer by their integer national ID."""
        return self.repository.get_customer(national_id)

    def get_all_customer_info_for_completer(self) -> List[dict]:
        """Gets info (name, national_id) for the QCompleter autofill."""
        customers = self.repository.get_all_customers()
        return [{"name": c.name, "national_id": c.national_id} for c in customers]

