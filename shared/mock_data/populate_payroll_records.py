# shared/mock_data/populate_payroll.py

import jdatetime
from dateutil.relativedelta import relativedelta
import random
from features.Admin_Panel.wage_calculator.wage_calculator_logic import WageCalculatorLogic
from features.Admin_Panel.wage_calculator.wage_calculator_repo import WageCalculatorRepository
from shared.orm_models.payroll_models import PayrollRecordModel


def populate_historical_payroll_records(
        invoices_session_factory,
        payroll_session_factory
):
    """
    Populates Payroll.db with historical payroll records for the last few months.
    This function has been corrected to include the CURRENT month.
    """
    with payroll_session_factory() as payroll_session:
        # Check if data already exists to prevent re-running
        if payroll_session.query(PayrollRecordModel).first():
            return

    print("Populating Payroll.db with historical payroll records...")

    # We need a temporary instance of the logic layer to run the calculations
    temp_repo = WageCalculatorRepository()
    # Create the logic instance with the factories it needs
    temp_logic = WageCalculatorLogic(
        repository=temp_repo,
        invoices_session_factory=invoices_session_factory,
        payroll_session_factory=payroll_session_factory
    )

    today = jdatetime.date.today()

    # --- THIS IS THE FIX ---
    # We change the loop to start from 0, which includes the current month.
    # range(0, 3) will run for i = 0, 1, 2.
    for i in range(3):
        # convert to Gregorian → shift → back to Jalali
        greg = today.togregorian()
        shifted = greg - relativedelta(months=i)
        target_date = jdatetime.date.fromgregorian(date=shifted)
        year, month = target_date.year, target_date.month

        # This will now generate records for Shahrivar, Mordad, and Tir.
        print(f"  -> Generating mock payroll records for {year}/{month}...")

        try:
            # In a real scenario, you'd collect overtime. For mock data, we use random values.
            employees = temp_logic.get_employee_list()
            if not employees:
                print("    [SKIPPING] No employees found to generate payroll for.")
                continue

            mock_overtime = {emp.employee_id: random.randint(0, 20) for emp in employees}

            # Use the application's own logic to create the records
            temp_logic.execute_pay_run(year, month, mock_overtime)
        except Exception as e:
            print(
                f"    [WARNING] Could not generate mock payroll for {year}/{month}. This might happen if constants for that year don't exist. Error: {e}")
