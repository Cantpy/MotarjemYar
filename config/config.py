# config/config.py

from shared.orm_models.users_models import BaseUsers
from shared.orm_models.customer_models import BaseCustomers
from shared.orm_models.invoices_models import BaseInvoices
from shared.orm_models.services_models import BaseServices
from shared.orm_models.payroll_models import BasePayroll
from shared.orm_models.expenses_models import BaseExpenses
from shared.orm_models.info_page_models import BaseInfoPage
from shared.orm_models.workspace_models import BaseWorkspace
from shared.orm_models.license_models import BaseLicense

from shared.assets import (
    CUSTOMERS_DB_URL, INVOICES_DB_URL, SERVICES_DB_URL, EXPENSES_DB_URL, USERS_DB_URL,
    PAYROLL_DB_URL, INFO_PAGE_DB_URL, WORKSPACE_DB_URL, LICENSES_DB_URL
)


DATABASE_BASES = {
    'users': BaseUsers,
    'customers': BaseCustomers,
    'invoices': BaseInvoices,
    'services': BaseServices,
    'payroll': BasePayroll,
    'expenses': BaseExpenses,
    'info_page': BaseInfoPage,
    'workspace': BaseWorkspace,
    'licenses': BaseLicense
}

DATABASE_PATHS = {
    'invoices': INVOICES_DB_URL,
    'customers': CUSTOMERS_DB_URL,
    'services': SERVICES_DB_URL,
    'expenses': EXPENSES_DB_URL,
    'users': USERS_DB_URL,
    'payroll': PAYROLL_DB_URL,
    'info_page': INFO_PAGE_DB_URL,
    'workspace': WORKSPACE_DB_URL,
    'licenses': LICENSES_DB_URL
}

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
