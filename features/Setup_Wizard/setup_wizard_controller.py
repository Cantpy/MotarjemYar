# features/Setup_Wizard/setup_wizard_controller.py

from features.Setup_Wizard.setup_wizard_logic import SetupWizardLogic
from features.Setup_Wizard.setup_wizard_view import SetupWizardView
from features.Setup_Wizard.setup_wizard_models import LicenseDTO, TranslationOfficeDTO, AdminUserDTO

from shared import show_information_message_box


class SetupWizardController:
    """
    Controller for the setup wizard.
    - Connects View signals to its slots.
    - Calls Logic to perform business operations.
    - Updates the View based on the Logic's responses.
    """
    def __init__(self, logic: SetupWizardLogic, view: SetupWizardView):
        self._logic = logic
        self._view = view
        self._view.register_validators(
            license_validator=self._validate_and_process_license,
            office_validator=self._validate_and_process_office,
            admin_validator=self._validate_and_process_admin
        )

    # ... (get_view and prepare_wizard are unchanged) ...
    def get_view(self) -> SetupWizardView:
        """Exposes the view widget."""
        return self._view

    def prepare_wizard(self) -> bool:
        """
        Determines the correct starting step and prepares the view.
        Returns True if the wizard needs to be run, False otherwise.
        """
        next_step = self._logic.get_next_step()
        if next_step is not next_step.COMPLETED:
            # Calls the corrected, non-showing view method
            self._view.prepare_to_show_step(next_step)
            return True
        return False

    # ... (_validate_and_process_license and _validate_and_process_office are unchanged) ...
    def _validate_and_process_license(self, dto: LicenseDTO) -> bool:
        """Synchronous validation function for the License Page."""
        try:
            self._logic.process_license_step(dto)
            return True
        except ValueError as e:
            self._view.show_error_on_page(self._view.license_page, str(e))
            return False
        except Exception as e:
            print(f'validate and process license error: {e}')
            self._view.show_error_on_page(self._view.license_page, f"یک خطای پیشبینی نشده رخ داد: {e}")
            return False

    def _validate_and_process_office(self, dto: TranslationOfficeDTO) -> bool:
        """Synchronous validation function for the Office Page."""
        try:
            self._logic.process_office_step(dto)
            return True
        except Exception as e:
            print(f'validate and process office error: {e}')
            self._view.show_error_on_page(self._view.office_page, f"یک خطای پیشبینی نشده رخ داد: {e}")
            return False

    # CHANGE: Simplified the method signature.
    def _validate_and_process_admin(self, user_dto: AdminUserDTO) -> bool:
        """Synchronous validation function for the Admin Page."""
        try:
            # CHANGE: The logic method is now called with only the user_dto.
            self._logic.process_admin_and_profile_step(user_dto)
            return True
        except ValueError as e:
            print(f'validate and process admin error: {e}')
            self._view.show_error_on_page(self._view.admin_page, str(e))
            return False
        except Exception as e:
            print(f'validate and process admin unexpected error: {e}')
            self._view.show_error_on_page(self._view.admin_page, f"یک خطای پیشبینی نشده رخ داد: {e}")
            return False

    def _on_wizard_finished(self):
        show_information_message_box(self._view,
                                     "تکمیل راه‌اندازی",
                                     "راه‌اندازی مترجم‌یار با موفقیت انجام شد.")
