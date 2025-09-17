# features/Workspace/workspace_factory.py

from features.Workspace.workspace_repo import ChatRepository, UserRepository
from features.Workspace.workspace_logic import ChatLogic
from features.Workspace.workspace_view import ChatView
from features.Workspace.workspace_controller import ChatController
from server.client import ChatClient


class WorkspaceFactory:
    """
    Factory class to create and assemble the entire workspace module.
    """
    @staticmethod
    def create(session_provider, current_user_id: int, broker_host: str, parent=None) -> ChatController:
        """
        Factory function to create and assemble the entire chat module.

        Args:
            session_provider: The application's central session provider instance.
            current_user_id: The ID of the user currently logged into the application.
            broker_host:
            parent:

        Returns:
            A fully initialized and ready-to-use ChatController.
        """
        # 1. Instantiate the stateless repository
        chat_repository = ChatRepository()
        user_repository = UserRepository()
        chat_client = ChatClient(host=broker_host)

        # 2. Instantiate the _logic layer, injecting the repository and session provider
        chat_logic = ChatLogic(user_repository=user_repository,
                               chat_repository=chat_repository,
                               client=chat_client,
                               session_provider=session_provider)

        # 3. Instantiate the _view, providing the current user's ID for UI purposes
        chat_view = ChatView(current_user_id=current_user_id, parent=parent)

        # 4. Instantiate the controller, injecting the _logic and the _view
        chat_controller = ChatController(
            logic=chat_logic,
            view=chat_view,
            current_user_id=current_user_id,
            client=chat_client
        )

        # 5. Perform the initial data load to populate the UI
        # This is a critical step to make the feature usable as soon as it's displayed
        chat_controller.perform_initial_load()

        # 6. Return the fully assembled controller
        return chat_controller


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    from core.database_init import DatabaseInitializer
    from core.database_seeder import DatabaseSeeder
    from config.config import DATABASE_PATHS

    app = QApplication(sys.argv)

    # 1. Initialize databases
    initializer = DatabaseInitializer()
    session_provider = initializer.setup_file_databases(DATABASE_PATHS)

    # 2. Seed (optional – dev/test mode)
    seeder = DatabaseSeeder(session_provider)
    seeder.seed_initial_data()

    # 3. Use factory
    controller = WorkspaceFactory.create(session_provider=session_provider, current_user_id=1)

    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
