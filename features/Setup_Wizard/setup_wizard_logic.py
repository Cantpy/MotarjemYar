# features/Setup_Wizard/setup_wizard_logic.py

# CHANGE: AdminProfileDTO removed
from features.Setup_Wizard.setup_wizard_models import (WizardStep, LicenseDTO, TranslationOfficeDTO, AdminUserDTO)
from features.Setup_Wizard.setup_wizard_repo import SetupWizardRepository
from shared.session_provider import ManagedSessionProvider


class SetupWizardLogic:
    """Business logic for the first-time setup wizard."""

    def __init__(self, repo: SetupWizardRepository,
                 user_db_session: ManagedSessionProvider,
                 license_db_session: ManagedSessionProvider):
        self._repo = repo
        self._user_db_session = user_db_session
        self._license_db_session = license_db_session
        self._validated_license_key: str | None = None

    def _get_license_details_from_rules(self, license_key: str) -> dict | None:
        """
        A local license validation rule engine.
        It checks the key against predefined rules and returns the license details.
        THIS is where you define your business logic for different license tiers.
        """
        key_upper = license_key.upper()  # Make it case-insensitive

        if "FREELANCER" in key_upper:
            return {
                "license_key": license_key, "app_version": "freelancer",
                "max_admins": 1, "max_translators": 1, "max_clerks": 1, "max_accountants": 1
            }
        if "OFFICE" in key_upper:
            return {
                "license_key": license_key, "app_version": "office",
                "max_admins": 2, "max_translators": 10, "max_clerks": 5, "max_accountants": 2
            }
        if "ENTERPRISE" in key_upper:
            return {
                "license_key": license_key, "app_version": "enterprise",
                "max_admins": 10, "max_translators": 100, "max_clerks": 50, "max_accountants": 20
            }

        # If the key matches none of the rules, it's invalid.
        return None

    def get_next_step(self) -> WizardStep:
        """Determines which wizard step should be shown next."""
        with self._license_db_session() as session:
            if not self._repo.is_license_present(session):
                return WizardStep.LICENSE

        with self._user_db_session() as session:
            if not self._repo.is_office_present(session):
                return WizardStep.TRANSLATION_OFFICE
            if not self._repo.is_admin_present(session):
                return WizardStep.ADMIN_USER

        return WizardStep.COMPLETED

    def process_license_step(self, license_dto: LicenseDTO) -> None:
        """Validates a license key using local rules and saves the full details."""
        # 1. Use the local validation engine as the source of truth.
        license_details = self._get_license_details_from_rules(license_dto.license_key)

        # 2. If the rules didn't return anything, the key is invalid.
        if not license_details:
            raise ValueError("کلید لایسنس وارد شده معتبر نمی باشد.")

        # 3. If valid, pass the complete dictionary to the repository.
        with self._license_db_session() as session:
            self._repo.save_license(session, license_details)

        # 4. Cache the key for the next step (e.g., to link the office to it).
        self._validated_license_key = license_dto.license_key

    def process_office_step(self, office_dto: TranslationOfficeDTO) -> None:
        """Validates and saves translation office data."""
        # --- Add validation for mandatory fields ---
        if not office_dto.name:
            raise ValueError("نام دفتر نمی‌تواند خالی باشد. لطفا این فیلد را پر کنید.")

        if not self._validated_license_key:
            print(f'process office step error: license key is not valid')
            raise RuntimeError("License key has not been validated.")

        with self._user_db_session() as session:
            print(f'saving data to the database under key: {self._validated_license_key}')
            self._repo.save_translation_office(session, office_dto, self._validated_license_key)

    # CHANGE: Simplified method signature and logic.
    def process_admin_and_profile_step(self, user_dto: AdminUserDTO) -> None:
        """Validates and saves the admin user."""
        # CHANGE: Added display_name to the validation check.
        if not user_dto.username or not user_dto.display_name or len(user_dto.password) < 8:
            raise ValueError("نام کاربری و نام نمایشی نمی‌تواند خالی باشد و رمز عبور باید حداقل ۸ کاراکتر باشد.")

        # CHANGE: Removed payroll_session from the context manager.
        with self._user_db_session() as user_session:
            # CHANGE: Call the new, simplified repository method.
            self._repo.save_admin_user(user_session, user_dto)
