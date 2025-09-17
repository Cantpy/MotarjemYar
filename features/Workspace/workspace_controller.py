# features/Workspace/workspace_controller.py

from features.Workspace.workspace_logic import ChatLogic
from features.Workspace.workspace_view import ChatView
from features.Workspace.workspace_models import MessageDTO

from PySide6.QtCore import QThread, QObject
from server.client import ChatClient


class ChatController(QObject):
    """
    The orchestrator for the Chat feature.
    - Listens to the View's signals.
    - Calls the Logic layer.
    - Updates the View with data.
    """

    def __init__(self, view: ChatView, logic: ChatLogic, current_user_id: int, client: ChatClient):
        super().__init__()
        self._logic = logic
        self._view = view
        self._current_user_id = current_user_id
        self._client = client

        # State variable to keep track of the currently active chat
        self._active_chat_id: int | None = None

        # Connect the _view's signals to the controller's handler methods
        self._connect_signals()

    def _connect_signals(self):
        """Connects signals from the _view to the controller's handlers (slots)."""
        self._view.chatSelected.connect(self.handle_chat_selection)
        self._view.sendMessageClicked.connect(self.handle_send_message)

    def get_view(self) -> ChatView:
        """Returns the _view instance managed by this controller."""
        return self._view

    def perform_initial_load(self):
        """
        Performs the initial data fetch when the feature is first opened.
        This would be called by the factory right after creating the controller.
        """
        chat_dtos = self._logic.get_chats_for_user(self._current_user_id)
        self._view.display_chat_list(chat_dtos)

        # --- Register with Broker ---
        chat_ids = [chat.id for chat in chat_dtos]
        self._client.send_message({
            "type": "register",
            "user_id": self._current_user_id,
            "chat_ids": chat_ids
        })

    def perform_initial_load(self):
        """
        Performs the initial data fetch when the feature is first opened.
        This would be called by your factory right after creating the controller.
        """
        # 1. Get the list of chats for the current user from the _logic layer
        chat_dtos = self._logic.get_chats_for_user(self._current_user_id)

        # 2. Tell the _view to display this list
        self._view.display_chat_list(chat_dtos)

    # --- HANDLERS (SLOTS) ---

    def handle_chat_selection(self, chat_id: int):
        """Handles the user selecting a new chat from the list."""
        print(f"Controller: Chat {chat_id} selected.")
        self._active_chat_id = chat_id

        # 1. Request the message history for this chat from the _logic layer
        message_history_dtos = self._logic.get_chat_history(chat_id)

        # 2. Tell the _view to display these messages
        self._view.display_chat_history(message_history_dtos)

    def handle_send_message(self, content: str):
        """Handles the user clicking the 'send' button."""
        if self._active_chat_id is None:
            # Maybe show a warning to the user in a real app
            print("Controller: Cannot send message, no chat selected.")
            return

        print(f"Controller: Sending message '{content}' to chat {self._active_chat_id}.")

        # 1. Ask the _logic layer to send the message
        new_message_dto = self._logic.send_message(
            sender_id=self._current_user_id,
            chat_id=self._active_chat_id,
            content=content
        )

        # 2. If the message was sent successfully...
        if new_message_dto:
            # 2a. Tell the _view to add the new message to the display
            self._view.add_message(new_message_dto)

            # 2b. Tell the _view to clear the input field
            self._view.clear_message_input()
        else:
            # Handle potential errors, e.g., user not authorized to send in a channel
            print("Controller: Logic layer prevented message from being sent.")

    # --- METHODS FOR REAL-TIME UPDATES ---

    def on_new_message_received(self, message_data: dict):
        """
        This is a public method that will be called by the real-time client
        when a new message arrives from the network.
        """
        if message_data.get("type") == "new_message":
            chat_id = message_data.get("chat_id")
            # We need to reconstruct the DTO from the payload dictionary
            payload = message_data.get("payload", {})

            if chat_id == self._active_chat_id:
                # You'll need a function to convert the payload dict back to a MessageDTO
                # For now, we'll assume a simple reconstruction
                # message_dto = MessageDTO(**payload) # This requires some care with nested DTOs
                # self.view.add_message(message_dto)
                print(f"Controller: Real-time message received: {payload}")

    def _start_client_thread(self):
        """Creates a QThread, moves the client to it, and starts listening."""
        self.client_thread = QThread()
        self._client.moveToThread(self.client_thread)

        # Connect the thread's started signal to our client's main loop
        self.client_thread.started.connect(self._client.connect_and_listen)

        # Connect the client's received signal to our controller's handler
        self._client.messageReceived.connect(self.on_new_message_received)

        # Handle cleanup
        self.client_thread.finished.connect(self.client_thread.deleteLater)

        self.client_thread.start()

    def cleanup(self):
        self._client.disconnect()
        self.client_thread.quit()
        self.client_thread.wait()