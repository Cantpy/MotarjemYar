# config/config.py

from shared.orm_models.business_models import BaseBusiness
from shared.orm_models.payroll_models import BasePayroll
from shared.orm_models.info_page_models import BaseInfoPage
from shared.orm_models.workspace_models import BaseWorkspace
from shared.orm_models.license_models import BaseLicense

from shared.assets import (
    PAYROLL_DB_URL, INFO_PAGE_DB_URL, WORKSPACE_DB_URL, LICENSES_DB_URL, BUSINESS_DB_URL
)


DATABASE_BASES = {
    'business': BaseBusiness,
    'payroll': BasePayroll,
    'info_page': BaseInfoPage,
    'workspace': BaseWorkspace,
    'licenses': BaseLicense
}

DATABASE_PATHS = {
    'business': BUSINESS_DB_URL,
    'payroll': PAYROLL_DB_URL,
    'info_page': INFO_PAGE_DB_URL,
    'workspace': WORKSPACE_DB_URL,
    'licenses': LICENSES_DB_URL
}

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
