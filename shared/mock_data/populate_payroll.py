# shared/mock_data/populate_payroll.py

from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import random
from datetime import date, timedelta

from shared.database_models.payroll_models import (EmployeeModel, EmployeePayrollProfileModel, SystemConstantModel,
                                                   SalaryComponentModel, TaxBracketModel)
from .mock_data_source import MOCK_PEOPLE_DATA


def populate_payroll_db(payroll_session: Session):
    """Populates the Payroll.db with constants, components, and employees."""
    if payroll_session.query(EmployeeModel).first():
        return

    print("Populating Payroll.db with employees, constants, and components...")

    # --- 1. System Constants for 1404 ---
    constants_1404 = [
        SystemConstantModel(year=1404, code='MIN_DAILY_WAGE_RIAL', name='حداقل دستمزد روزانه',
                            value=Decimal('2388728')),
        SystemConstantModel(year=1404, code='HOUSING_ALLOWANCE_RIAL', name='کمک هزینه مسکن', value=Decimal('9000000')),
        SystemConstantModel(year=1404, code='GROCERIES_ALLOWANCE_RIAL', name='کمک هزینه خواروبار',
                            value=Decimal('14000000')),
        SystemConstantModel(year=1404, code='CHILDREN_ALLOWANCE_PER_CHILD_RIAL', name='حق اولاد (برای یک فرزند)',
                            value=Decimal('7166184')),
        SystemConstantModel(year=1404, code='OVERTIME_RATE_PCT', name='ضریب اضافه کاری', value=Decimal('0.4')),  # 40%
        SystemConstantModel(year=1404, code='INSURANCE_EMP_RATE_PCT', name='درصد بیمه (سهم کارگر)',
                            value=Decimal('0.07')),  # 7%
    ]
    payroll_session.add_all(constants_1404)

    # --- 2. Standard Salary Components ---
    salary_components = [
        SalaryComponentModel(name='Basic Salary', type='Earning', is_taxable_for_income_tax=True,
                             is_base_for_insurance_calculation=True),
        SalaryComponentModel(name='Overtime Pay', type='Earning', is_taxable_for_income_tax=True,
                             is_base_for_insurance_calculation=True),
        SalaryComponentModel(name='Housing Allowance', type='Earning', is_taxable_for_income_tax=True,
                             is_base_for_insurance_calculation=True),
        SalaryComponentModel(name='Groceries Allowance', type='Earning', is_taxable_for_income_tax=True,
                             is_base_for_insurance_calculation=False),
        SalaryComponentModel(name='Children Allowance', type='Earning', is_taxable_for_income_tax=False,
                             is_base_for_insurance_calculation=False),
        SalaryComponentModel(name='Commission', type='Earning', is_taxable_for_income_tax=True,
                             is_base_for_insurance_calculation=True),
        SalaryComponentModel(name='Employee Insurance', type='Deduction', is_deductible_for_taxable_income=True),
        SalaryComponentModel(name='Income Tax', type='Deduction', is_deductible_for_taxable_income=False),
    ]
    payroll_session.add_all(salary_components)

    # --- 3. Tax Brackets for 1404 ---
    # Simplified tax brackets
    tax_brackets = [
        TaxBracketModel(year=1404, lower_bound=Decimal(0), upper_bound=Decimal(1200000000), rate=Decimal(0.0)),
        TaxBracketModel(year=1404, lower_bound=Decimal(1200000000), upper_bound=Decimal(1680000000),
                        rate=Decimal(0.10)),
        TaxBracketModel(year=1404, lower_bound=Decimal(1680000000), upper_bound=None, rate=Decimal(0.15)),
    ]
    payroll_session.add_all(tax_brackets)

    # --- 4. Mock Employees ---
    for person in MOCK_PEOPLE_DATA:
        employee = EmployeeModel(
            employee_id=str(uuid.uuid4()),
            first_name=person['first'],
            last_name=person['last'],
            # --- The national_id now comes from the shared source ---
            national_id=person['nid'],
            hire_date=date.today() - timedelta(days=random.randint(30, 1000)),
            payroll_profile=EmployeePayrollProfileModel(
                payment_type=person['payment'],
                custom_daily_payment_rials=Decimal(person.get('salary_rials', 0)),
                commission_rate=Decimal(person.get('rate', 0)),
                marital_status=random.choice(['Single', 'Married']),
                children_count=random.randint(0, 2)
            )
        )
        payroll_session.add(employee)

    payroll_session.commit()
