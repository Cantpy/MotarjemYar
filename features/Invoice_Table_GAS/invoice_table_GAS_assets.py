from shared import return_resource

INVOICES_DB_URL = return_resource('databases', 'invoices.db')
USERS_DB_URL = return_resource('databases', 'users.db')


# Uncomment the following lines if you want to use the assets dictionary
# ASSETS = {
#     'invoices_db_url': INVOICES_DB_URL,
#     'users_db_url': USERS_DB_URL
# }
#
#
# def get_assets():
#     """
#     Returns the assets required for the Invoice Table GAS feature.
#
#     This function provides the database URLs needed for the invoice management system.
#
#     Returns:
#         dict: A dictionary containing the database URLs.
#     """
#     return ASSETS
#
#
# def get_invoice_db_url():
#     """
#     Returns the URL for the invoices database.
#
#     This function is a convenience method to access the invoices database URL directly.
#
#     Returns:
#         str: The URL of the invoices database.
#     """
#     return ASSETS['invoices_db_url']
#
#
# def get_users_db_url():
#     """
#     Returns the URL for the users database.
#
#     This function is a convenience method to access the users database URL directly.
#
#     Returns:
#         str: The URL of the users database.
#     """
#     return ASSETS['users_db_url']
