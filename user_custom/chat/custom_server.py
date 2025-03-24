import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 8081

clients_list = []

def run_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(8)
    print(f"Server listening on {host}:{port}")
    while True:
        print("inside")
        conn, addr = server.accept()
        threading.Thread(target=connect_client, args=(conn, addr)).start()

def broadcast(message, sender):
    print("broadcast")
    message_bytes = message.encode('utf-8')
    message_size = len(message_bytes).to_bytes(4, 'big')
    for client in clients_list:
        if client != sender:
            try:
                print("before send")
                client.sendall(message_size + message_bytes)
            except Exception as e:
                print(f"Error broadcasting: {e}")
                clients_list.remove(client)

def connect_client(conn, addr):
    conn.send(b"Successfully Joined Chatroom")
    print("inside chat")
    clients_list.append(conn)
    try:
        while True:
            message_size_bytes = conn.recv(4)
            if not message_size_bytes:
                break
            message_size = int.from_bytes(message_size_bytes, 'big')
            data = conn.recv(message_size).decode('utf-8')
            print("boradcast")
            broadcast(data, conn)
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        clients_list.remove(conn)
        conn.close()
        print(f"Client {addr} disconnected.")



if __name__ == "__main__":
    run_server(HOST, PORT)