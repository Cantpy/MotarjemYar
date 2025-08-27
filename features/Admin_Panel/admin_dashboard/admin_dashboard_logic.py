# motarjemyar/admin_dashboard/admin_dashboard_logic.py
from .admin_dashboard_repo import AdminDashboardRepository
from .admin_dashboard_models import KpiData, AttentionQueueItem, TopPerformer
from shared.utils.persian_tools import to_persian_numbers


class AdminDashboardLogic:
    def __init__(self, repository, invoices_session_factory, customers_session_factory):
        self._repo = repository
        self.InvoicesSession = invoices_session_factory
        self.CustomersSession = customers_session_factory

    def get_kpi_data(self) -> KpiData:
        with self.InvoicesSession() as session:
            # Fetch raw numbers
            revenue_today = self._repo.get_revenue_today(session)
            revenue_month = self._repo.get_revenue_this_month(session)
            outstanding = self._repo.get_total_outstanding(session)
            new_customers = self._repo.get_new_customers_this_month(session)

            # Format and return as a clean KpiData object
            return KpiData(
                revenue_today=self.format_currency(revenue_today),
                revenue_month=self.format_currency(revenue_month),
                outstanding=self.format_currency(outstanding),
                new_customers=f"{to_persian_numbers(new_customers)} نفر"
            )

    def get_top_performers_data(self) -> dict:
        """Fetches and prepares data for the top performers widget."""
        with self.InvoicesSession() as session:
            raw_translators = self._repo.get_top_translators_this_month(session)
            raw_clerks = self._repo.get_top_clerks_this_month(session)

            top_translators = [TopPerformer(name=t.translator, value=t.document_count or 0) for t in raw_translators]
            top_clerks = [TopPerformer(name=c.username, value=c.invoice_count) for c in raw_clerks]

            return {
                "translators": top_translators,
                "clerks": top_clerks
            }

    def get_attention_queue(self) -> list[AttentionQueueItem]:
        """
        Fetches orders needing attention and enriches them with companion counts.
        """
        with self.InvoicesSession() as inv_session, self.CustomersSession() as cust_session:
            # 1. Get the primary invoice data
            raw_orders = self._repo.get_orders_needing_attention(inv_session)
            if not raw_orders:
                return []

            # 2. Extract national IDs to query for companions
            national_ids = [order.national_id for order in raw_orders]
            companion_counts = self._repo.get_companion_counts_for_customers(cust_session, national_ids)

            # 3. Assemble the final, rich list of dataclasses
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
                    companion_count=companion_counts.get(order.national_id, 0)
                )
                attention_items.append(item)

            return attention_items

    def format_currency(self, amount: float) -> str:
        return f"{amount:,.0f} تومان"
