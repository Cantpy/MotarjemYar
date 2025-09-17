# shared/assets.py

from shared.utils.path_utils import return_resource

INVOICES_DB_URL = return_resource("databases", "invoices.db")
CUSTOMERS_DB_URL = return_resource("databases", "customers.db")
SERVICES_DB_URL = return_resource('databases', 'services.db')
EXPENSES_DB_URL = return_resource('databases', 'expenses.db')
USERS_DB_URL = return_resource('databases', 'users.db')
PAYROLL_DB_URL = return_resource('databases', 'payroll.db')
INFO_PAGE_DB_URL = return_resource('databases', 'info_page.db')
WORKSPACE_DB_URL = return_resource('databases', 'workspace.db')

APP_LOGO = return_resource("resources", "png-icon.png", "Designs")
