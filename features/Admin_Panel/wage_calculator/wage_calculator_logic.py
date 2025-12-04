# features/Admin_Panel/wage_calculator/wage_calculator_logic.py

import uuid
import jdatetime
from decimal import Decimal, getcontext
from datetime import datetime, timezone

from features.Admin_Panel.wage_calculator.wage_calculator_models import (PayrollRunEmployee, PayslipData,
                                                                         PayrollComponent, EmployeeInfo,
                                                                         TranslationOffice, CommissionDetail)
from features.Admin_Panel.wage_calculator.wage_calculator_repo import WageCalculatorRepository
from shared.orm_models.payroll_models import (PayrollRecordModel, PayrollComponentDetailModel, TaxBracketModel,
                                              EmploymentType, PayrollAuditLogModel)

from shared.session_provider import ManagedSessionProvider, SessionManager

getcontext().prec = 28

# Dictionary to map database statuses to display statuses
STATUS_TRANSLATIONS = {
    'Draft': 'پیش‌نویس',
    'Finalized': 'نهایی شده',
    'Paid': 'پرداخت شده'
}


class WageCalculatorLogic:
    def __init__(self, repository: WageCalculatorRepository,
                 payroll_engine: ManagedSessionProvider,
                 business_engine: ManagedSessionProvider):
        self._repo = repository
        self._payroll_session = payroll_engine
        self._business_session = business_engine

    def get_employee_list(self) -> list[EmployeeInfo]:
        """Gets a simple list of employees for the UI to display in a dropdown."""
        with self._payroll_session() as session:
            employees = self._repo.payroll_repo.get_all_active_employees(session)
            return [
                EmployeeInfo(
                    employee_id=emp.employee_id,
                    full_name=f"{emp.first_name} {emp.last_name}",
                ) for emp in employees
            ]

    def get_payroll_run_summary(self, year: int, month: int) -> list[PayrollRunEmployee]:
        """
        Fetches a summary for the main table, converting Rials from DB to Tomans for UI
        and translating the status for display.
        """
        start_date, end_date = self._get_jalali_month_range(year, month)
        with self._payroll_session() as session:
            all_employees = self._repo.payroll_repo.get_all_active_employees(session)
            records_for_period = self._repo.payroll_repo.get_payroll_run_for_period(session, start_date, end_date)
            records_map = {rec.employee_id: rec for rec in records_for_period}

            summary_list = []
            for emp in all_employees:
                record = records_map.get(emp.employee_id)
                if record:
                    # --- FIX: Translate status from English (DB) to Persian (UI) ---
                    display_status = STATUS_TRANSLATIONS.get(record.status, record.status)
                    summary_list.append(PayrollRunEmployee(
                        payroll_id=record.payroll_id, employee_id=record.employee_id,
                        full_name=f"{record.employee.first_name} {record.employee.last_name}",
                        gross_income=record.gross_income_rials / 10,
                        net_income=record.net_income_rials / 10,
                        status=display_status
                    ))
                else:
                    summary_list.append(PayrollRunEmployee(
                        payroll_id=None, employee_id=emp.employee_id,
                        full_name=f"{emp.first_name} {emp.last_name}",
                        gross_income=Decimal('0'), net_income=Decimal('0'),
                        status="محاسبه نشده"
                    ))
            return summary_list

    def get_payslip_data_for_preview(self, payroll_id: str) -> PayslipData:
        """
        Fetches a saved PayrollRecord and converts it into a clean PayslipData DTO.
        """
        with self._payroll_session() as session:
            record = self._repo.payroll_repo.get_detailed_payslip_by_id(session, payroll_id)
            if not record:
                raise ValueError(f"فیش حقوقی با شناسه {payroll_id} یافت نشد.")
            return self._convert_record_to_payslip_data(record)

    def calculate_payslip_for_preview(self, inputs: dict) -> PayslipData:
        """
        Calculates a payslip and returns the DTO for preview without saving.
        """

        employee_id = inputs['employee_id']
        start_date = inputs['start_date']
        end_date = inputs['end_date']
        # --- MODIFIED: Rename for clarity, will be used as total hours for part-time ---
        work_metric = Decimal(inputs.get('overtime_hours', 0.0))
        year = jdatetime.date.fromgregorian(date=start_date).year

        with (self._payroll_session() as p_session,
              self._business_session() as b_session):
            employee = self._repo.payroll_repo.get_employee_by_id(p_session, employee_id)
            if not employee or not employee.payroll_profile:
                raise ValueError(f"پروفایل حقوقی برای کارمند با شناسه {employee_id} یافت نشد.")

            constants = self._repo.payroll_repo.get_system_constants(p_session, year)
            tax_brackets = self._repo.payroll_repo.get_tax_brackets(p_session, year)
            salary_components_map = self._repo.payroll_repo.get_salary_components_map(p_session)
            translation_office_info = self._repo.users_repo.get_translation_office_info(b_session)

            calculated_data = self._calculate_single_payslip(
                employee, start_date, end_date, work_metric, constants,
                tax_brackets, salary_components_map, b_session
            )

            components = [
                PayrollComponent(
                    name=name,
                    display_name=salary_components_map[name].display_name,
                    type=salary_components_map[name].type,
                    amount=amount / 10
                )
                for name, amount in calculated_data['components'].items() if amount != 0
            ]

            if isinstance(translation_office_info, list):
                office_model = translation_office_info[0] if translation_office_info else None
            else:
                office_model = translation_office_info

            tr = None
            if office_model:
                tr = TranslationOffice(
                    name=office_model.name,
                    registration=office_model.reg_no or "",
                    representative=office_model.representative or "",
                    manager=office_model.manager or "",
                    address=office_model.address or "",
                    phone=office_model.phone or "",
                )

            user_data = SessionManager().get_session()

            # --- MODIFIED: Populate new DTO fields ---
            return PayslipData(
                payroll_id=calculated_data['payroll_id'],
                employee_code=employee.employee_code,
                employee_name=f"{employee.first_name} {employee.last_name}",
                employee_national_id=employee.national_id,
                pay_period_str=(f"{jdatetime.date.fromgregorian(date=start_date):%Y/%m/%d} تا "
                                f"{jdatetime.date.fromgregorian(date=end_date):%Y/%m/%d}"),
                gross_income=calculated_data['gross_income'] / 10,
                total_deductions=calculated_data['total_deductions'] / 10,
                net_income=calculated_data['net_income'] / 10,
                components=components,
                issuer=user_data.full_name or user_data.user_id,
                translation_office=tr,
                employment_type=employee.payroll_profile.employment_type,
                hours_worked=calculated_data.get('hours_worked'),
                commissions=calculated_data.get('commission_details', []),
                _raw_data_for_save={
                    'employee_id': employee_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'overtime': work_metric,
                    'taxable_income': calculated_data['taxable_income'],
                    'tax': calculated_data['tax'],
                    'insurance': calculated_data['insurance'],
                },
            )

    def audit_payroll(self, payslip_data: PayslipData):
        """Logs an audit entry for payroll processing."""
        user_info = SessionManager().get_session()
        user_name = user_info.full_name or user_info.user_id
        with self._payroll_session() as session:
            audit_log = PayrollAuditLogModel(
                entity_type='payslip',
                entity_id=payslip_data.payroll_id,
                action='create',
                performed_by=user_name,
                performed_at=datetime.now(timezone.utc),
                details=f"Payslip created for {payslip_data.employee_name}"
            )
            session.add(audit_log)
            session.commit()

    def save_payslip_record(self, payslip_data: PayslipData):
        """Saves a payslip to the database, ensuring the status is in English for the DB constraint."""
        raw = payslip_data._raw_data_for_save
        with self._payroll_session() as session:
            salary_components = self._repo.payroll_repo.get_salary_components_map(session)

            record = PayrollRecordModel(
                payroll_id=payslip_data.payroll_id,
                employee_id=raw['employee_id'],
                pay_period_start_date=raw['start_date'],
                pay_period_end_date=raw['end_date'],
                base_working_hours_in_period=((raw['end_date'] - raw['start_date']).days + 1) * 8,
                overtime_hours_in_period=raw['overtime'],
                gross_income_rials=payslip_data.gross_income * 10,
                total_deductions_rials=payslip_data.total_deductions * 10,
                taxable_income_rials=raw['taxable_income'],
                calculated_tax_rials=raw['tax'],
                calculated_insurance_rials=raw['insurance'],
                net_income_rials=payslip_data.net_income * 10,
                # --- FIX: Revert to the English status required by the database CHECK constraint ---
                status='Finalized'
            )

            record.component_details = [
                PayrollComponentDetailModel(
                    component_id=salary_components[comp.name].component_id,
                    amount_rials=comp.amount * 10
                ) for comp in payslip_data.components
            ]

            session.add(record)
            session.commit()

    def _calculate_progressive_tax(self, annual_income_rials: Decimal, brackets: list[TaxBracketModel]) -> Decimal:
        """Corrected progressive tax calculation using proper column names."""
        tax = Decimal(0)
        income = annual_income_rials
        last_upper_bound = Decimal(0)

        for bracket in brackets:
            if income <= last_upper_bound:
                break

            lower = bracket.lower_bound_rials
            upper = bracket.upper_bound_rials if bracket.upper_bound_rials is not None else income

            taxable_in_bracket = min(income, upper) - lower
            if taxable_in_bracket < 0:
                taxable_in_bracket = 0

            tax += taxable_in_bracket * bracket.rate
            last_upper_bound = upper

        return tax

    def _convert_record_to_payslip_data(self, record: PayrollRecordModel) -> PayslipData:
        """Helper to convert an ORM model to a PayslipData DTO, handling Rials to Tomans conversion."""
        if not record:
            return None

        with self._business_session as session:
            translation_office_info = self._repo.users_repo.get_translation_office_info(session)

        if isinstance(translation_office_info, list):
            office_model = translation_office_info[0] if translation_office_info else None
        else:
            office_model = translation_office_info

        tr = None
        if office_model:
            tr = TranslationOffice(
                name=office_model.name,
                registration=office_model.reg_no or "",
                representative=office_model.representative or "",
                manager=office_model.manager or "",
                address=office_model.address or "",
                phone=office_model.phone or "",
            )

        sorted_details = sorted(record.component_details,
                                key=lambda d: (d.salary_component.type, d.salary_component.name))
        components = [
            PayrollComponent(
                name=detail.salary_component.name,
                type=detail.salary_component.type,
                display_name=detail.salary_component.display_name,
                amount=detail.amount_rials / 10
            ) for detail in sorted_details
        ]

        user_info = SessionManager().get_session()

        # Note: This is a simplified conversion. A full implementation would need to
        # rebuild commission/part-time data from other sources if it's not stored
        # directly in the payroll record. For now, we set the type.
        return PayslipData(
            payroll_id=record.payroll_id,
            employee_name=f"{record.employee.first_name} {record.employee.last_name}",
            employee_national_id=record.employee.national_id,
            employee_code=record.employee.employee_code,
            pay_period_str=f"{jdatetime.date.fromgregorian(date=record.pay_period_start_date):%Y/%m/%d}"
                           f" تا {jdatetime.date.fromgregorian(date=record.pay_period_end_date):%Y/%m/%d}",
            gross_income=record.gross_income_rials / 10,
            total_deductions=record.total_deductions_rials / 10,
            net_income=record.net_income_rials / 10,
            components=components,
            translation_office=tr,
            issuer=user_info.full_name or user_info.user_id,
            employment_type=record.employee.payroll_profile.employment_type
        )

    # --- MODIFIED: Renamed overtime_hours to work_metric and expanded logic ---
    def _calculate_single_payslip(self, employee, start_date, end_date, work_metric, constants, tax_brackets,
                                  salary_components, i_session) -> dict:
        """
        Unified salary calculation engine (Decimal-safe).
        """
        profile = employee.payroll_profile
        calculated_components = {}
        working_days = Decimal((end_date - start_date).days + 1)
        # --- NEW: Dictionary to hold extra data for the DTO ---
        extra_data = {}

        def D(value):
            if isinstance(value, Decimal):
                return value
            if value is None:
                return Decimal("0")
            return Decimal(str(value))

        if profile.employment_type == EmploymentType.FULL_TIME:
            base_daily_wage = max(
                D(profile.base_salary_rials),
                D(constants.get("MIN_DAILY_WAGE_RIAL", 0)),
            )
            base_salary = base_daily_wage * working_days
            calculated_components["Basic Salary"] = base_salary

            hourly_wage = base_daily_wage / D("7.33")
            overtime_pay = D(work_metric) * hourly_wage * (D(constants.get("OVERTIME_RATE_PCT", 0.4)) + 1)
            calculated_components["Overtime Pay"] = overtime_pay

            calculated_components["Housing Allowance"] = (D(constants.get("HOUSING_ALLOWANCE_RIAL", 0)) / D(
                30)) * working_days
            calculated_components["Groceries Allowance"] = (D(constants.get("GROCERIES_ALLOWANCE_RIAL", 0)) / D(
                30)) * working_days
            calculated_components["Children Allowance"] = (
                    D(profile.children_count) * (
                        (D(constants.get("CHILDREN_ALLOWANCE_PER_CHILD_RIAL", 0)) / D(30)) * working_days)
            )
        # --- MODIFIED: Implemented Part-Time logic ---
        elif profile.employment_type == EmploymentType.PART_TIME:
            hourly_rate = D(profile.hourly_rate_rials or constants.get("MIN_HOURLY_WAGE_RIAL", 0))
            total_hours = D(work_metric)
            base_salary = total_hours * hourly_rate
            calculated_components["BaseBusiness Hourly Salary"] = base_salary
            extra_data['hours_worked'] = total_hours

        # --- MODIFIED: Implemented Commission logic ---
        elif profile.employment_type == EmploymentType.COMMISSION:
            invoices = self._repo.invoices_repo.get_translator_invoices_for_period(
                i_session,
                f"{employee.first_name} {employee.last_name}",
                start_date,
                end_date,
            )
            commission_rate = D(profile.commission_rate_pct or 0)
            total_commission_earning = Decimal("0")
            commission_details = []

            for inv in invoices:
                # Invoice amounts are in Toman, convert to Rial for calculation
                total_translation_rials = D(inv.total_translation_price) * 10
                translator_share_rials = total_translation_rials * commission_rate
                total_commission_earning += translator_share_rials
                commission_details.append(
                    CommissionDetail(
                        invoice_number=inv.invoice_number,
                        customer_name=inv.name,
                        # Convert back to Toman for display
                        total_price=total_translation_rials / 10,
                        translator_share=translator_share_rials / 10
                    )
                )
            calculated_components["Commission"] = total_commission_earning
            extra_data['commission_details'] = commission_details

        else:
            print(f"employee id: {employee.employee_id}, employment type: {employee.payroll_profile.employment_type}")
            raise ValueError(f"شیوه پرداخت برای کارمند با شناسه {employee.employee_id} قابل شناسایی نیست.")

        insurance_base = Decimal("0")
        gross_income = Decimal("0")

        for name, amount in calculated_components.items():
            amount = D(amount)
            comp_def = salary_components.get(name)
            if comp_def and comp_def.type == "Earning":
                gross_income += amount
                if comp_def.is_base_for_insurance_calculation:
                    insurance_base += amount

        insurance_rate = D(constants.get("INSURANCE_EMP_RATE_PCT", 0.07))
        insurance_deduction = insurance_base * insurance_rate
        calculated_components["Employee Insurance"] = insurance_deduction

        taxable_income = gross_income - insurance_deduction
        annualized_taxable_income = taxable_income * D(12)
        annual_tax = self._calculate_progressive_tax(annualized_taxable_income, tax_brackets)
        monthly_tax = D(annual_tax) / D(12)
        calculated_components["Income Tax"] = monthly_tax

        total_deductions = insurance_deduction + monthly_tax
        net_income = gross_income - total_deductions

        employer_insurance = insurance_base * D(constants.get("INSURANCE_EMPLOYER_RATE_PCT", 0.20))
        unemployment_insurance = insurance_base * D(constants.get("UNEMPLOYMENT_INSURANCE_RATE_PCT", 0.03))
        total_employer_contribution = employer_insurance + unemployment_insurance

        calculated_components["Employer Insurance (20%)"] = employer_insurance
        calculated_components["Unemployment Insurance (3%)"] = unemployment_insurance

        # --- MODIFIED: Merge extra_data into the return dictionary ---
        return {
            "payroll_id": str(uuid.uuid4()),
            "gross_income": gross_income,
            "total_deductions": total_deductions,
            "net_income": net_income,
            "taxable_income": taxable_income,
            "tax": monthly_tax,
            "insurance": insurance_deduction,
            "employer_insurance": employer_insurance,
            "unemployment_insurance": unemployment_insurance,
            "employer_total_contribution": total_employer_contribution,
            "components": calculated_components,
            **extra_data
        }

    def _get_jalali_month_range(self, year, month):
        start_j = jdatetime.date(year, month, 1)
        # --- MODIFIED: More robust way to find the end of a Jalali month ---
        if month == 12 and not start_j.isleap():
            end_j = jdatetime.date(year, month, 29)
        elif month >= 7:
            end_j = jdatetime.date(year, month, 30)
        else:
            end_j = jdatetime.date(year, month, 31)

        return start_j.togregorian(), end_j.togregorian()
