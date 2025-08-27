# _logic.py
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer, Companion
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_repo import CustomerRepository

from enum import Enum, auto

from shared.utils.validation_utils import validate_national_id, validate_email, validate_phone_number


class CustomerStatus(Enum):
    NEW = auto()
    EXISTING_UNMODIFIED = auto()    # Exists in DB and matches the form
    EXISTING_MODIFIED = auto()      # Exists in DB but form has changes


class CustomerExistsError(Exception):
    def __init__(self, message, customer_obj):
        super().__init__(message)
        self.customer = customer_obj


class CustomerLogic:
    def __init__(self):
        self._repo = CustomerRepository()
        self._loaded_customer_state: Customer | None = None
        self._customers_for_completer = []
        self._completer_cache: list[dict] | None = None
        self._current_customer_on_form: Customer = None     # Tracks the autofilled customer

    def _build_customer_from_data(self, raw_data: dict) -> Customer:
        """Helper to construct a Customer object from raw form data."""
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
        Fetches all customers AND companions, merges them, removes duplicates,
        and returns a unified list for the completer.
        """
        if self._completer_cache is not None:
            return self._completer_cache

        print("LOGIC: Refreshing completer cache from database...")
        customers = self._repo.get_all_customers_for_completer()
        companions = self._repo.get_all_companions_for_completer()

        # --- Merge and De-duplicate Logic ---
        # We use a dictionary keyed by NID to automatically handle duplicates.
        # The main customer's data will take precedence if an NID is in both lists.
        unified_map = {}

        # Add all customers first
        for cust in customers:
            unified_map[cust['national_id']] = {"name": cust['name'], "national_id": cust['national_id']}

        # Add companions only if their NID isn't already in the map
        for comp in companions:
            if comp['national_id'] not in unified_map:
                # When a companion is selected, we actually need to load their main customer.
                # So, we store the main customer's NID for the lookup.
                unified_map[comp['national_id']] = {
                    "name": f"{comp['name']} (همراه)",  # Add a suffix for clarity in the UI
                    "national_id": comp['main_customer_nid']  # IMPORTANT: The ID to fetch is the main customer's
                }

        self._completer_cache = list(unified_map.values())
        return self._completer_cache

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

        # (Add your other validation _logic here for format, etc.)

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
        self.invalidate_completer_cache()

        return customer

    def update_customer(self, customer: Customer):
        """Updates an existing customer's data in the repository."""
        self._repo.add_customer(customer)
        self._customers_for_completer = []      # Invalidate cache
        self._loaded_customer_state = customer  # Cache the newly updated customer
        self.invalidate_completer_cache()

    def get_customer_details(self, national_id: str) -> Customer | None:
        """
        Gets full details for one customer. The national_id provided will always
        be the main customer's NID, even if a companion was selected.
        """
        customer = self._repo.get_customer(national_id)
        self._loaded_customer_state = customer
        return customer

    def invalidate_completer_cache(self):
        """Forces the completer data to be re-fetched on the next request."""
        self._completer_cache = None

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
        db_customer = self._repo.get_customer(nid)
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
