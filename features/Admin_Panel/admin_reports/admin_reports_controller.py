# Admin_Panel/admin_reports/admin_reports_controller.py

from PySide6.QtWidgets import QFileDialog
from shared import show_information_message_box, show_error_message_box, show_warning_message_box
import jdatetime

# Import all necessary components
from .admin_reports_view import AdminReportsView
from .admin_reports_logic import AdminReportsLogic
from .descriptive_search_parser import DescriptiveSearchParser


# --- Sub-Controller for the Financial Charts Tab ---
class FinancialReportsController:
    """Manages the logic for the annual financial charts."""

    def __init__(self, view, logic):
        self._view = view
        self._logic = logic
        self._current_year = jdatetime.date.today().year

        # Connect signals from the financial _view to its methods
        self._view.next_year_requested.connect(self._next_year)
        self._view.previous_year_requested.connect(self._previous_year)
        self._view.export_requested.connect(self._handle_export)

        self.load_report_data()

    def load_report_data(self):
        try:
            data = self._logic.get_full_report_data(self._current_year)
            self._view.set_year_display(self._current_year)

            self._view.update_tooltip_data(
                revenues=data["revenues"], avg_revenue=data["avg_revenue"],
                expenses=data["expenses"], avg_expense=data["avg_expense"],
                profits=data["profits"], persian_months=data["persian_months"]
            )

            self._view.update_stat_cards(data["total_revenue"], data["total_expense"], data["total_profit"])

            revenues_m = [self._logic.format_to_million_toman(v) for v in data["revenues"]]
            avg_revenue_m = self._logic.format_to_million_toman(data["avg_revenue"])
            expenses_m = [self._logic.format_to_million_toman(v) for v in data["expenses"]]
            avg_expense_m = self._logic.format_to_million_toman(data["avg_expense"])
            profits_m = [self._logic.format_to_million_toman(v) for v in data["profits"]]

            self._view.update_revenue_chart(revenues_m, avg_revenue_m, data["persian_months"])
            self._view.update_expense_chart(expenses_m, avg_expense_m, data["persian_months"])
            self._view.update_profit_chart(revenues_m, expenses_m, profits_m, data["persian_months"])

        except Exception as e:
            print(f"An error occurred while loading financial report data: {e}")

    def _next_year(self):
        self._current_year += 1
        self.load_report_data()

    def _previous_year(self):
        self._current_year -= 1
        self.load_report_data()

    def _handle_export(self):
        suggested_filename = f"Report_{self._current_year}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self._view, "ذخیره گزارش اکسل", suggested_filename,
                                                   "Excel Files (*.xlsx)")
        if file_path:
            try:
                self._logic.export_year_data_to_excel(self._current_year, file_path)
                show_information_message_box(self._view,
                                             "موفقیت",
                                             f"گزارش با موفقیت ذخیره شد:\n{file_path}")
            except Exception as e:
                show_error_message_box(self._view,
                                       "خطا",
                                       f"خطایی در ایجاد فایل اکسل رخ داد:\n{e}")


# --- Sub-Controller for the Advanced Search Tab ---
class AdvancedSearchController:
    """Manages the logic for the advanced search queries."""

    def __init__(self, view, logic):
        self._view = view
        self._logic = logic
        self._view.search_requested.connect(self.perform_search)
        self._parser = DescriptiveSearchParser()

        self._current_results = []
        self._current_headers = []

        self._connect_signals()
        # Fetch completer data and set it up in the _view ---
        self._setup_completer()

    def _connect_signals(self):
        self._view.search_requested.connect(self.perform_search)
        self._view.descriptive_search_requested.connect(self.perform_descriptive_search)
        self._view.export_table_requested.connect(self._handle_export)

    def perform_descriptive_search(self, query: str):
        """Parses a natural language query and then calls the main search method."""
        print(f"Parsing descriptive query: '{query}'")
        criteria = self._parser.parse(query)

        if criteria:
            print(f"Parsed criteria: {criteria}")
            self.perform_search(criteria)  # Reuse the existing search logic!
        else:
            show_warning_message_box(self._view,
                                     "نامفهوم",
                                     "متاسفانه منظور شما از این درخواست مشخص نشد.")

    def _setup_completer(self):
        """Fetches service names and initializes the QCompleter in the _view."""
        try:
            service_names = self._logic.get_all_service_names()
            self._view.set_document_completer(service_names)
        except Exception as e:
            print(f"Failed to load service names for completer: {e}")
            # The app can still run, just without auto-completion

    def perform_search(self, criteria: dict):
        search_type = criteria.get('type')
        results = []
        headers = []

        try:
            if search_type == 'unpaid':
                data = self._logic.find_unpaid_invoices(criteria['start_date'], criteria['end_date'])
                headers = ["شماره فاکتور", "نام مشتری", "تاریخ صدور", "مبلغ پرداخت نشده", "تلفن"]
                results = [
                    [inv.invoice_number, inv.name, inv.issue_date, f"{inv.total_amount:,.0f}", inv.phone]
                    for inv in data
                ]

            elif search_type == 'docs':
                doc_names = criteria.get('doc_names')
                if not doc_names:
                    show_warning_message_box(self._view,
                                             "ورودی نامعتبر",
                                             "لطفا حداقل نام یک سند را وارد کنید.")
                    return
                data = self._logic.find_invoices_by_document_names(doc_names)
                headers = ["شماره فاکتور", "نام مشتری", "کد ملی", "تاریخ صدور", "مبلغ کل"]
                results = [
                    [inv.invoice_number, inv.name, inv.national_id, inv.issue_date, f"{inv.total_amount:,.0f}"]
                    for inv in data
                ]

            elif search_type == 'frequent':
                min_visits = criteria.get('min_visits')
                start_date = criteria.get('start_date')
                end_date = criteria.get('end_date')
                data = self._logic.find_frequent_customers(min_visits, start_date, end_date)
                headers = ["نام مشتری", "کد ملی", "تعداد مراجعه"]
                # Data is already in the correct tuple format
                results = [[row.name, row.national_id, row.visit_count] for row in data]

            self._current_results = results
            self._current_headers = headers

            self._view.display_results(results, headers)
            if not results:
                show_information_message_box(self._view,
                                             "نتیجه",
                                             "هیچ موردی با این مشخصات یافت نشد.")

        except Exception as e:
            print(f"An error occurred during advanced search: {e}")
            show_error_message_box(self._view,
                                   "خطا",
                                   f"خطایی در هنگام جستجو رخ داد:\n{e}")

    def _handle_export(self):
        """Exports the currently displayed table data to an Excel file."""
        if not self._current_results:
            show_warning_message_box(self._view,
                                     "خطا",
                                     "داده‌ای برای خروجی گرفتن وجود ندارد.")
            return

        suggested_filename = "Advanced_Search_Results.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self._view, "ذخیره نتایج اکسل", suggested_filename,
                                                   "Excel Files (*.xlsx)")

        if file_path:
            try:
                self._logic.export_table_to_excel(
                    self._current_results,
                    self._current_headers,
                    file_path
                )
                show_information_message_box(self._view,
                                             "موفقیت",
                                             f"نتایج با موفقیت ذخیره شد:\n{file_path}")
            except Exception as e:
                show_error_message_box(self._view,
                                       "خطا",
                                       f"خطایی در ایجاد فایل اکسل رخ داد:\n{e}")


# --- Main Controller (The Orchestrator) ---
class AdminReportsController:
    """
    The main controller that creates and orchestrates the sub-controllers
    for each tab within the Reports section.
    """

    def __init__(self, view: AdminReportsView, logic: AdminReportsLogic):
        self._view = view
        self._logic = logic

        # --- Create and store the sub-controllers, giving them their _view and dependencies ---
        self.financial_controller = FinancialReportsController(self._view.financial_reports, self._logic)
        self.advanced_search_controller = AdvancedSearchController(self._view.advanced_search, self._logic)

    def get_view(self) -> AdminReportsView:
        """Returns the main container _view for the entire Reports tab."""
        return self._view
