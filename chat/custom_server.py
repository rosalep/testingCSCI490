import sys
import os
import django
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_custom.settings')
django.setup()
import socket
import threading
import json
import hashlib
import base64
from chat.models import ChatMessage
from game.models import Player, Game

CHAT_SERVER_HOST = '127.0.0.1'
CHAT_SERVER_PORT = 8765
CHAT_ROOMS = {}  # Dictionary to store game_id: [list_of_client_sockets]

def perform_handshake(client_socket):
    try:
        request_data = client_socket.recv(4096).decode('utf-8')
        headers = {}
        for line in request_data.split('\r\n')[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.strip().lower()] = value.strip()

        if 'upgrade' in headers and headers['upgrade'].lower() == 'websocket' and \
           'connection' in headers and 'upgrade' in [c.strip().lower() for c in headers['connection'].split(',')] and \
           'sec-websocket-key' in headers and \
           'sec-websocket-version' in headers and headers['sec-websocket-version'] == '13':

            sec_websocket_key = headers['sec-websocket-key']
            magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            combined_string = sec_websocket_key + magic_string
            sha1_hash = hashlib.sha1(combined_string.encode('utf-8')).digest()
            sec_websocket_accept = base64.b64encode(sha1_hash).decode('utf-8')

            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {sec_websocket_accept}\r\n"
                "\r\n"
            ).encode('utf-8')
            client_socket.send(response)
            print(f"WebSocket handshake successful for {client_socket.getpeername()}")
            return True
        else:
            print(f"Invalid WebSocket handshake request from {client_socket.getpeername()}")
            return False
    except Exception as e:
        print(f"Error during handshake with {client_socket.getpeername()}: {e}")
        return False

def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    if not perform_handshake(client_socket):
        client_socket.close()
        return

    current_game_id = None
    current_player = None
    try:
        while True:
            # Basic WebSocket frame reading (only for text, no masking handled for server->client)
            header = client_socket.recv(2)
            if not header:
                break

            opcode = header[0] & 0x0F
            is_masked = (header[1] & 0x80) != 0
            payload_len = header[1] & 0x7F

            if payload_len == 126:
                payload_len = int.from_bytes(client_socket.recv(2), 'big')
            elif payload_len == 127:
                payload_len = int.from_bytes(client_socket.recv(8), 'big')

            mask = client_socket.recv(4) if is_masked else None
            payload = client_socket.recv(payload_len)

            if is_masked and mask:
                unmasked_payload = bytes([payload[i] ^ mask[i % 4] for i in range(payload_len)])
                try:
                    message = json.loads(unmasked_payload.decode('utf-8'))
                    message_type = message.get('type')

                    if message_type == 'join_room':
                        game_id = message.get('game_id')
                        player_id = message.get('player_id')
                        try:
                            player = Player.objects.get(player_id=player_id)
                            game = Game.objects.get(game_id=game_id)
                            current_player = player
                            current_game_id = game_id
                            if game_id not in CHAT_ROOMS:
                                CHAT_ROOMS[game_id] = []
                            if client_socket not in CHAT_ROOMS[game_id]:
                                CHAT_ROOMS[game_id].append(client_socket)
                            print(f"Client {client_address} (Player: {player.player_import.username}) joined room {game_id}")
                            send_chat_history(client_socket, game_id)
                        except Player.DoesNotExist:
                            print(f"Player ID {player_id} not found.")
                    elif message_type == 'chat_message':
                        if current_game_id and 'message' in message and current_player :
                            message = message['message']
                            ChatMessage.objects.create(game_import=game, message_sender=current_player, message=message)
                            broadcast(current_game_id, f"{current_player.player_import.username}: {message}", client_socket)
                    elif message_type == 'leave_room':
                        if current_game_id and client_socket in CHAT_ROOMS.get(current_game_id, []):
                            CHAT_ROOMS[current_game_id].remove(client_socket)
                            print(f"Client {client_address} (Player: {player.player_import.username}) left room {current_game_id}")

                except json.JSONDecodeError:
                    print(f"Received non-JSON data from {client_address}: {unmasked_payload.decode('utf-8')}")
                except Exception as e:
                    print(f"Error processing message from {client_address}: {e}")
            elif opcode == 0x08:  # Connection Close
                print(f"Client {client_address} initiated closing handshake.")
                break # Exit the loop to close the connection

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        print(f"Connection closed with {client_address}")
        if current_game_id and client_socket in CHAT_ROOMS.get(current_game_id, []):
            CHAT_ROOMS[current_game_id].remove(client_socket)
        client_socket.close()

def send_chat_history(client_socket, game_id):
    try:
        history = ChatMessage.objects.filter(game_import=game_id).order_by('time_sent')[:50] # Get last 50 messages
        history_messages = [{"player": msg.player.player_import.username, "message": msg.message, "time_sent": str(msg.time_sent)} for msg in history]
        send_websocket_message(client_socket, json.dumps({'type': 'history', 'messages': history_messages}))
    except Exception as e:
        print(f"Error sending chat history for game {game_id}: {e}")

def send_websocket_message(client_socket, message):
    payload = message.encode('utf-8')
    length = len(payload)
    header = bytearray()
    header.append(0x81)  # Text frame, fin bit set

    if length <= 125:
        header.append(length)
    elif length <= 65535:
        header.append(126)
        header.extend(length.to_bytes(2, 'big'))
    else:
        header.append(127)
        header.extend(length.to_bytes(8, 'big'))

    client_socket.send(header + payload)

def broadcast(game_id, message, sender_socket):
    if game_id in CHAT_ROOMS:
        for client in CHAT_ROOMS[game_id]:
            try:
                send_websocket_message(client, json.dumps({'message': message}))
                # check against game word
                game = Game.objects.get(game_id=game_id)
                print(message.split(":",1)[1].strip())
                if game.word_to_guess == message.split(":",1)[1].strip():
                    print("got it")
                    # change score and go to next round
                    Game.objects.update_score(game, game.guessers.team_id, 1)
                    
                    Game.objects.next_round(game)
                    print("after correct guess")
            except socket.error as e:
                print(f"Error sending message to a client in room {game_id}: {e}")
                if client in CHAT_ROOMS.get(game_id, []):
                    CHAT_ROOMS[game_id].remove(client)
                    client.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
    server_socket.listen(5)
    print(f"Chat server listening on {CHAT_SERVER_HOST}:{CHAT_SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.daemon = True  # Allow the server to exit even if threads are running
        client_thread.start()

if __name__ == "__main__":
    start_server()
