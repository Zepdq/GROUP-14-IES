# Server Code
import socket
import threading
import os

# Configuratie
HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECTED_MESSAGE = "DISCONNECT"

# Initialize server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# Lijst van actieve clients
clients = []

# Zorg ervoor dat de directory voor bestanden bestaat
os.makedirs('server_files', exist_ok=True)

def broadcast(message, sender_conn):
    """Verstuur een bericht naar alle verbonden clients, behalve de afzender."""
    for client in clients:
        conn, addr = client
        if conn != sender_conn:
            try:
                conn.send(message.encode(FORMAT))
                print(f"Bericht verzonden naar {addr}: {message}")  # Debugprint
            except Exception as e:
                print(f"Fout tijdens broadcast naar {addr}: {e}")
                clients.remove(client)

def handle_client(conn, addr):
    """Afhandelen van een verbinding met een client."""
    print(f"Nieuwe verbinding: {addr} verbonden.")
    clients.append((conn, addr))

    connected = True
    while connected:
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT).strip()
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)

                if msg == DISCONNECTED_MESSAGE:
                    connected = False
                    print(f"{addr} heeft de verbinding verbroken.")
                    conn.send("Verbinding verbroken.".encode(FORMAT))
                elif msg == 'LIST':
                    files = os.listdir('server_files')
                    files_list = "\n".join(files) if files else "No files available."
                    conn.send(files_list.encode(FORMAT))
                elif msg.startswith('DOWNLOAD'):
                    file_name = msg.split(" ", 1)[1]
                    file_path = os.path.join('server_files', file_name)
                    if os.path.exists(file_path):
                        conn.send("FILE_FOUND".encode(FORMAT))
                        with open(file_path, 'rb') as f:
                            conn.send(f.read())
                    else:
                        conn.send("FILE_NOT_FOUND".encode(FORMAT))
                elif msg.startswith("UPLOAD"):
                    _, file_name = msg.split(" ", 1)
                    file_path = os.path.join('server_files', file_name)
                    with open(file_path, 'wb') as f:
                        data = conn.recv(1024)
                        f.write(data)
                    print(f"File {file_name} uploaded by {addr}")
                    conn.send("UPLOAD_SUCCESS".encode(FORMAT))
                else:
                    print(f"[{addr}] {msg}")  # Debugprint
                    broadcast(f"[{addr}] {msg}", conn)
        except Exception as e:
            print(f"Fout met {addr}: {e}")
            connected = False

    conn.close()
    clients.remove((conn, addr))
    print(f"Verbinding met {addr} gesloten.")

def start():
    """Start de server en luistert naar inkomende verbindingen."""
    print(f"STARTING server op IP: {SERVER} en PORT: {PORT}")
    server.listen()
    print(f"Server luistert op IP: {SERVER} en PORT: {PORT}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Actieve verbindingen: {threading.active_count() - 1}")

if __name__ == "__main__":
    print("Server wordt gestart...")
    start()
