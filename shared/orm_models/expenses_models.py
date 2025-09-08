# shared/orm_models/expenses_models.py

from sqlalchemy import (
    create_engine, func, extract, Text, Integer, Date, CheckConstraint, Index
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from datetime import date

BaseExpenses = declarative_base()


class ExpenseModel(BaseExpenses):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)     # e.g., 'Salary', 'Rent', 'Utilities'

    __table_args__ = (
        CheckConstraint("category IN ('Salary', 'Rent', 'Utilities', 'Office Supplies', 'Other')"),
        Index('idx_expenses_date', 'expense_date'),
        Index('idx_expenses_category', 'category'),
    )

    def __repr__(self) -> str:
        return f"<ExpenseModel(name={self.name}, amount={self.amount}, date={self.expense_date})>"