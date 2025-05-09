import sys
import os
import django
# lets django run
# must be put on path, otherwise it doesnt work
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
from django.shortcuts import redirect

CHAT_SERVER_HOST = '127.0.0.1'
CHAT_SERVER_PORT = 8765
CHAT_ROOMS = {}  # equivalent to different games


"""
example client socket:
    <socket.socket fd=9, family=2, type=1, proto=0, laddr=('127.0.0.1', 8765), raddr=('127.0.0.1', 46538)>

example request data:
    GET / HTTP/1.1
    Host: 127.0.0.1:8765
    Connection: Upgrade
    Pragma: no-cache
    Cache-Control: no-cache
    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
    Upgrade: websocket
    Origin: http://127.0.0.1:8000
    Sec-WebSocket-Version: 13
    Accept-Encoding: gzip, deflate, br, zstd
    Accept-Language: en-US,en;q=0.9
    Cookie: csrftoken=DTXCZosKlsWTyzR37ZfXs1Mi4W9He4Jn; sessionid=kua3byxpfs9n61fnw8hh1kddqk11ykqh
    Sec-WebSocket-Key: TkEfLs1Lbz6NEKje+fppYA==
    Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits
"""
# reference code used: https://github.com/AlexanderEllis/websocket-from-scratch/blob/main/server.py
# HTTP handshake
def perform_handshake(client_socket):
    try:
        request_data = client_socket.recv(4096).decode('utf-8')
        headers = {}
        # create dictionary
        for line in request_data.split('\r\n')[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.strip().lower()] = value.strip()

        if 'upgrade' in headers and headers['upgrade'].lower() == 'websocket' and \
           'connection' in headers and 'upgrade' in [c.strip().lower() for c in headers['connection'].split(',')] and \
           'sec-websocket-key' in headers and \
           'sec-websocket-version' in headers and headers['sec-websocket-version'] == '13':

            # create a new key to use as accept
            sec_websocket_key = headers['sec-websocket-key']
            magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            combined_string = sec_websocket_key + magic_string
            sha1_hash = hashlib.sha1(combined_string.encode('utf-8')).digest()
            sec_websocket_accept = base64.b64encode(sha1_hash).decode('utf-8')

            # corresponding response with accept key
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
    
# Websocket frame ref: https://www.openmymind.net/WebSocket-Framing-Masking-Fragmentation-and-More/
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    # do handshake
    if not perform_handshake(client_socket):
        client_socket.close()
        return

    current_game_id = None
    current_player = None
    try:
        while True:
            # read in Websocket frame 
            header = client_socket.recv(2)
            if not header: #or len(header) < 2:
                break
            # bitwise used for masking
            opcode = header[0] & 0x0F # 4 bits; 0x0F represents 15 AKA 00001111, which masks the last 4 bits
            is_masked = (header[1] & 0x80) != 0 # 1 bit; 0x80 is 128
            payload_len = header[1] & 0x7F # depends: 0-125, 126, 127

            # RFC 6455: the following 2 bytes interpreted as a 16-bit unsigned integer are the payload length
            if payload_len == 126:
                payload_len = int.from_bytes(client_socket.recv(2), 'big')
            # RFC 6455: the following 8 bytes interpreted as a 64-bit unsigned integer are the payload length
            elif payload_len == 127:
                payload_len = int.from_bytes(client_socket.recv(8), 'big')

            # masking key; up to 4 bytes
            mask = client_socket.recv(4) if is_masked else None
            payload = client_socket.recv(payload_len)

            if is_masked and mask:
                # get each chunk
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
                           
                        except Player.DoesNotExist:
                            print(f"Player ID {player_id} not found.")
                    # share canvas data
                    elif message_type == 'canvas_update':
                        if current_game_id: # in a game
                            if message['message']:
                                # like the chat broadcast, but specifically for the canvas data
                                # pass the sender bc we dont want to overwrite the artists' canvas
                                broadcast_canvas_data(current_game_id, {'message':message['message'], 'type': message['type']}, client_socket)
                    # send guesses
                    elif message_type == 'chat_message':
                        if current_game_id and 'message' in message and current_player :
                            ChatMessage.objects.create(game_import=game, message_sender=current_player, message=message['message'])
                            broadcast(current_game_id, {'type': message_type,'player': current_player.player_import.username,  'message': message['message']})
                    elif message_type == 'leave_room':
                        if current_game_id and client_socket in CHAT_ROOMS.get(current_game_id, []):
                            CHAT_ROOMS[current_game_id].remove(client_socket)
                            print(f"Client {client_address} (Player: {player.player_import.username}) left room {current_game_id}")

                except json.JSONDecodeError:
                    print(f"Received non-JSON data from {client_address}: {unmasked_payload.decode('utf-8')}")
                except Exception as e:
                    print(f"Error processing message from {client_address}: {e}")
            elif opcode == 0x08:  
                print(f"Client {client_address} initiated closing handshake.")
                break 

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        print(f"Connection closed with {client_address}")
        if current_game_id and client_socket in CHAT_ROOMS.get(current_game_id, []):
            CHAT_ROOMS[current_game_id].remove(client_socket)
        client_socket.close()


def send_websocket_message(client_socket, message):
    payload = message.encode('utf-8')
    length = len(payload)
    header = bytearray()
    header.append(0x81) 

    if length <= 125:
        header.append(length)
    elif length <= 65535:
        header.append(126)
        header.extend(length.to_bytes(2, 'big'))
    else:
        header.append(127)
        header.extend(length.to_bytes(8, 'big'))

    client_socket.send(header + payload)

def broadcast_canvas_data(game_id, message, sender_socket):
    # check that game exists
    if game_id in CHAT_ROOMS:
        # send data to each player in the game 
        for client in CHAT_ROOMS[game_id]:
            # dont include artist 
            if client != sender_socket:
                try:
                    # pass the message parameters (type, message)
                    send_websocket_message(client, json.dumps({'type': message['type'],'message': message['message']})) 
                except socket.error as e:
                    print(f"Socket Error in Game {game_id}: {e}")
                except Exception as e:
                    print(f"Exception Error: {e}")

# sender_socket isnt a parameter since we want the chat messages to show up for all players
def broadcast(game_id, message):
    if game_id in CHAT_ROOMS:
        for client in CHAT_ROOMS[game_id]:
            try:
                # same concept as in broadcast_canvas_data, but with new parameter 'player'
                # 'player' keeps track of who sent the chat message
                send_websocket_message(client, json.dumps({'message': message['message'], 'type': message['type'], 'player': message['player']}))
                # check against game word
                game = Game.objects.get(game_id=game_id)

                if game.word_to_guess == message['message']:
                    print("\nMESSAGE CHECK\n")
                    # change score and go to next round
                    Game.objects.update_score(game, game.guessers.team_id, 1)
                    # getting called multiple times
                    Game.objects.next_round(game)

            except socket.error as e:
                print(f"Error sending chat in room {game_id}: {e}")
                # disconnect on error
                if client in CHAT_ROOMS.get(game_id, []):
                    CHAT_ROOMS[game_id].remove(client)
                    client.close()

def start_server():
    # basic server code
    # create the socket, bind to IP and port, and keep listening
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
    # server_socket.listen(5)
    server_socket.listen()
    print(f"Chat server listening on {CHAT_SERVER_HOST}:{CHAT_SERVER_PORT}")

    # keep listening for connections
    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.daemon = True  # can run background threads
        client_thread.start()

if __name__ == "__main__":
    start_server()
