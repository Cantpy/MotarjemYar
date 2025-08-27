# motarjemyar/wage_calculator/wage_calculator_logic.py

from datetime import date
import jdatetime
from .wage_calculator_models import EmployeeData, CalculatedWage, PayrollStats, RoleSummaryData
from .wage_calculator_repo import WageCalculatorRepository
from collections import defaultdict


class WageCalculatorLogic:
    def __init__(self, repository: WageCalculatorRepository,
                 invoices_session_factory,
                 users_session_factory,
                 payroll_session_factory):
        self._repo = repository
        self.InvoicesSession = invoices_session_factory
        self.UsersSession = users_session_factory
        self.PayrollSession = payroll_session_factory

    def get_all_employees_for_display(self) -> list[EmployeeData]:
        """Gets all users and their payroll profiles, formatted for the main table."""
        with self.UsersSession() as u_session, self.PayrollSession() as p_session:
            users = self._repo.get_all_employees(u_session)
            employee_list = []
            for user in users:
                profile = self._repo.get_employee_payroll_profile(p_session, user.id)
                if user.user_profile and profile:
                    payment_detail = ""
                    if profile.payment_type == 'Fixed':
                        payment_detail = f"{profile.custom_base_salary:,.0f} تومان"
                    elif profile.payment_type == 'Commission':
                        if user.role == 'translator':
                            payment_detail = f"{profile.commission_rate * 100:.0f}% از ترجمه"
                        else:
                            payment_detail = f"{profile.per_invoice_rate:,.0f} برای هر فاکتور"

                    employee_list.append(EmployeeData(
                        user_id=user.id,
                        username=user.username,
                        full_name=user.user_profile.full_name,
                        role=user.role,
                        payment_type=profile.payment_type,
                        payment_detail=payment_detail
                    ))
            return employee_list

    def calculate_wage(self, employee_user_id: int, inputs: dict) -> CalculatedWage:
        """The core, compliant calculation engine."""
        year = inputs.get('year', jdatetime.date.today().year)

        with self.PayrollSession() as p_session, self.UsersSession() as u_session:
            profile = self._repo.get_employee_payroll_profile(p_session, employee_user_id)
            constants = self._repo.get_labor_law_constants(p_session, year)
            user = self._repo.get_user_by_id(u_session, employee_user_id)

        if not user or not user.user_profile or not profile or not constants:
            raise ValueError("اطلاعات حقوقی کارمند یا قوانین کار برای سال مشخص شده یافت نشد.")

        # --- Fixed Salary Calculation ---
        if profile.payment_type == 'Fixed':
            base_salary = max(profile.custom_base_salary, constants.get('base_salary', 0))
            housing = constants.get('housing_allowance', 0)
            groceries = constants.get('groceries_allowance', 0)

            overtime_hours = inputs.get('overtime_hours', 0)
            num_children = inputs.get('num_children', 0)

            children_pay = num_children * constants.get('children_allowance_per_child', 0)
            overtime_rate = (base_salary / 220) * constants.get('overtime_rate_multiplier', 1.4)
            overtime_pay = overtime_hours * overtime_rate

            total_allowances = housing + groceries + children_pay
            gross_wage = base_salary + total_allowances + overtime_pay

            social_security = gross_wage * constants.get('social_security_employee_rate', 0.07)
            tax = (gross_wage - social_security) * constants.get('estimated_tax_rate', 0.10)
            net_wage = gross_wage - social_security - tax

            details = (f"حقوق پایه: {base_salary:,.0f}\n"
                       f"مزایا (مسکن، خواروبار، اولاد): {total_allowances:,.0f}\n"
                       f"اضافه کار ({overtime_hours} ساعت): {overtime_pay:,.0f}\n"
                       f"جمع ناخالص: {gross_wage:,.0f}\n"
                       f"--- کسورات ---\n"
                       f"بیمه تامین اجتماعی: ({social_security:,.0f})\n"
                       f"مالیات (تخمینی): ({tax:,.0f})")

            return CalculatedWage(user.user_profile.full_name, net_wage, details)

        # --- Commission Salary Calculation ---
        elif profile.payment_type == 'Commission':
            start_date, end_date = inputs['start_date'], inputs['end_date']
            performance_bonus = 0
            details = ""
            with self.InvoicesSession() as i_session:
                if user.role == 'translator':
                    performance_value = self._repo.get_translator_performance(i_session, user.user_profile.full_name,
                                                                              start_date, end_date)
                    performance_bonus = performance_value * profile.commission_rate
                    details = f"جمع مبلغ ترجمه: {performance_value:,.0f}\nدرصد سهم: {profile.commission_rate * 100:.0f}%\nمبلغ سهم: {performance_bonus:,.0f}"
                else:  # Clerk or Accountant
                    performance_value = self._repo.get_clerk_performance(i_session, user.username, start_date, end_date)
                    performance_bonus = performance_value * profile.per_invoice_rate
                    details = f"تعداد فاکتور: {performance_value}\nمبلغ هر فاکتور: {profile.per_invoice_rate:,.0f}\nمبلغ کل: {performance_bonus:,.0f}"

            return CalculatedWage(user.user_profile.full_name, performance_bonus, details)

        else:
            raise ValueError(f"نوع پرداخت ناشناخته: {profile.payment_type}")

    def get_role_summary_data(self) -> list[RoleSummaryData]:
        """This method is now less relevant for a monthly view but can remain as is for a general overview."""
        summary_agg = defaultdict(lambda: {"count": 0, "salaries": []})

        with self.UsersSession() as u_session, self.PayrollSession() as p_session:
            users = self._repo.get_all_employees(u_session)
            for user in users:
                profile = self._repo.get_employee_payroll_profile(p_session, user.id)
                role = user.role

                if profile:
                    summary_agg[role]["count"] += 1
                    if profile.payment_type == 'Fixed':
                        salary = profile.custom_base_salary or 0
                        summary_agg[role]["salaries"].append(salary)

        # Define the display names for our roles
        role_map = {
            "admin": "مدیران",
            "clerk": "کارمندان",
            "translator": "مترجمان",
            "accountant": "حسابداران"
        }

        # Convert the aggregated data into our clean list of dataclasses
        final_summary_list = []
        for role_key, role_name in role_map.items():
            data = summary_agg.get(role_key, {"count": 0, "salaries": []})

            total_salary = sum(data["salaries"])
            average_salary = total_salary / len(data["salaries"]) if data["salaries"] else 0

            final_summary_list.append(RoleSummaryData(
                role_key=role_key,
                role_name=role_name,
                count=data["count"],
                total_salary=int(total_salary),
                average_salary=int(average_salary)
            ))

        return final_summary_list

    def get_payroll_stats_for_month(self, year: int, month: int) -> PayrollStats:
        """Calculates the top KPI stats for a specific month."""
        with self.UsersSession() as u_session, self.PayrollSession() as p_session, self.InvoicesSession() as i_session:
            all_users = self._repo.get_all_employees(u_session)
            invoices_this_month = self._repo.get_total_invoices_for_month(i_session, year, month)

            total_employees = len(all_users)
            total_payroll = 0

            for user in all_users:
                profile = self._repo.get_employee_payroll_profile(p_session, user.id)
                if profile:
                    if profile.payment_type == 'Fixed':
                        total_payroll += profile.custom_base_salary or 0
                    else:  # Commission
                        if user.role == 'translator':
                            translator_revenue = sum(inv.total_translation_price for inv in invoices_this_month if
                                                     inv.translator == user.user_profile.full_name)
                            total_payroll += translator_revenue * profile.commission_rate
                        elif user.role in ['clerk', 'accountant']:
                            clerk_invoices = sum(1 for inv in invoices_this_month if inv.username == user.username)
                            total_payroll += clerk_invoices * profile.per_invoice_rate

            average_salary = total_payroll / total_employees if total_employees > 0 else 0

            return PayrollStats(total_employees, int(total_payroll), int(average_salary))
