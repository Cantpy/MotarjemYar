# orm_models.py

# ... (All your existing Base and model classes from the prompt) ...

# --- Add these dataclasses for data transfer ---
from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class FinancialReportData:
    """Data for the financial summary report."""
    total_revenue: int
    total_discount: int
    total_advance: int
    net_income: int
    fully_paid_invoices: int
    unpaid_invoices: int


@dataclass
class RevenueByTranslatorData:
    """Aggregated revenue data for a single translator."""
    translator_name: str
    total_revenue: int
    invoice_count: int
    average_revenue_per_invoice: int


@dataclass
class TopCustomerData:
    """Data representing a top customer."""
    customer_name: str
    national_id: str
    total_spent: int
    invoice_count: int


@dataclass
class UserActivityData:
    """Data representing user activity."""
    username: str
    full_name: Optional[str]
    invoice_count: int
    total_time_on_app_hours: float
