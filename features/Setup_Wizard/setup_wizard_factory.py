# features/Setup_Wizard/setup_wizard_factory.py

from sqlalchemy.engine import Engine
from features.Setup_Wizard.setup_wizard_view import SetupWizardView
from features.Setup_Wizard.setup_wizard_controller import SetupWizardController
from features.Setup_Wizard.setup_wizard_logic import SetupWizardLogic
from features.Setup_Wizard.setup_wizard_repo import SetupWizardRepository
from shared.session_provider import ManagedSessionProvider  # Crucial utility


class SetupWizardFactory:
    """Factory for creating and wiring the Setup Wizard package."""

    @staticmethod
    def create(user_db_engine: Engine, license_db_engine: Engine, parent=None) -> SetupWizardController:
        """
        Creates a fully configured Setup Wizard module by assembling its components.
        """
        user_session = ManagedSessionProvider(engine=user_db_engine)
        license_session = ManagedSessionProvider(engine=license_db_engine)

        repo = SetupWizardRepository()
        logic = SetupWizardLogic(repo=repo, user_db_session=user_session, license_db_session=license_session)

        # --- Create the view first, but don't wire it yet ---
        view = SetupWizardView(parent=parent)

        # --- Create the controller, which will then wire itself to the view ---
        controller = SetupWizardController(logic=logic, view=view)

        return controller
