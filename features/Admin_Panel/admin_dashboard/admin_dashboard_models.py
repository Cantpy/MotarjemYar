# Admin_Panel/admin_dashboard/admin_dashboard_models.py

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class KpiData:
    """Holds the formatted data for the four main KPI cards."""
    revenue_today: str
    revenue_month: str
    outstanding: str
    new_customers: str


@dataclass
class AttentionQueueItem:
    """Represents a single, rich item in the 'Orders Needing Attention' list."""
    invoice_number: int
    customer_name: str
    delivery_date: date
    national_id: int
    payment_status: int
    total_amount: int
    final_amount: int
    companion_count: int = 0


@dataclass
class TopPerformer:
    """Represents a single top-performing employee."""
    name: str
    value: float    # Can be revenue for translators or count for clerks
