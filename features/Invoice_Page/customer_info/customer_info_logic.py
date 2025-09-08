# features/Invoice_Page/customer_info/customer_info_logic.py

from features.Invoice_Page.customer_info.customer_info_models import Customer, Companion
from features.Invoice_Page.customer_info.customer_info_repo import CustomerRepository
from shared.session_provider import SessionProvider
from enum import Enum, auto

from shared.utils.validation_utils import validate_national_id, validate_email, validate_phone_number


class ValidationError(ValueError):
    """Custom exception to hold structured validation errors."""

    def __init__(self, message, errors: dict[str, str]):
        super().__init__(message)
        self.errors = errors


class CustomerStatus(Enum):
    NEW = auto()
    EXISTING_UNMODIFIED = auto()    # Exists in DB and matches the form
    EXISTING_MODIFIED = auto()      # Exists in DB but form has changes


class CustomerExistsError(Exception):
    def __init__(self, message, customer_obj):
        super().__init__(message)
        self.customer = customer_obj


class CustomerLogic:
    def __init__(self, repo: CustomerRepository, session_provider: SessionProvider):
        self._repo = repo
        self.session_provider = session_provider
        self._completer_cache: list[dict] | None = None
        self._loaded_customer_state: Customer | None = None     # Tracks the autofilled customer

    def _validate_customer_data(self, customer: Customer) -> dict[str, str]:
        """
        Centralized validation for customer data.
        Returns a dictionary of errors, empty if valid.
        """
        errors = {}
        if len(customer.name) < 3:
            errors['name'] = "نام باید حداقل ۳ حرف باشد"
        if not validate_national_id(customer.national_id):
            errors['national_id'] = "کد/شناسه ملی معتبر نیست"
        if not validate_phone_number(customer.phone):
            errors['phone'] = "شماره تماس معتبر نیست"
        if customer.email and not validate_email(customer.email):
            errors['email'] = "فرمت ایمیل صحیح نیست"

        # Companion validation
        companion_errors = []
        for i, companion in enumerate(customer.companions):
            if not validate_national_id(companion.national_id):
                companion_errors.append(f"کد ملی همراه {i + 1} نامعتبر است.")
        if companion_errors:
            errors['companions'] = "\n".join(companion_errors)

        return errors

    def _build_customer_from_data(self, raw_data: dict) -> Customer:
        """Helper to construct a Customer DTO from raw form data."""
        companions_data = raw_data.get('companions', [])
        companions = [
            Companion(name=comp.get('name', ''), national_id=comp.get('national_id', ''))
            for comp in companions_data
            if comp.get('name') and comp.get('national_id')
        ]
        return Customer(
            national_id=raw_data.get('national_id', '').strip(),
            name=raw_data.get('name', '').strip(),
            phone=raw_data.get('phone', '').strip(),
            email=raw_data.get('email', '').strip(),
            address=raw_data.get('address', '').strip(),
            companions=companions
        )

    def get_all_customer_and_companion_info(self) -> list[dict]:
        """
        Fetches all customers AND companions, merges them, and returns a
        unified list for the completer. This is the single source of truth for the completer.
        """
        if self._completer_cache is not None:
            return self._completer_cache

        with self.session_provider.customers() as session:
            customers = self._repo.get_all_customers_for_completer(session)
            companions = self._repo.get_all_companions_for_completer(session)

        unified_map = {}
        for cust in customers:
            unified_map[cust['national_id']] = cust

        for comp in companions:
            if comp['national_id'] not in unified_map:
                unified_map[comp['national_id']] = {
                    "name": f"{comp['name']} (همراه)",
                    "national_id": comp['main_customer_nid']    # IMPORTANT: The ID to fetch is the main customer's
                }

        self._completer_cache = list(unified_map.values())
        return self._completer_cache

    def invalidate_completer_cache(self):
        """Forces the completer data to be re-fetched on the next request."""
        self._completer_cache = None

    def get_all_customer_info_for_completer(self) -> list[dict]:
        """Fetches and caches customer info for the completer."""
        # In a real app, you might refresh this periodically
        if not self._customers_for_completer:
            customers = self._repo.get_all_customers(self.session_provider.customers)
            self._customers_for_completer = [
                {"name": c.name, "national_id": c.national_id} for c in customers
            ]
        return self._customers_for_completer

    def save_customer(self, raw_data: dict) -> Customer:
        """
        Validates and saves a customer. This is the primary entry point for creating a new customer.
        """
        customer = self._build_customer_from_data(raw_data)

        # Step 1: Validate the data
        validation_errors = self._validate_customer_data(customer)
        if validation_errors:
            raise ValidationError("اطلاعات وارد شده نامعتبر است.", errors=validation_errors)

        # Step 2: Check for existence
        with self.session_provider.customers() as session:
            existing_customer = self._repo.get_customer(session, customer.national_id)
            if existing_customer:
                raise CustomerExistsError("مشتری با این کد ملی قبلا ثبت شده است.", customer)

        # Step 3: Save the new customer
        with self.session_provider.customers() as session:
            self._repo.save_customer(session, customer)

        self.invalidate_completer_cache()
        return customer

    def update_customer(self, customer: Customer) -> Customer:
        """
        Updates an existing customer's data. Assumes validation has already passed.
        """
        with self.session_provider.customers() as session:
            self._repo.save_customer(session, customer)

        self.invalidate_completer_cache()
        self._loaded_customer_state = customer  # Update the cached state
        return customer

    def get_customer_details(self, national_id: str) -> Customer | None:
        """Gets full details for one customer by their main national ID."""
        with self.session_provider.customers() as session:
            customer = self._repo.get_customer(session, national_id)
        self._loaded_customer_state = customer  # Cache the loaded customer
        return customer

    def _compare_customer_data(self, raw_data: dict, existing_customer: Customer) -> bool:
        """
        Compares raw form data against an existing Customer object.
        Returns True if there are any differences (i.e., it was modified).
        """
        if not existing_customer:
            return True  # If there's no existing customer to compare to, it's "modified" from nothing.

        # Compare main fields, normalizing by stripping whitespace.
        if raw_data.get('name', '').strip() != existing_customer.name: return True
        if raw_data.get('phone', '').strip() != existing_customer.phone: return True
        if raw_data.get('email', '').strip() != (existing_customer.email or ''): return True
        if raw_data.get('address', '').strip() != (existing_customer.address or ''): return True

        # Compare companions. This is more complex.
        # We'll compare them as sets of tuples to ignore order.
        raw_companions_data = raw_data.get('companions', [])

        form_companions = {
            (comp.get('name', '').strip(), comp.get('national_id', '').strip())
            for comp in raw_companions_data if comp.get('name') and comp.get('national_id')
        }

        db_companions = {
            (comp.name, comp.national_id) for comp in existing_customer.companions
        }

        if form_companions != db_companions:
            return True

        # If all checks pass, the data is unmodified.
        return False

    def check_customer_status(self, raw_data: dict) -> tuple[CustomerStatus, Customer | None]:
        """
        Checks if the data on the form corresponds to a new or existing customer
        and whether it has been modified. This is the core of the smart navigation.
        """
        nid = raw_data.get('national_id', '').strip()
        if not nid:
            # If there's no NID, it must be a new customer.
            self._loaded_customer_state = None
            form_customer = self._build_customer_from_data(raw_data)
            return CustomerStatus.NEW, form_customer

        # Check against the cached customer that was loaded onto the form.
        if self._loaded_customer_state and self._loaded_customer_state.national_id == nid:
            # The user is working with a customer they just autofilled.
            # Check if they've changed anything since it was loaded.
            if self._compare_customer_data(raw_data, self._loaded_customer_state):
                modified_customer = self._build_customer_from_data(raw_data)
                return CustomerStatus.EXISTING_MODIFIED, modified_customer
            else:
                return CustomerStatus.EXISTING_UNMODIFIED, self._loaded_customer_state

        # If not from cache, check the database directly. This handles cases where
        # the user manually types an NID that already exists.
        db_customer = self._repo.get_customer(self.session_provider.customers, nid)
        if db_customer:
            # An existing customer was found. Cache it for future checks.
            self._loaded_customer_state = db_customer
            # We assume it's unmodified since the user just typed the ID and hasn't changed anything yet.
            return CustomerStatus.EXISTING_UNMODIFIED, db_customer
        else:
            # The NID is not in the DB, so it's a new customer.
            self._loaded_customer_state = None
            form_customer = self._build_customer_from_data(raw_data)
            return CustomerStatus.NEW, form_customer
