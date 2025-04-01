# import socket
# import threading
# import sys
# import select
# from thread import *

# # threading will help with handling multiple clients/requests at the same time
# # that way, there can be more than one concurrent game at a time
# HOST = '127.0.0.1'
# PORT = 8080

# clients_list = []
# def run_server(host, port):
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.bind((host, port))
#     server.listen(8) # two teams of four
#     while True:
#         # accept incoming connections
#         conn, addr = server.accept()
#         # make new thread to handle connection & start it
#         threading.Thread(target=connect_client, args=conn).start()

# # sends the message
# def broadcast(message, sender):
#     for clients in clients_list:
#         # checks if recv is not sender
#         if clients != sender:
#             try:
#                 message_size = int.from_bytes(message, 'big')
#                 clients.sendall(message_size + message.encode('utf-8'))
#                 # clients.send(message)
#             except:
#                 # clients.close()
#                 clients_list.remove(clients)
        
# # connects to host
# def connect_client(conn, addr):
#     conn.send("Successfully Joined Chatroom")
#     # join "queue"
#     clients_list.append(conn)
#     while True:
#         # specify max size of messages to read (bytes)
#         message = conn.recv(1024)
#         if message:
#             message_size = int.from_bytes(message, 'big')
#             data = conn.recv(message_size).decode('utf-8')
#             broadcast(data, conn)    
#         else:
#             break
#     clients_list.remove(conn)
#     conn.close()
#     print(f"Client {addr} disconnected.")
# if __name__ == "__main__":
#     run_server(HOST, PORT)