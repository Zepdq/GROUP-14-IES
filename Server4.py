# Server Code
import socket
import threading
import os

class Server:
    PORT = 5050
    HEADER = 64
    FORMAT = 'utf-8'
    DISCONNECTED_MESSAGE = "DISCONNECT"
    SERVER_FILES_DIR = 'server_files'

    def __init__(self, host, port):
        self.address = (host, port)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(self.address)
            print(f"[INFO] Server successfully bound to {self.address}")
        except OSError as e:
            print(f"[ERROR] Failed to bind to {self.address}: {e}")
            raise

        self.users = {
            "Ot": "Buschman",
            "Jop": "Goekoop",
        } # Hardcoded gebruikers voor testen
        os.makedirs(self.SERVER_FILES_DIR, exist_ok=True)
        self.clients = []  # Voor chatfunctionaliteit

    def broadcast(self, message, sender_conn):
        """Stuur een bericht naar alle verbonden clients behalve de afzender."""
        for client in self.clients:
            if client != sender_conn:
                try:
                    client.send(message.encode(self.FORMAT))
                except Exception as e:
                    print(f"[ERROR] Could not send message to a client: {e}")

    def start(self):
        """Start het draaien van de server en luister voor inkomende verbindingen."""
        print("[INFO] Starting server...")
        print(f"[INFO] Server running on {self.address}")
        self.server.listen()
        print("[INFO] Server is now listening for connections...")
        while True:
            try:
                conn, addr = self.server.accept()
                self.clients.append(conn)
                print(f"[NEW CONNECTION] {addr} connected.")
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.start()
                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            except Exception as e:
                print(f"[ERROR] Error accepting connection: {e}")
                continue

    def handle_client(self, conn, addr):
        """Beheer de communicatie met een enkele client."""
        print(f"[HANDLING] New connection from {addr}")
        logged_in_user = None
        connected = True

        while connected:
            try:
                msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
                if not msg_length:
                    raise ConnectionResetError("No data received, closing connection.")
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(self.FORMAT)

                print(f"[RECEIVED] From {addr}: {msg}")  # Debugging logs voor elke ontvangen command

                if msg == self.DISCONNECTED_MESSAGE:
                    connected = False
                    print(f"[DISCONNECT] {addr} disconnected.")
                elif msg.startswith("LOGIN"):
                    logged_in_user = self.handle_login(conn, msg)
                elif not logged_in_user:
                    conn.send("LOGIN_REQUIRED".encode(self.FORMAT))
                elif msg.startswith("CHAT"):
                    chat_message = msg.split(" ", 1)[1]
                    self.broadcast(f"[{addr}] {chat_message}", conn)
                elif msg == "LIST":
                    self.handle_list(conn)
                elif msg.startswith("DOWNLOAD"):
                    self.handle_download(conn, msg)
                elif msg.startswith("UPLOAD"):
                    self.handle_upload(conn, msg)
                elif msg == "LOGOUT":
                    logged_in_user = None
                    conn.send("LOGOUT_SUCCESS".encode(self.FORMAT))
                else:
                    conn.send("INVALID_COMMAND".encode(self.FORMAT))
            except Exception as e:
                print(f"[ERROR] An error occurred while handling the client {addr}: {e}. Closing connection...")
                connected = False

        self.clients.remove(conn)
        conn.close()
        print(f"[CLOSED] Connection with {addr} closed.")

    def handle_login(self, conn, msg):
        """Afhandelen van de login-verzoek van een client."""
        try:
            print(f"[DEBUG] Login attempt with message: {msg}")
            _, username, password = msg.split(" ", 2)
            if username in self.users and self.users[username] == password:
                conn.send("LOGIN_SUCCESS".encode(self.FORMAT))
                print(f"[LOGIN SUCCESS] User '{username}' logged in.")
                return username
            else:
                conn.send("LOGIN_FAILED".encode(self.FORMAT))
                print(f"[LOGIN FAILED] Invalid credentials for user '{username}'.")
                return None
        except ValueError:
            conn.send("INVALID_LOGIN_FORMAT".encode(self.FORMAT))
            print("[LOGIN ERROR] Invalid login format received.")
            return None

    def handle_list(self, conn):
        """Stuur een lijst van bestanden in de serverdirectory naar de client."""
        try:
            files = os.listdir(self.SERVER_FILES_DIR)
        except OSError as e:
            conn.send("LIST_FAILED".encode(self.FORMAT))
            return
        files_list = "\n".join(files) if files else "No files available."
        conn.send(files_list.encode(self.FORMAT))

    def handle_download(self, conn, msg):
        try:
            _, file_name = msg.split(" ", 1)
            file_path = os.path.join(self.SERVER_FILES_DIR, file_name)
            if os.path.exists(file_path):
                conn.send("FILE_FOUND".encode(self.FORMAT))
                with open(file_path, 'rb') as f:
                    while chunk := f.read(1024):
                        conn.sendall(chunk)
                conn.sendall(b"EOF")  # Correcte eindmarkering verzenden
            else:
                conn.send("FILE_NOT_FOUND".encode(self.FORMAT))
        except ValueError:
            conn.send("INVALID_DOWNLOAD_COMMAND".encode(self.FORMAT))
        except Exception as e:
            print(f"[DOWNLOAD ERROR] Unexpected error during download: {e}")

    def handle_upload(self, conn, msg):
        try:
            _, file_name = msg.split(" ", 1)
            file_path = os.path.join(self.SERVER_FILES_DIR, file_name)

            conn.settimeout(30)
            with open(file_path, 'wb') as f:
                while True:
                    data = conn.recv(1024)
                    if data.endswith(b"EOF"):
                        f.write(data[:-3])
                        break
                    f.write(data)
            conn.send("UPLOAD_SUCCESS".encode(self.FORMAT))
        except Exception as e:
            conn.send("UPLOAD_FAILED".encode(self.FORMAT))

if __name__ == "__main__":
    server = Server(socket.gethostbyname(socket.gethostname()), Server.PORT)
    server.start()
