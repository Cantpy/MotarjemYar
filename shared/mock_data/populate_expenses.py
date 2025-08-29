# shared/mock_data/populate_expenses.py

import random
from datetime import date
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta
from ..database_models.expenses_models import ExpenseModel


def populate_expenses_db(expenses_session: Session):
    """Populates the Expenses.db with a 3-year history of mock monthly expenses."""
    if expenses_session.query(ExpenseModel).first():
        return  # Data already exists

    print("Populating Expenses.db with mock monthly expenses...")

    expenses = []
    today = date.today()
    for i in range(36):  # 3 years * 12 months
        current_month = today - relativedelta(months=i)

        # Rent for the month
        expenses.append(ExpenseModel(
            name="اجاره دفتر",
            amount=random.randint(15, 25) * 1000000,
            expense_date=current_month,
            category="Rent"
        ))

        # Generic salary expense (note: this is separate from the detailed payroll records)
        expenses.append(ExpenseModel(
            name="حقوق کارمندان (کلی)",
            amount=random.randint(80, 120) * 1000000,
            expense_date=current_month,
            category="Salary"
        ))

        # Utilities and supplies for the month
        expenses.append(ExpenseModel(
            name="هزینه های جاری (آب، برق، اینترنت)",
            amount=random.randint(2, 5) * 1000000,
            expense_date=current_month,
            category="Utilities"
        ))

    expenses_session.add_all(expenses)
    expenses_session.commit()
