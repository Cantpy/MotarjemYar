"""
Centralized and production-ready database seeder for all engines.
Handles users, services, payroll, and configuration constants.
"""

from __future__ import annotations

import bcrypt
from decimal import Decimal
from typing import Dict
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, Session

from shared.orm_models.users_models import UsersModel
from shared.orm_models.services_models import FixedPricesModel, ServicesModel
from shared.orm_models.payroll_models import SystemConstantModel, SalaryComponentModel, TaxBracketModel
from shared import get_resource_path
from shared.session_provider import ManagedSessionProvider

# Application-specific imports
from features.Services.tab_manager.tab_manager_logic import ExcelImportLogic
from features.Services.documents.documents_logic import ServicesLogic
from features.Services.documents.documents_repo import ServiceRepository
from features.Services.other_services.other_services_logic import OtherServicesLogic
from features.Services.other_services.other_services_repo import OtherServicesRepository


class DatabaseSeeder:
    """Orchestrates seeding of all application databases."""

    def __init__(self, engines: Dict[str, Engine]):
        self.engines = engines

    # ------------------------------------------------------------------
    # PUBLIC INTERFACE
    # ------------------------------------------------------------------

    def seed_initial_data(self, is_demo_mode: bool = False) -> None:
        """Seeds all initial data across subsystems."""
        print("🚀 Starting initial database seeding...")

        if is_demo_mode:
            self._seed_default_user()

        self._seed_fixed_prices()
        self._seed_services_from_excel()
        self._seed_payroll_system_constants()
        self._seed_salary_components()
        self._seed_tax_brackets()

        print("✅ Data seeding complete.")

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _get_session(self, engine_name: str) -> Session | None:
        """Get a new SQLAlchemy session for the given engine name."""
        engine = self.engines.get(engine_name)
        if not engine:
            print(f"⚠️ Engine '{engine_name}' not found. Skipping.")
            return None
        return sessionmaker(bind=engine)()

    def _safe_commit(self, session: Session) -> None:
        try:
            session.commit()
        except Exception as e:
            print(f"❌ Commit failed: {e}")
            session.rollback()

    # ------------------------------------------------------------------
    # USER SEEDING
    # ------------------------------------------------------------------

    def _seed_default_user(self) -> None:
        """Create a default demo user if none exists."""
        print("🧪 Seeding default demo user (testuser)...")

        session = self._get_session("users")
        if not session:
            return

        try:
            if session.query(UsersModel).filter_by(username="testuser").first():
                print("⚙️ Default user already exists.")
                return

            password = "password123"
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

            user = UsersModel(
                employee_id="EMP-DEMO-0001",
                username="testuser",
                password_hash=hashed,
                role="translator",
                active=1,
                display_name="کاربر آزمایشی",
                avatar_path=None,
            )

            session.add(user)
            self._safe_commit(session)
            print("✅ Default demo user created.")
        finally:
            session.close()

    # ------------------------------------------------------------------
    # SERVICES SEEDING
    # ------------------------------------------------------------------

    def _seed_services_from_excel(self) -> None:
        """Seed the services DB from an Excel file if empty."""
        print("📦 Checking Services.db for seeding requirements...")

        session = self._get_session("services")
        if not session:
            return

        try:
            if session.query(ServicesModel).count() > 0:
                print("⚙️ Services already populated. Skipping Excel import.")
                return

            excel_path = get_resource_path("assets", "services_datasheet.xlsx")
            if not excel_path.exists():
                print(f"⚠️ Excel file not found at {excel_path}")
                return

            managed_engine = ManagedSessionProvider(self.engines["services"])
            services_logic = ServicesLogic(ServiceRepository(), managed_engine)
            other_services_logic = OtherServicesLogic(OtherServicesRepository(), managed_engine)
            importer = ExcelImportLogic(services_logic, other_services_logic)

            print(f"📊 Importing services from: {excel_path}")
            results = importer.import_from_excel_file(str(excel_path))

            for sheet, result in results.items():
                status = "✅" if result.failed_count == 0 else "⚠️"
                print(f"{status} {sheet}: {result.success_count} rows, {result.failed_count} failed.")

        except Exception as e:
            print(f"❌ Error during Excel import: {e}")
        finally:
            session.close()

    def _seed_fixed_prices(self) -> None:
        """Seed fixed service prices."""
        print("💰 Seeding fixed prices...")

        session = self._get_session("services")
        if not session:
            return

        prices = [
            ("کپی برابر اصل", 5000),
            ("ثبت در سامانه", 30000),
            ("مهر دادگستری", 150000),
            ("مهر امور خارجه", 15000),
            ("نسخه اضافی", 12000),
        ]

        try:
            existing = {fp.name for fp in session.query(FixedPricesModel.name).all()}
            added = 0
            for name, price in prices:
                if name not in existing:
                    session.add(FixedPricesModel(name=name, price=price))
                    added += 1

            if added:
                self._safe_commit(session)
                print(f"✅ Added {added} fixed prices.")
            else:
                print("⚙️ No new fixed prices to add.")
        finally:
            session.close()

    # ------------------------------------------------------------------
    # PAYROLL SEEDING
    # ------------------------------------------------------------------

    def _seed_payroll_system_constants(self) -> None:
        """Seed government-mandated constants and system configuration values."""
        print("🏛️ Seeding payroll system constants...")

        session = self._get_session("payroll")
        if not session:
            return

        try:
            if session.query(SystemConstantModel).count() > 0:
                print("⚙️ System constants already exist. Skipping.")
                return

            constants = [
                # Year 1404 configuration
                SystemConstantModel(
                    year=1404,
                    code="MIN_MONTHLY_WAGE_RIAL_1404",
                    name="حداقل دستمزد ماهانه (ریال)",
                    value=Decimal("111200000"),
                    unit="ریال",
                    description="حداقل حقوق پایه مصوب سال 1404 بر اساس وزارت کار"
                ),
                SystemConstantModel(
                    year=1404,
                    code="SSO_EMPLOYEE_PCT",
                    name="درصد سهم بیمه کارگر",
                    value=Decimal("7.0"),
                    unit="percent",
                    description="درصد سهم بیمه تامین اجتماعی برای کارگر"
                ),
                SystemConstantModel(
                    year=1404,
                    code="SSO_EMPLOYER_PCT",
                    name="درصد سهم بیمه کارفرما",
                    value=Decimal("23.0"),
                    unit="percent",
                    description="درصد سهم بیمه تامین اجتماعی برای کارفرما"
                ),
                SystemConstantModel(
                    year=1404,
                    code="SSO_BASE_CEILING_RIAL_1404",
                    name="سقف دستمزد مشمول بیمه",
                    value=Decimal("548500000"),
                    unit="ریال",
                    description="حداکثر پایه حقوق مشمول بیمه تامین اجتماعی در سال 1404"
                ),
            ]

            session.add_all(constants)
            self._safe_commit(session)
            print("✅ Payroll system constants seeded.")
        finally:
            session.close()

    def _seed_salary_components(self) -> None:
        """Seed standard earning and deduction components for payroll slips."""
        print("🧾 Seeding salary components...")

        session = self._get_session("payroll")
        if not session:
            return

        try:
            if session.query(SalaryComponentModel).count() > 0:
                print("⚙️ Salary components already exist. Skipping.")
                return

            components = [
                SalaryComponentModel(
                    name="base_salary",
                    display_name="حقوق پایه",
                    type="Earning",
                    is_taxable_for_income_tax=True,
                    is_deductible_for_taxable_income=False,
                    is_base_for_insurance_calculation=True
                ),
                SalaryComponentModel(
                    name="overtime_pay",
                    display_name="اضافه‌کار",
                    type="Earning",
                    is_taxable_for_income_tax=True,
                    is_deductible_for_taxable_income=False,
                    is_base_for_insurance_calculation=True
                ),
                SalaryComponentModel(
                    name="transport_allowance",
                    display_name="حق ایاب و ذهاب",
                    type="Earning",
                    is_taxable_for_income_tax=False,
                    is_deductible_for_taxable_income=False,
                    is_base_for_insurance_calculation=False
                ),
                SalaryComponentModel(
                    name="meal_allowance",
                    display_name="بن کارگری / حق خواروبار",
                    type="Earning",
                    is_taxable_for_income_tax=False,
                    is_deductible_for_taxable_income=False,
                    is_base_for_insurance_calculation=False
                ),
                SalaryComponentModel(
                    name="income_tax",
                    display_name="مالیات بر درآمد",
                    type="Deduction",
                    is_taxable_for_income_tax=False,
                    is_deductible_for_taxable_income=True,
                    is_base_for_insurance_calculation=False
                ),
                SalaryComponentModel(
                    name="insurance_contribution",
                    display_name="حق بیمه",
                    type="Deduction",
                    is_taxable_for_income_tax=False,
                    is_deductible_for_taxable_income=True,
                    is_base_for_insurance_calculation=False
                ),
            ]

            session.add_all(components)
            self._safe_commit(session)
            print("✅ Salary components seeded.")
        finally:
            session.close()

    def _seed_tax_brackets(self) -> None:
        """Seed progressive income tax brackets for the year 1404."""
        print("📈 Seeding tax brackets...")

        session = self._get_session("payroll")
        if not session:
            return

        try:
            if session.query(TaxBracketModel).count() > 0:
                print("⚙️ Tax brackets already exist. Skipping.")
                return

            brackets = [
                TaxBracketModel(
                    year=1404,
                    lower_bound_rials=Decimal("0"),
                    upper_bound_rials=Decimal("720000000"),
                    rate=Decimal("0.10"),
                ),
                TaxBracketModel(
                    year=1404,
                    lower_bound_rials=Decimal("720000001"),
                    upper_bound_rials=Decimal("1200000000"),
                    rate=Decimal("0.15"),
                ),
                TaxBracketModel(
                    year=1404,
                    lower_bound_rials=Decimal("1200000001"),
                    upper_bound_rials=None,  # No upper limit
                    rate=Decimal("0.20"),
                ),
            ]

            session.add_all(brackets)
            self._safe_commit(session)
            print("✅ Tax brackets seeded.")
        finally:
            session.close()
