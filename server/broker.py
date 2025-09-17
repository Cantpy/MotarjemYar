# server/broker.py

import asyncio
import json
import logging

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global State ---
# These two dictionaries are the entire "state" of our broker.
# 1. Maps a user_id to their writer object for sending data.
clients = {}
# 2. Maps a chat_id to a set of user_ids who are in that chat.
chat_rooms = {}


async def handle_client(reader, writer):
    """This function is called for each new client that connects."""
    user_id = None
    addr = writer.get_extra_info('peername')
    logging.info(f"New connection from {addr}")

    try:
        while True:
            # Wait for data from the client (e.g., {"type": "register", ...})
            data = await reader.readline()
            if not data:
                break  # Client disconnected

            message = data.decode().strip()
            try:
                msg_data = json.loads(message)

                # --- Message Routing Logic ---

                # A. Handle Registration: The first thing a client must do
                if msg_data.get("type") == "register":
                    user_id = msg_data.get("user_id")
                    chat_ids = msg_data.get("chat_ids", [])

                    if user_id is None:
                        continue

                    clients[user_id] = writer  # Store the writer for this user
                    for chat_id in chat_ids:
                        if chat_id not in chat_rooms:
                            chat_rooms[chat_id] = set()
                        chat_rooms[chat_id].add(user_id)
                    logging.info(f"User {user_id} registered for chats: {chat_ids}")

                # B. Handle Incoming Chat Messages
                elif user_id and msg_data.get("type") == "message":
                    chat_id = msg_data.get("chat_id")
                    message_payload = msg_data.get("payload")  # This will be our MessageDTO

                    if chat_id in chat_rooms:
                        # Prepare the message to be broadcast
                        broadcast_data = {
                            "type": "new_message",
                            "chat_id": chat_id,
                            "payload": message_payload
                        }
                        broadcast_json = json.dumps(broadcast_data) + '\n'

                        # Find all users in the room
                        recipients = chat_rooms.get(chat_id, set())
                        for recipient_id in recipients:
                            # Don't send the message back to the original sender
                            if recipient_id != user_id:
                                recipient_writer = clients.get(recipient_id)
                                if recipient_writer:
                                    recipient_writer.write(broadcast_json.encode())
                                    await recipient_writer.drain()

            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Invalid message from {addr}: {message} - Error: {e}")

    except ConnectionResetError:
        logging.warning(f"Connection reset by {addr}")
    finally:
        # --- Cleanup on Disconnect ---
        if user_id is not None:
            logging.info(f"User {user_id} ({addr}) disconnected.")
            clients.pop(user_id, None)
            for chat_id in list(chat_rooms.keys()):
                chat_rooms[chat_id].discard(user_id)
        writer.close()
        await writer.wait_closed()


async def main():
    """Starts the TCP server."""
    server = await asyncio.start_server(handle_client, '0.0.0.0', 8888)
    addr = server.sockets[0].getsockname()
    logging.info(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
