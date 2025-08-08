# logic.py
from datetime import date
from typing import List
from features.Reports.reports_repo import ReportsRepo
from features.Reports.reports_models import (
    FinancialReportData, RevenueByTranslatorData, TopCustomerData, UserActivityData
)


class ReportsLogic:
    def __init__(self, repo: ReportsRepo):
        self.repo = repo

    def generate_financial_report(self, start_date: date, end_date: date) -> FinancialReportData:
        data = self.repo.get_financial_summary(start_date, end_date)
        # Provide defaults for all keys if data is missing
        defaults = {
            'total_revenue': 0, 'total_discount': 0, 'total_advance': 0,
            'net_income': 0, 'fully_paid_invoices': 0, 'unpaid_invoices': 0
        }
        defaults.update(data)
        return FinancialReportData(**defaults)

    def generate_translator_performance_report(self, start_date: date, end_date: date) -> List[RevenueByTranslatorData]:
        data = self.repo.get_revenue_by_translator(start_date, end_date)
        report_data = []
        for item in data:
            invoice_count = item.get('invoice_count', 1)  # Avoid division by zero
            item['average_revenue_per_invoice'] = (item.get('total_revenue', 0) / invoice_count) if invoice_count > 0 else 0
            report_data.append(RevenueByTranslatorData(**item))
        return report_data

    def generate_top_customers_report(self, start_date: date, end_date: date) -> List[TopCustomerData]:
        data = self.repo.get_top_customers(start_date, end_date)
        return [TopCustomerData(**item) for item in data]

    def generate_user_activity_report(self, start_date: date, end_date: date) -> List[UserActivityData]:
        data = self.repo.get_user_activity(start_date, end_date)
        report_data = []
        for item in data:
            item['total_time_on_app_hours'] = item.pop('total_time_on_app_seconds', 0) / 3600
            report_data.append(UserActivityData(**item))
        return report_data
