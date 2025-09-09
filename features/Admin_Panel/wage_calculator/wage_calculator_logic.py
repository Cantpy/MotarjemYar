# Admin_Panel/wage_calculator/wage_calculator_logic.py

import uuid
import jdatetime
from datetime import timedelta
from decimal import Decimal, getcontext

from features.Admin_Panel.wage_calculator.wage_calculator_models import (PayrollRunEmployee, PayslipData,
                                                                         PayrollComponent, EmployeeInfo)
from features.Admin_Panel.wage_calculator.wage_calculator_repo import WageCalculatorRepository
from shared.orm_models.payroll_models import PayrollRecordModel, PayrollComponentDetailModel, TaxBracketModel
from shared.session_provider import SessionProvider

getcontext().prec = 18


class WageCalculatorLogic:
    def __init__(self, repository: WageCalculatorRepository, session_provider: SessionProvider):
        self._repo = repository
        self._session_provider = session_provider

    def get_employee_list(self) -> list[EmployeeInfo]:
        """Gets a simple list of employees for the UI to display in a dropdown."""
        with self._session_provider.payroll() as session:
            employees = self._repo.get_all_active_employees(session)
            return [
                EmployeeInfo(
                    employee_id=emp.employee_id,
                    full_name=f"{emp.first_name} {emp.last_name}",
                    payment_type=emp.payroll_profile.payment_type if emp.payroll_profile else 'N/A'
                ) for emp in employees
            ]

    def get_payroll_run_summary(self, year: int, month: int) -> list[PayrollRunEmployee]:
        """Fetches the summary of a pay run for the main table."""
        start_date, end_date = self._get_jalali_month_range(year, month)
        with self._session_provider.payroll() as session:
            records = self._repo.get_payroll_run_for_period(session, start_date, end_date)
            return [
                PayrollRunEmployee(
                    payroll_id=rec.payroll_id, employee_id=rec.employee_id,
                    full_name=f"{rec.employee.first_name} {rec.employee.last_name}",
                    gross_income=rec.gross_income_tomans, net_income=rec.net_income_tomans,
                    status=rec.status
                ) for rec in records
            ]

    def get_payslip_data_for_preview(self, payroll_id: str) -> PayslipData:
        """
        Fetches a saved PayrollRecord and converts it into a clean PayslipData DTO
        for the preview dialog to display.
        """
        with self._session_provider.payroll() as session:
            record = self._repo.get_detailed_payslip_by_id(session, payroll_id)
            if not record:
                raise ValueError(f"فیش حقوقی با شناسه {payroll_id} یافت نشد.")

            # Sort components by type (Earnings first) and then by name
            sorted_details = sorted(record.component_details,
                                    key=lambda d: (d.salary_component.type, d.salary_component.name))

            components = [
                PayrollComponent(
                    name=detail.salary_component.name,
                    type=detail.salary_component.type,
                    amount=detail.amount_tomans
                ) for detail in sorted_details
            ]

            return PayslipData(
                payroll_id=record.payroll_id,
                employee_name=f"{record.employee.first_name} {record.employee.last_name}",
                employee_national_id=record.employee.national_id,
                pay_period_str=f"{jdatetime.date.fromgregorian(date=record.pay_period_start_date):%Y/%m/%d} تا {jdatetime.date.fromgregorian(date=record.pay_period_end_date):%Y/%m/%d}",
                gross_income=record.gross_income_tomans,
                total_deductions=record.total_deductions_tomans,
                net_income=record.net_income_tomans,
                components=components
            )

    def execute_pay_run(self, year: int, month: int, overtime_map: dict):
        """Calculates and saves payroll for ALL employees for the given period."""
        start_date, end_date = self._get_jalali_month_range(year, month)

        with self._session_provider.payroll() as p_session, self._session_provider.invoices() as i_session:
            employees = self._repo.get_all_active_employees(p_session)
            constants = self._repo.get_system_constants(p_session, year)
            tax_brackets = self._repo.get_tax_brackets(p_session, year)
            salary_components = self._repo.get_salary_components_map(p_session)

            new_records = []
            for emp in employees:
                if not emp.payroll_profile: continue

                overtime_hours = Decimal(overtime_map.get(emp.employee_id, 0.0))
                record = self._calculate_single_payslip(emp, start_date, end_date, overtime_hours, constants,
                                                        tax_brackets, salary_components, i_session)
                if record:
                    new_records.append(record)

            if new_records:
                self._repo.save_payroll_records_batch(p_session, new_records)

    def _calculate_single_payslip(self, employee, start_date, end_date, overtime_hours, constants, tax_brackets,
                                  salary_components, i_session) -> PayrollRecordModel:
        profile = employee.payroll_profile
        calculated_components = {}
        working_days = (end_date - start_date).days + 1

        if profile.payment_type in ['Full-time', 'Part-time']:
            base_daily_wage = max(profile.custom_daily_payment_rials or 0, constants.get('MIN_DAILY_WAGE_RIAL', 0))
            base_salary = base_daily_wage * Decimal(working_days)
            calculated_components['Basic Salary'] = base_salary

            hourly_wage = base_daily_wage / Decimal('7.33')
            overtime_pay = overtime_hours * hourly_wage * (constants.get('OVERTIME_RATE_PCT', Decimal('0.4')) + 1)
            calculated_components['Overtime Pay'] = overtime_pay

            calculated_components['Housing Allowance'] = (constants.get('HOUSING_ALLOWANCE_RIAL',
                                                                        0) / 30) * working_days
            calculated_components['Groceries Allowance'] = (constants.get('GROCERIES_ALLOWANCE_RIAL',
                                                                          0) / 30) * working_days
            children_pay = profile.children_count * (
                        (constants.get('CHILDREN_ALLOWANCE_PER_CHILD_RIAL', 0) / 30) * working_days)
            calculated_components['Children Allowance'] = children_pay

        elif profile.payment_type == 'Commission':
            commission_base = self._repo.get_translator_performance_rials(i_session,
                                                                          f"{employee.first_name} {employee.last_name}",
                                                                          start_date, end_date)
            commission_earning = commission_base * profile.commission_rate
            calculated_components['Commission'] = commission_earning

        insurance_base, gross_income = Decimal(0), Decimal(0)
        for name, amount in calculated_components.items():
            comp_def = salary_components[name]
            if comp_def.type == 'Earning':
                gross_income += amount
                if comp_def.is_base_for_insurance_calculation:
                    insurance_base += amount

        insurance_deduction = insurance_base * constants.get('INSURANCE_EMP_RATE_PCT', Decimal('0.07'))
        calculated_components['Employee Insurance'] = insurance_deduction

        taxable_income = gross_income - insurance_deduction
        annualized_taxable_income = taxable_income * 12
        annual_tax = self._calculate_progressive_tax(annualized_taxable_income, tax_brackets)
        monthly_tax = annual_tax / 12
        calculated_components['Income Tax'] = monthly_tax

        total_deductions = insurance_deduction + monthly_tax
        net_income = gross_income - total_deductions

        record = PayrollRecordModel(
            payroll_id=str(uuid.uuid4()), employee_id=employee.employee_id,
            pay_period_start_date=start_date, pay_period_end_date=end_date,
            base_working_days_in_period=working_days, overtime_hours_in_period=overtime_hours,
            gross_income_tomans=gross_income / 10, total_deductions_tomans=total_deductions / 10,
            taxable_income_tomans=taxable_income / 10, calculated_tax_tomans=monthly_tax / 10,
            calculated_insurance_tomans=insurance_deduction / 10, net_income_tomans=net_income / 10
        )
        record.component_details = [
            PayrollComponentDetailModel(component_id=salary_components[name].component_id, amount_tomans=amount / 10)
            for name, amount in calculated_components.items() if amount != 0]
        return record

    def _calculate_progressive_tax(self, annual_income_rials: Decimal, brackets: list[TaxBracketModel]) -> Decimal:
        tax, remaining_income = Decimal(0), annual_income_rials
        for bracket in brackets:
            if remaining_income <= 0: break
            lower = bracket.lower_bound
            upper = bracket.upper_bound if bracket.upper_bound is not None else Decimal('Infinity')
            if remaining_income > lower:
                taxable_in_this_bracket = min(remaining_income, upper) - lower
                tax += taxable_in_this_bracket * bracket.rate
        return tax

    def _get_jalali_month_range(self, year, month):
        """
        Returns the start and end Gregorian dates for the given Jalali month and year.
        """
        start_j = jdatetime.date(year, month, 1)
        end_j = (start_j + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        return start_j.togregorian(), end_j.togregorian()
