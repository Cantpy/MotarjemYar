# shared/assets.py

from shared.utils.path_utils import return_resource

INVOICES_DB_URL = return_resource("databases", "invoices.db")
CUSTOMERS_DB_URL = return_resource("databases", "customers.db")
SERVICES_DB_URL = return_resource('databases', 'services.db')
EXPENSES_DB_URL = return_resource('databases', 'expenses.db')
USERS_DB_URL = return_resource('databases', 'users.db')
print('users db url: ', USERS_DB_URL)
PAYROLL_DB_URL = return_resource('databases', 'payroll.db')

APP_LOGO = return_resource("resources", "png-icon.png", "Designs")
