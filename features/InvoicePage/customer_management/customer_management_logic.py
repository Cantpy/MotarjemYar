from typing import List, Optional, Tuple
from features.InvoicePage.customer_management.customer_managemnet_models import (CustomerData, CompanionData,
                                                                                 CustomerDisplayData)
from features.InvoicePage.customer_management.customer_management_repo import CustomerRepository


class CustomerLogic:
    """Business logic for customer management."""

    def __init__(self, repository: CustomerRepository):
        self.repository = repository

    def get_all_customers_with_details(self) -> List[CustomerDisplayData]:
        """Get all customers with their companions and invoice counts."""
        try:
            customers = self.repository.get_all_customers_with_details()
            return customers
        except Exception as e:
            print("error getting all customers with details: ", e)

    def search_customers_and_companions(self, search_term: str) -> List[CustomerDisplayData]:
        """Search customers and companions by various criteria."""
        return self.repository.search_customers_and_companions(search_term)

    def get_customer_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        """Get a specific customer by national ID."""
        return self.repository.get_customer_by_national_id(national_id)

    def create_customer(self, customer_data: CustomerData) -> Tuple[bool, List[str]]:
        """Create a new customer with validation."""
        # Validate customer data
        if not customer_data.is_valid():
            return False, customer_data.get_validation_errors()

        # Check if customer already exists
        existing_customer = self.repository.get_customer_by_national_id(customer_data.national_id)
        if existing_customer:
            return False, ["مشتری با این کد ملی قبلاً ثبت شده است"]

        # Create customer
        success = self.repository.create_customer(customer_data)
        if success:
            return True, []
        else:
            return False, ["خطا در ایجاد مشتری"]

    def update_customer(self, customer_data: CustomerData) -> Tuple[bool, List[str]]:
        """Update an existing customer with validation."""
        # Validate customer data
        if not customer_data.is_valid():
            return False, customer_data.get_validation_errors()

        # Check if customer exists
        existing_customer = self.repository.get_customer_by_national_id(customer_data.national_id)
        if not existing_customer:
            return False, ["مشتری یافت نشد"]

        # Update customer
        success = self.repository.update_customer(customer_data)
        if success:
            return True, []
        else:
            return False, ["خطا در بروزرسانی مشتری"]

    def delete_customer(self, national_id: str) -> Tuple[bool, List[str], bool, int]:
        """
        Delete a customer with validation.
        Returns: (success, errors, has_active_invoices, active_invoice_count)
        """
        # Check if customer exists
        customer = self.repository.get_customer_by_national_id(national_id)
        if not customer:
            return False, ["مشتری یافت نشد"], False, 0

        # Check for active invoices
        has_active_invoices, active_count = self.repository.check_customer_has_active_invoices(national_id)

        # Return info about active invoices without deleting
        if has_active_invoices:
            return False, [], True, active_count

        # Delete customer
        success = self.repository.delete_customer(national_id)
        if success:
            return True, [], False, 0
        else:
            return False, ["خطا در حذف مشتری"], False, 0

    def force_delete_customer(self, national_id: str) -> Tuple[bool, List[str]]:
        """Force delete a customer even if they have active invoices."""
        customer = self.repository.get_customer_by_national_id(national_id)
        if not customer:
            return False, ["مشتری یافت نشد"]

        success = self.repository.delete_customer(national_id)
        if success:
            return True, []
        else:
            return False, ["خطا در حذف مشتری"]

    def get_companions_by_customer_id(self, customer_national_id: str) -> List[CompanionData]:
        """Get all companions for a customer."""
        return self.repository.get_companions_by_customer_id(customer_national_id)

    def create_companion(self, companion_data: CompanionData) -> Tuple[bool, List[str]]:
        """Create a new companion with validation."""
        # Validate companion data
        if not companion_data.is_valid():
            return False, companion_data.get_validation_errors()

        # Check if customer exists
        customer = self.repository.get_customer_by_national_id(companion_data.customer_national_id)
        if not customer:
            return False, ["مشتری مرتبط یافت نشد"]

        # Create companion
        success = self.repository.create_companion(companion_data)
        if success:
            return True, []
        else:
            return False, ["خطا در ایجاد همراه"]

    def update_companion(self, companion_data: CompanionData) -> Tuple[bool, List[str]]:
        """Update an existing companion with validation."""
        # Validate companion data
        if not companion_data.is_valid():
            return False, companion_data.get_validation_errors()

        # Update companion
        success = self.repository.update_companion(companion_data)
        if success:
            return True, []
        else:
            return False, ["خطا در بروزرسانی همراه"]

    def delete_companion(self, companion_id: int) -> Tuple[bool, List[str]]:
        """Delete a companion."""
        success = self.repository.delete_companion(companion_id)
        if success:
            return True, []
        else:
            return False, ["خطا در حذف همراه"]

    def validate_customer_data(self, customer_data: CustomerData) -> List[str]:
        """Validate customer data and return errors."""
        return customer_data.get_validation_errors()

    def validate_companion_data(self, companion_data: CompanionData, companion_index: int = 0) -> List[str]:
        """Validate companion data and return errors."""
        return companion_data.get_validation_errors(companion_index)

    def check_customer_has_active_invoices(self, national_id: str) -> Tuple[bool, int]:
        """Check if customer has active invoices."""
        return self.repository.check_customer_has_active_invoices(national_id)

    def format_customer_display_text(self, customer: CustomerDisplayData) -> str:
        """Format customer information for display."""
        base_text = f"{customer.name} ({customer.national_id})"
        if customer.companions:
            companion_names = [comp.name for comp in customer.companions]
            base_text += f" - همراهان: {', '.join(companion_names)}"
        return base_text

    def get_customer_summary(self, customer: CustomerDisplayData) -> str:
        """Get a summary of customer information."""
        summary = f"نام: {customer.name}\n"
        summary += f"کد ملی: {customer.national_id}\n"
        summary += f"تلفن: {customer.phone}\n"
        if customer.email:
            summary += f"ایمیل: {customer.email}\n"
        if customer.address:
            summary += f"آدرس: {customer.address}\n"
        if customer.telegram_id:
            summary += f"تلگرام: {customer.telegram_id}\n"
        summary += f"تعداد فاکتورها: {customer.invoice_count}\n"

        if customer.companions:
            summary += f"همراهان ({len(customer.companions)}):\n"
            for i, comp in enumerate(customer.companions, 1):
                summary += f"  {i}. {comp.name} ({comp.national_id})\n"
        else:
            summary += "همراه: ندارد\n"

        return summary
