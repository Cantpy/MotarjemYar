# shared/assets.py

from shared.utils.path_utils import get_resource_path

INVOICES_DB_URL = get_resource_path("databases", "invoices.db")
CUSTOMERS_DB_URL = get_resource_path("databases", "customers.db")
SERVICES_DB_URL = get_resource_path('databases', 'services.db')
EXPENSES_DB_URL = get_resource_path('databases', 'expenses.db')
USERS_DB_URL = get_resource_path('databases', 'users.db')
PAYROLL_DB_URL = get_resource_path('databases', 'payroll.db')
INFO_PAGE_DB_URL = get_resource_path('databases', 'info_page.db')
WORKSPACE_DB_URL = get_resource_path('databases', 'workspace.db')

APP_LOGO = get_resource_path("resources", "png-icon.png", "Designs")
