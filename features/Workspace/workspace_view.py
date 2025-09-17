# In your chat/_view.py file

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QPushButton,
                               QLabel, QScrollArea, QFrame)

from features.Workspace.workspace_models import ChatDTO, MessageDTO, UserDTO


# --- Custom Widget for a Single Message ---
class MessageWidget(QWidget):
    """A custom widget to display a single message bubble."""

    def __init__(self, message: MessageDTO, current_user_id: int):
        super().__init__()
        self.message_data = message

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Display sender's name
        sender_label = QLabel(f"<b>{message.sender.name}</b>")

        # Display message content
        content_label = QLabel(message.content)
        content_label.setWordWrap(True)

        # Display timestamp
        timestamp_label = QLabel(message.created_at.strftime("%Y-%m-%d %H:%M"))
        timestamp_label.setStyleSheet("color: grey; font-size: 9px;")

        layout.addWidget(sender_label)
        layout.addWidget(content_label)
        layout.addWidget(timestamp_label)

        # Style the message bubble
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-radius: 8px;
            }
        """)

        # Align to the right if the current user sent the message
        is_own_message = message.sender.id == current_user_id
        if is_own_message:
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.setStyleSheet("""
                QWidget {
                    background-color: #dcf8c6; /* A light green, like WhatsApp */
                    border-radius: 8px;
                }
            """)


# --- Main Chat View ---
class ChatView(QWidget):
    """
    The main UI for the chat/workspace feature.
    It is a "dumb" component: it displays data and emits signals.
    """
    # --- SIGNALS (Outputs to Controller) ---
    chatSelected = Signal(int)  # Emits the chat_id
    sendMessageClicked = Signal(str)  # Emits the message content

    def __init__(self, current_user_id: int, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        # --- Main Layout ---
        main_layout = QHBoxLayout(self)

        # --- Left Panel: Chat List ---
        self.chat_list_widget = QListWidget()
        self.chat_list_widget.setMaximumWidth(250)
        self.chat_list_widget.setStyleSheet("QListWidget::item:selected { background-color: #cde8ff; }")

        # --- Right Panel: Conversation ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Message Display Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.addStretch()  # Pushes messages to the top
        self.scroll_area.setWidget(self.message_container)

        # Message Input Area
        input_frame = QFrame()
        input_frame.setMaximumHeight(100)
        input_layout = QHBoxLayout(input_frame)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("پیام خود را اینجا بنویسید...")

        self.send_button = QPushButton("ارسال")

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        right_layout.addWidget(self.scroll_area)
        right_layout.addWidget(input_frame)

        main_layout.addWidget(self.chat_list_widget)
        main_layout.addWidget(right_panel, stretch=1)

    def _connect_signals(self):
        """Connects internal widget signals to this _view's public signals."""
        self.send_button.clicked.connect(self._on_send_clicked)
        self.chat_list_widget.currentItemChanged.connect(self._on_chat_selected)

    # --- Private Handlers that Emit Public Signals ---
    def _on_send_clicked(self):
        message_text = self.message_input.toPlainText().strip()
        if message_text:
            self.sendMessageClicked.emit(message_text)

    def _on_chat_selected(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        if current_item:
            chat_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.chatSelected.emit(chat_id)

    # --- PUBLIC METHODS (Inputs from Controller) ---

    def display_chat_list(self, chats: list[ChatDTO]):
        """Clears and repopulates the list of chats."""
        self.chat_list_widget.clear()
        for chat in chats:
            item = QListWidgetItem(chat.name)
            item.setData(Qt.ItemDataRole.UserRole, chat.id)  # Store chat ID in the item
            self.chat_list_widget.addItem(item)

    def display_chat_history(self, messages: list[MessageDTO]):
        """Clears the message _view and displays a list of past messages."""
        # Clear existing messages by creating a new container
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.addStretch()
        self.scroll_area.setWidget(self.message_container)

        for msg in messages:
            self.add_message(msg, scroll_to_bottom=False)

        self._scroll_to_bottom()

    def add_message(self, message: MessageDTO, scroll_to_bottom: bool = True):
        """Adds a new message to the display area."""
        message_widget = MessageWidget(message, self.current_user_id)

        # Insert the message before the stretch item
        self.message_layout.insertWidget(self.message_layout.count() - 1, message_widget)

        if scroll_to_bottom:
            self._scroll_to_bottom()

    def clear_message_input(self):
        """Clears the text input box."""
        self.message_input.clear()

    def _scroll_to_bottom(self):
        """Helper function to scroll the message area to the latest message."""
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
