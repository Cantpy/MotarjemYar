# features/Workspace/workspace_factory.py

from sqlalchemy.engine import Engine

from features.Workspace.workspace_repo import ChatRepository, UserRepository
from features.Workspace.workspace_logic import ChatLogic
from features.Workspace.workspace_view import ChatView
from features.Workspace.workspace_controller import ChatController
from server.client import ChatClient

from shared.session_provider import ManagedSessionProvider


class WorkspaceFactory:
    """
    Factory class to create and assemble the entire workspace module.
    """
    @staticmethod
    def create(users_engine: Engine, workspace_engine: Engine,
               current_user_id: int, broker_host: str, parent=None) -> ChatController:
        """
        Factory function to create and assemble the entire chat module.

        Args:
            users_engine: SQLAlchemy Engine connected to the users database.
            workspace_engine: SQLAlchemy Engine connected to the workspace database.
            current_user_id: The ID of the user currently logged into the application.
            broker_host: The host address of the chat message broker.
            parent: Optional parent widget for the view.
        Returns:
            A fully initialized and ready-to-use ChatController.
        """
        users_session = ManagedSessionProvider(users_engine)
        workspace_session = ManagedSessionProvider(workspace_engine)

        chat_repository = ChatRepository()
        user_repository = UserRepository()
        chat_client = ChatClient(host=broker_host)

        # 2. Instantiate the _logic layer, injecting the _repository and session provider
        chat_logic = ChatLogic(user_repository=user_repository,
                               chat_repository=chat_repository,
                               client=chat_client,
                               users_engine=users_session,
                               workspace_engine=workspace_session)

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

    app = QApplication(sys.argv)

    # 1. We need ALL the engines for the MainWindow
    from core.database_init import DatabaseInitializer

    initializer = DatabaseInitializer()
    all_engines = initializer.setup_memory_databases()  # Use memory for testing

    # 2. We need a dummy username
    username_for_test = "testuser"

    # 3. Call the factory with the correct, full dictionary of engines
    controller = WorkspaceFactory.create(
        users_engine=all_engines.get('users'),
        workspace_engine=all_engines.get('workspace'),
        current_user_id=1,
        broker_host='localhost',
    )

    # 4. Show the view
    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
