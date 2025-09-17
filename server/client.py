# server/client

import socket
import json
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool


class ChatClient(QObject):
    """
    Handles TCP communication with the broker in a background thread.
    """
    # Signal to emit when a message is received from the server.
    # The payload will be a dictionary (the decoded JSON).
    messageReceived = Signal(dict)

    def __init__(self, host='127.0.0.1', port=8888):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self._is_running = False

    def connect_and_listen(self):
        """Main method to be run in the background thread."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self._is_running = True

            # Start listening for incoming messages
            buffer = ""
            while self._is_running:
                data = self.socket.recv(4096).decode()
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        msg_data = json.loads(line)
                        # Emit the signal to notify the controller on the main thread
                        self.messageReceived.emit(msg_data)
                    except json.JSONDecodeError:
                        print(f"Client: Received invalid JSON: {line}")
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.disconnect()

    def send_message(self, data: dict):
        """Sends a JSON message to the server. Can be called from any thread."""
        if self.socket and self._is_running:
            try:
                message = json.dumps(data) + '\n'
                self.socket.sendall(message.encode())
            except Exception as e:
                print(f"Client failed to send message: {e}")

    def disconnect(self):
        """Shuts down the connection."""
        self._is_running = False
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Client disconnected.")
