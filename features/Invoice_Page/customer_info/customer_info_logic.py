# features/Invoice_Page/customer_info/customer_info_logic.py

from features.Invoice_Page.customer_info.customer_info_models import Customer, Companion
from features.Invoice_Page.customer_info.customer_info_repo import CustomerRepository
from shared.session_provider import ManagedSessionProvider
from enum import Enum, auto
from shared import to_english_number

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
    """
    Business logic for managing customers and companions.
    """

    def __init__(self, repo: CustomerRepository, customer_engine: ManagedSessionProvider):
        self._repo = repo
        self._customer_session = customer_engine
        self._completer_cache: list[dict] | None = None
        self._loaded_customer_state: Customer | None = None

    def _validate_customer_data(self, customer: Customer) -> dict[str, str]:
        """Centralized validation for customer data."""
        errors = {}
        if len(customer.name) < 3:
            errors['name'] = "نام باید حداقل ۳ حرف باشد"
        if not validate_national_id(customer.national_id):
            errors['national_id'] = "کد/شناسه ملی معتبر نیست"
        if not validate_phone_number(customer.phone):
            errors['phone'] = "شماره تماس معتبر نیست"
        if customer.email and not validate_email(customer.email):
            errors['email'] = "فرمت ایمیل صحیح نیست"

        companion_errors = [
            f"کد ملی همراه {i + 1} نامعتبر است."
            for i, companion in enumerate(customer.companions)
            if not validate_national_id(companion.national_id)
        ]
        if companion_errors:
            errors['companions'] = "\n".join(companion_errors)

        return errors

    def _build_customer_from_data(self, raw_data: dict) -> Customer:
        """Constructs a Customer DTO from a raw data dictionary."""
        companions_data = raw_data.get('companions', [])
        companions = [
            Companion(name=comp.get('name', ''), national_id=comp.get('national_id', ''))
            for comp in companions_data if comp.get('name') and comp.get('national_id')
        ]
        return Customer(
            national_id=raw_data.get('national_id', '').strip(),
            name=raw_data.get('name', '').strip(),
            phone=raw_data.get('phone', '').strip(),
            email=raw_data.get('email', '').strip(),
            address=raw_data.get('address', '').strip(),
            companions=companions
        )

    def get_all_data_for_completers(self) -> dict:
        """
        NEW: Fetches and formats data for name, NID, and phone completers.
        Returns a dictionary with lists for each completer type.
        """
        with self._customer_session() as session:
            all_customers = self._repo.get_all_customers(session)

        # Prepare the data structures
        names_data = []
        nids_data = []
        phones_data = []

        for customer in all_customers:
            nid = customer.national_id

            # Data for the name completer
            if customer.name:
                names_data.append({"display": customer.name, "lookup_id": nid})

            # Data for the national_id completer
            if customer.national_id:
                nids_data.append({"display": customer.national_id, "lookup_id": nid})

            # Data for the phone completer
            if customer.phone:
                phones_data.append({"display": customer.phone, "lookup_id": nid})

        return {
            "names": names_data,
            "nids": nids_data,
            "phones": phones_data
        }

    def get_all_customer_and_companion_info(self) -> list[dict]:
        """
        Returns a flat list of dicts for the UI completer.
        Caches the result for performance.
        """
        if self._completer_cache is not None:
            return self._completer_cache

        with self._customer_session() as session:
            customers = self._repo.get_all_customers_for_completer(session)
            companions = self._repo.get_all_companions_for_completer(session)

        unified = [
            {"name": cust["name"], "national_id": cust["national_id"], "type": "main"}
            for cust in customers
        ]
        unified.extend([
            {
                "name": f"{comp['name']} (همراه)",
                "national_id": comp["main_customer_nid"],
                "type": "companion",
                "companion_nid": comp["national_id"]
            }
            for comp in companions
        ])

        self._completer_cache = unified
        return unified

    def invalidate_completer_cache(self):
        """Forces the completer data to be re-fetched on the next request."""
        self._completer_cache = None

    def save_customer(self, raw_data: dict) -> Customer:
        """Validates and saves a new customer."""
        customer = self._build_customer_from_data(raw_data)

        validation_errors = self._validate_customer_data(customer)
        if validation_errors:
            raise ValidationError("اطلاعات وارد شده نامعتبر است.", errors=validation_errors)

        with self._customer_session() as session:
            if self._repo.get_customer(session, customer.national_id):
                raise CustomerExistsError("مشتری با این کد ملی قبلا ثبت شده است.", customer)

        with self._customer_session() as session:
            self._repo.save_customer(session, customer)

        self.invalidate_completer_cache()
        return customer

    def update_customer(self, customer: Customer) -> Customer:
        """Updates an existing customer's data."""
        with self._customer_session() as session:
            self._repo.save_customer(session, customer)
        self.invalidate_completer_cache()
        self._loaded_customer_state = customer
        return customer

    def get_customer_details(self, national_id: str) -> Customer | None:
        """Gets full details for one customer."""
        nid_normalized = to_english_number(national_id)
        with self._customer_session() as session:
            customer = self._repo.get_customer(session, nid_normalized)
            print(f"customer extracted by the logic layer: {customer} with national id: {national_id}")
        self._loaded_customer_state = customer
        return customer

    def get_all_customer_info_for_completer(self) -> list[dict]:
        """Fetches and caches customer info for the completer."""
        # In a real app, you might refresh this periodically
        if not self._completer_cache:
            with self._customer_session() as session:
                customers = self._repo.get_all_customers(session)
                self._customers_for_completer = [
                    {"name": c.name, "national_id": c.national_id} for c in customers
                ]
            return self._customers_for_completer

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
        nid = to_english_number(raw_data.get('national_id', '').strip())
        if not nid:
            # If there's no NID, it must be a new customer.
            self._loaded_customer_state = None
            form_customer = self._build_customer_from_data(raw_data)
            return CustomerStatus.NEW, form_customer

        # Check against the cached customer that was loaded onto the form.
        if self._loaded_customer_state and self._loaded_customer_state.national_id == nid:
            if self._compare_customer_data(raw_data, self._loaded_customer_state):
                modified_customer = self._build_customer_from_data(raw_data)
                return CustomerStatus.EXISTING_MODIFIED, modified_customer
            else:
                return CustomerStatus.EXISTING_UNMODIFIED, self._loaded_customer_state

        db_customer = None
        with self._customer_session() as session:
            db_customer = self._repo.get_customer(session, nid)

        if db_customer:
            self._loaded_customer_state = db_customer
            if self._compare_customer_data(raw_data, db_customer):
                modified_customer = self._build_customer_from_data(raw_data)
                return CustomerStatus.EXISTING_MODIFIED, modified_customer

            else:
                return CustomerStatus.EXISTING_UNMODIFIED, db_customer

        else:
            self._loaded_customer_state = None
            form_customer = self._build_customer_from_data(raw_data)
            return CustomerStatus.NEW, form_customer
