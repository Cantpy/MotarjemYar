# shared/dtos/expenses_dto.py

from datetime import date
from dataclasses import dataclass


@dataclass
class ExpenseDTO:
    """Data Transfer Object for Expense data."""
    id: int
    name: str
    amount: int
    expense_date: date
    category: str
