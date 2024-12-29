# Author information
# # Ot Buschman
# # Job Goekoop
# # Eva van der Poel
# # Zep de Quay

import socket
import threading
import os

# Configuration
HEADER = 64 #Size of bites, specifies the length of the incoming message
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname()) #Auto IP from host
ADDR = (SERVER, PORT) #Combining server and port
FORMAT = 'utf-8'
DISCONNECTED_MESSAGE = "DISCONNECT"

# Initialize the server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

#Ensure the directory for files exists
os.makedirs('server_files', exist_ok = True)

def handle_client(conn, addr):
    """Handles communication with a single client."""
    print(f"New connection {addr} connected.")

    connected = True
    while connected:
        # Receive the message length
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            # Receive the actual message
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECTED_MESSAGE:
                connected = False           #Disconnect the loop
                print(f"{addr}: {msg}")

            elif msg == 'LIST':
                files = os.listdir('server_files')
                files_list = "\n".join(files) if files else "No files available."
                conn.send(files_list.encode(FORMAT))
            elif msg.startswith('DOWNLOAD'):
                file_name = msg.split("",1)[1]
                file_path = os.path.join('server_files', file_name)
                if os.path.exists(file_path):
                    conn.send("FILE_FOUND".encode(FORMAT))
                    with open(file_path, 'rb') as f:
                        conn.send(f.read())
                else:
                    conn.send("FILE_NOT_FOUND".encode(FORMAT))
            elif msg.startswit("UPLOAD"):
                # Handle file upload
                _, file_name = msg.split(" ", 1)
                file_path = os.path.join('server_files', file_name)
                with open(file_path, 'wb') as f:
                    data = conn.recv(1024)
                    f.write(data)
                print(f"File {file_name} uploaded by {addr}")
                conn.send("UPLOAD_SUCCESS".encode(FORMAT))
            else:
                conn.send("INVALID_COMMAND".encode(FORMAT))



    conn.close()  #Close the client connection when disconnected

def start():
    """Starts the server and listens for incoming connections."""
    print(f"STARTING server on IP: {SERVER} and PORT : {PORT}")
    server.listen()
    print(f"Server is listening on IP: {SERVER} and PORT : {PORT}")
    while True:
        conn, addr = server.accept() #Accept new clients, so that more clients can connect simultanious
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Active connections: {threading.active_count() - 1}")

if __name__ == "__main__":
    print("Starting the server...")
    start()   #Beginning the serverloop



