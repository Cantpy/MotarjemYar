# features/Admin_Panel/admin_dashboard/admin_dashboard_logic.py

from .admin_dashboard_repo import AdminDashboardRepository
from .admin_dashboard_models import KpiData, AttentionQueueItem, TopPerformer, UnpaidCollectedItem
from shared.utils.persian_tools import to_persian_numbers
from datetime import datetime

from shared. session_provider import ManagedSessionProvider


class AdminDashboardLogic:
    def __init__(self, repository: AdminDashboardRepository,
                 invoices_engine: ManagedSessionProvider,
                 customers_engine: ManagedSessionProvider):
        self._repo = repository
        self._invoices_session = invoices_engine
        self._customers_session = customers_engine

    def get_kpi_data(self) -> KpiData:
        with self._invoices_session() as session:
            revenue_today = self._repo.get_revenue_today(session)
            revenue_month = self._repo.get_revenue_this_month(session)
            outstanding = self._repo.get_total_outstanding(session)
            new_customers = self._repo.get_new_customers_this_month(session)

            return KpiData(
                revenue_today=self.format_currency(revenue_today),
                revenue_month=self.format_currency(revenue_month),
                outstanding=self.format_currency(outstanding),
                new_customers=f"{to_persian_numbers(new_customers)} نفر"
            )

    def get_top_performers_data(self) -> dict:
        """Fetches and prepares data for the top performers widget."""
        with self._invoices_session() as session:
            raw_translators = self._repo.get_top_translators_this_month(session)
            raw_clerks = self._repo.get_top_clerks_this_month(session)

            top_translators = [TopPerformer(name=t.translator, value=t.document_count or 0) for t in raw_translators]
            top_clerks = [TopPerformer(name=c.username, value=c.invoice_count) for c in raw_clerks]

            return {
                "translators": top_translators,
                "clerks": top_clerks
            }

    def get_attention_queue(self) -> dict:
        """
        Fetches orders needing attention and enriches them with companion counts.
        """
        with self._invoices_session() as inv_session, self._customers_session() as cust_session:
            raw_orders = self._repo.get_orders_needing_attention(inv_session)
            unpaid_collected = self.get_unpaid_collected_data()
            if not raw_orders and not unpaid_collected:
                return {}

            national_ids = [order.national_id for order in raw_orders]
            companion_counts = self._repo.get_companion_counts_for_customers(cust_session, national_ids)

            attention_items = []
            for order in raw_orders:
                item = AttentionQueueItem(
                    invoice_number=order.invoice_number,
                    customer_name=order.name,
                    delivery_date=order.delivery_date,
                    national_id=order.national_id,
                    payment_status=order.payment_status,
                    total_amount=order.total_amount,
                    final_amount=order.final_amount,
                    advance_payment=order.advance_payment,
                    companion_count=companion_counts.get(order.national_id, 0)
                )
                attention_items.append(item)

            return {
                "due_orders": attention_items,
                "unpaid_collected": unpaid_collected
            }

    def get_unpaid_collected_data(self) -> list[UnpaidCollectedItem]:
        """Fetches and prepares data for unpaid but collected invoices."""
        with self._invoices_session() as session:
            raw_invoices = self._repo.get_unpaid_collected_invoices(session)
            unpaid_items = []
            for invoice in raw_invoices:
                days_diff = (datetime.now() - invoice.collection_date).days if invoice.collection_date else 0
                item = UnpaidCollectedItem(
                    invoice_number=invoice.invoice_number,
                    customer_name=invoice.name,
                    phone_number=invoice.phone,
                    amount_due=invoice.final_amount,
                    days_since_collection=days_diff
                )
                unpaid_items.append(item)
            return unpaid_items

    def format_currency(self, amount: float) -> str:
        return f"{amount:,.0f} تومان"
