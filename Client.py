# Author information
# # Ot Buschman
# # Job Goekoop
# # Eva van der Poel
# # Zep de Quay

import socket
import os

# Client configuration
HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECTED_MESSAGE = "DISCONNECT"
SERVER = "195.169.169.11"  # Replace with actual server IP if on a network
ADDR = (SERVER, PORT)

# Create client socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

# Ensure the directory for received files exists
os.makedirs('client_files', exist_ok=True)

def send(msg):
    """Send a message to the server."""
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def download_file(file_name):
    """Request to download a file from the server."""
    send(f"DOWNLOAD {file_name}")
    response = client.recv(1024).decode(FORMAT)
    if response == "FILE_FOUND":
        file_path = os.path.join('client_files', file_name)
        with open(file_path, 'wb') as f:
            data = client.recv(1024)
            f.write(data)
        print(f"File {file_name} downloaded and saved in client_files.")
    else:
        print("File not found on the server.")

def upload_file(file_name):
    """Upload a file to the server."""
    file_path = os.path.join('client_files', file_name)
    if os.path.exists(file_path):
        send(f"UPLOAD {file_name}")
        with open(file_path, 'rb') as f:
            client.send(f.read())
        print(client.recv(1024).decode(FORMAT))  # Server's response
    else:
        print("File not found in client_files.")

# Main menu loop
if __name__ == "__main__":
    print("Client connected to the server.")
    while True:
        print("\nMenu:")
        print("1. List files on server")
        print("2. Download a file")
        print("3. Upload a file")
        print("4. Disconnect")
        choice = input("Enter your choice: ")

        if choice == '1':
            send("LIST")
            files = client.recv(1024).decode(FORMAT)
            print("Files on server:")
            print(files)
        elif choice == '2':
            file_name = input("Enter the name of the file to download: ")
            download_file(file_name)
        elif choice == '3':
            file_name = input("Enter the name of the file to upload: ")
            upload_file(file_name)
        elif choice == '4':
            send(DISCONNECTED_MESSAGE)
            print("Disconnected from server.")
            break
        else:
            print("Invalid choice. Please try again.")

