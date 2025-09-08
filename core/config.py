from shared.orm_models.users_models import BaseUsers
from shared.orm_models.customer_models import BaseCustomers
from shared.orm_models.invoices_models import BaseInvoices
from shared.orm_models.services_models import BaseServices
from shared.orm_models.payroll_models import BasePayroll
from shared.orm_models.expenses_models import BaseExpenses


DATABASE_BASES = {
    'users': BaseUsers,
    'customers': BaseCustomers,
    'invoices': BaseInvoices,
    'services': BaseServices,
    'payroll': BasePayroll,
    'expenses': BaseExpenses,
}

DATABASE_PATHS = {
    'invoices': 'databases/invoices.db',
    'customers': 'databases/customers.db',
    'services': 'databases/services.db',
    'expenses': 'databases/expenses.db',
    'users': 'databases/users.db',
    'payroll': 'databases/payroll.db'
}
