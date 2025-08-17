# logic.py
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer, Companion
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_repo import CustomerRepository

from typing import List, Optional

from shared.utils.validation_utils import validate_national_id, validate_email, validate_phone_number


class CustomerExistsError(Exception):
    def __init__(self, message, customer_obj):
        super().__init__(message)
        self.customer = customer_obj


class CustomerLogic:
    def __init__(self):
        self._repo = CustomerRepository()
        self._customers_for_completer = []

    def _build_customer_from_data(self, raw_data: dict) -> Customer:
        """Helper to construct a Customer object from raw data."""
        companions = [
            Companion(name=comp['name'], national_id=comp['national_id'])
            for comp in raw_data.get('companions', [])
            if comp.get('name') and comp.get('national_id')
        ]
        customer = Customer(
            national_id=raw_data.get('national_id', ''),
            name=raw_data.get('name', ''),
            phone=raw_data.get('phone', ''),
            telegram_id=raw_data.get('telegram_id', ''),
            email=raw_data.get('email', ''),
            address=raw_data.get('address', ''),
            passport_image=raw_data.get('passport_image', ''),
            companions=companions
        )
        return customer

    def get_all_customer_info_for_completer(self) -> list[dict]:
        """Fetches and caches customer info for the completer."""
        # In a real app, you might refresh this periodically
        if not self._customers_for_completer:
            customers = self._repo.get_all_customers()
            self._customers_for_completer = [
                {"name": c.name, "national_id": c.national_id} for c in customers
            ]
        return self._customers_for_completer

    def save_customer(self, raw_data: dict) -> Customer:
        """Performs validation and saves a customer."""
        nid = raw_data.get('national_id')

        # --- Data Validation and Object Creation ---
        if not nid or not raw_data.get('name') or not raw_data.get('phone'):
            raise ValueError("کدملی، نام و شماره تماس اجباری هستند.")

        # (Add your other validation logic here for format, etc.)

        companions = [
            Companion(name=comp['name'], national_id=comp['national_id'])
            for comp in raw_data.get('companions', [])
            if comp.get('name') and comp.get('national_id')
        ]
        customer = Customer(
            national_id=raw_data.get('national_id', ''),
            name=raw_data.get('name', ''),
            phone=raw_data.get('phone', ''),
            telegram_id=raw_data.get('telegram_id', ''),
            email=raw_data.get('email', ''),
            address=raw_data.get('address', ''),
            passport_image=raw_data.get('passport_image', ''),
            companions=companions
        )
        # --- Main Customer Validation ---
        if not all([customer.national_id, customer.name, customer.phone]):
            raise ValueError("فیلدهای کدملی، نام و نام و خانوادگی، و شماره تماس باید پر شوند.")

        if not validate_national_id(str(customer.national_id)):
            raise ValueError(f"کد ملی مشتری نامعتبر است.\n{customer.national_id}")

        if not validate_phone_number(customer.phone):
            raise ValueError(f"شماره تماس مشتری نامعتیر است.\n {customer.phone}")

        if customer.email:
            if not validate_email(customer.email):
                raise ValueError(f"ایمیل مشتری نامعتیر است.\n {customer.email}")

        # --- Companion Validation ---
        for companion in customer.companions:
            if not validate_national_id(str(companion.national_id)):
                raise ValueError(f"کد ملی همراه مشتری نامعتبر است.\n {companion.national_id}")

        if self._repo.get_customer(nid):
            customer_obj = self._build_customer_from_data(raw_data)
            raise CustomerExistsError("مشتری با این کد ملی قبلا ثبت شده است.", customer_obj)

        customer = self._build_customer_from_data(raw_data)
        self._repo.add_customer(customer)

        # Invalidate the completer cache so it refreshes next time
        self._customers_for_completer = []

        return customer

    def update_customer(self, customer: Customer):
        """Updates an existing customer's data in the repository."""
        # The add_customer in the repo uses merge(), so it handles updates.
        self._repo.add_customer(customer)
        self._customers_for_completer = []

    def get_customer_details(self, national_id: str) -> Customer | None:
        """Gets full details for one customer."""
        return self._repo.get_customer(national_id)
