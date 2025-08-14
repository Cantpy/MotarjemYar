# controller.py
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer, Companion
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_logic import CustomerLogic
from typing import List, Optional, Dict


class CustomerController:
    def __init__(self):
        self.logic = CustomerLogic()

    def save_customer(self, customer_data: dict):
        """Constructs a Customer object and passes it to the logic layer."""
        # The view will handle the int conversion and exceptions
        customer = Customer(
            national_id=customer_data.get('national_id', ""),
            name=customer_data.get('name', ''),
            phone=customer_data.get('phone', ''),
            telegram_id=customer_data.get('telegram_id'),
            email=customer_data.get('email'),
            address=customer_data.get('address'),
            passport_image=customer_data.get('passport_image'),
            companions=[Companion(**c) for c in customer_data.get('companions', [])]
        )
        self.logic.save_customer(customer)

    def get_all_customer_info_for_completer(self) -> List[Dict]:
        """Fetches customer data needed for the completer."""
        return self.logic.get_all_customer_info_for_completer()

    def get_customer_details(self, national_id: int) -> Optional[Customer]:
        """Fetches full details for a specific customer by integer ID."""
        return self.logic.get_customer(national_id)
