# Admin_panel/admin_reports/admin_reports_logic.py

import pandas as pd
import jdatetime
from datetime import date
from features.Admin_Panel.admin_reports.admin_reports_repo import AdminReportsRepository
from shared.session_provider import SessionProvider


class AdminReportsLogic:
    def __init__(self, repository: AdminReportsRepository, session_provider: SessionProvider):
        self._repo = repository
        self._session_provider = session_provider

    def get_full_report_data(self, year: int) -> dict:
        """
        Generates a complete report including revenue, expenses, and profit for a year.
        """
        with (self._session_provider.invoices() as inv_sess,
              self._session_provider.services() as srv_sess,
              self._session_provider.expenses() as exp_sess):
            rev_by_month_g = self._repo.get_revenue_by_month(inv_sess, year)
            manual_exp_by_month_g = self._repo.get_manual_expenses_by_month(exp_sess, year)
            invoice_exp_by_month_g = self._repo.get_invoice_based_expenses_by_month(inv_sess, srv_sess, year)

        # Process and combine data for all 12 months
        revenues, expenses, profits = [], [], []
        for month_g in range(1, 13):
            j_month = jdatetime.date.fromgregorian(month=month_g, day=1, year=2024).month  # Get Jalali month

            # Revenue
            revenue = rev_by_month_g.get(month_g, 0.0)
            revenues.append(revenue)

            # Expenses
            manual_exp = manual_exp_by_month_g.get(month_g, 0.0)
            invoice_exp = invoice_exp_by_month_g.get(month_g, 0.0)
            total_expense = manual_exp + invoice_exp
            expenses.append(total_expense)

            # Profit
            profits.append(revenue - total_expense)

        avg_revenue = sum(revenues) / 12 if revenues else 0
        avg_expense = sum(expenses) / 12 if expenses else 0
        total_revenue = sum(revenues)
        total_expense = sum(expenses)
        total_profit = sum(profits)

        return {
            "revenues": revenues, "avg_revenue": avg_revenue, "total_revenue": total_revenue,
            "expenses": expenses, "avg_expense": avg_expense, "total_expense": total_expense,
            "profits": profits, "total_profit": total_profit,
            "persian_months": self.get_persian_month_names()
        }

    def format_to_million_toman(self, amount: float) -> float:
        """Converts an amount to millions of Tomans."""
        return amount / 1_000_000

    def get_persian_month_names(self) -> list:
        return [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]

    def format_currency(self, amount: float) -> str: return f"{amount:,.0f} تومان"

    def to_jalali(self, g_date: date) -> str: return jdatetime.date.fromgregorian(date=g_date).strftime('%Y/%m/%d')

    # --- METHOD FOR EXCEL EXPORT ---
    def export_year_data_to_excel(self, year: int, file_path: str):
        """Fetches detailed data and writes it to a multi-sheet Excel file."""
        with (self._session_provider.invoices() as inv_sess,
              self._session_provider.expenses() as exp_sess,
              self._session_provider.customers() as cust_sess):
            invoices = self._repo.get_detailed_invoices_for_year(inv_sess, year)
            expenses = self._repo.get_detailed_expenses_for_year(exp_sess, year)

            # Get companion counts in a separate query for efficiency
            customer_nids = [inv.national_id for inv in invoices]
            companion_counts = self._repo.get_companion_counts_for_customers(cust_sess, customer_nids)

        # --- Sheet 1: درآمد (Revenue) ---
        revenue_data = []
        for inv in invoices:
            revenue_data.append({
                "شماره فاکتور": inv.invoice_number,
                "تاریخ صدور": jdatetime.date.fromgregorian(date=inv.issue_date).strftime('%Y/%m/%d'),
                "نام مشتری": inv.name,
                "کد ملی مشتری": inv.national_id,
                "تعداد همراهان": companion_counts.get(inv.national_id, 0),
                "مترجم": inv.translator,
                "مبلغ کل": inv.total_amount,
                "مبلغ نهایی": inv.final_amount,
                "وضعیت پرداخت": "پرداخت شده" if inv.payment_status == 1 else "پرداخت نشده",
                "مهر دادگستری": inv.total_judiciary_count,
                "مهر خارجه": inv.total_foreign_affairs_count,
            })
        df_revenue = pd.DataFrame(revenue_data)

        # --- Sheet 2: هزینه‌ها (Expenses) ---
        expense_data = [{
            "تاریخ": jdatetime.date.fromgregorian(date=exp.expense_date).strftime('%Y/%m/%d'),
            "شرح هزینه": exp.name,
            "دسته‌بندی": exp.category,
            "مبلغ": exp.amount
        } for exp in expenses]
        df_expenses = pd.DataFrame(expense_data)

        # --- Sheet 3: سوددهی (Profitability) - Simplified for export ---
        df_profit = pd.DataFrame({
            "ماه": self.get_persian_month_names(),
            "درآمد ماهانه": self.get_full_report_data(year)["revenues"],
            "هزینه ماهانه": self.get_full_report_data(year)["expenses"],
            "سود ماهانه": self.get_full_report_data(year)["profits"],
        })

        # --- Write to Excel file ---
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_revenue.to_excel(writer, sheet_name='درآمد', index=False, header=True)
            df_expenses.to_excel(writer, sheet_name='هزینه‌ها', index=False, header=True)
            df_profit.to_excel(writer, sheet_name='سوددهی', index=False, header=True)

    def export_table_to_excel(self, table_data: list[list], headers: list[str], file_path: str):
        """
        Takes raw table data (list of lists) and headers and exports them to an Excel file.
        """
        if not table_data or not headers:
            raise ValueError("No data or headers to export.")

        # Create a pandas DataFrame directly from the list of lists and headers
        df = pd.DataFrame(table_data, columns=headers)

        # Write to an Excel file
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='نتایج جستجو', index=False, header=True)

    # --- METHODS FOR ADVANCED SEARCH ---

    def find_unpaid_invoices(self, start_date: date, end_date: date) -> list:
        with self._session_provider.invoices() as session:
            return self._repo.find_unpaid_invoices_in_range(session, start_date, end_date)

    def find_invoices_by_document_names(self, doc_names: list[str]) -> list:
        with self._session_provider.invoices() as session:
            return self._repo.find_invoices_by_document_names(session, doc_names)

    def find_frequent_customers(self, min_visits: int, start_date: date = None, end_date: date = None) -> list:
        with self._session_provider.invoices() as session:
            return self._repo.find_frequent_customers(session, min_visits, start_date, end_date)

    def get_all_service_names(self) -> list[str]:
        """Fetches a list of all service names for the auto-completer."""
        with self._session_provider.services() as session:
            # The repo method returns tuples, so we unpack them into a list of strings
            return [name for name, in self._repo.get_all_service_names(session)]
