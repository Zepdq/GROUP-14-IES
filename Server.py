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

        self.users = {"admin": "admin"}  # Hardcoded gebruikers voor testen
        os.makedirs(self.SERVER_FILES_DIR, exist_ok=True)

    def start(self):
        """Start het draaien van de server en luister voor inkomende verbindingen."""
        print("[INFO] Starting server...")
        print(f"[INFO] Server running on {self.address}")
        self.server.listen()
        print("[INFO] Server is now listening for connections...")
        self.server.settimeout(None)  # Disable timeout to avoid abrupt disconnections
        print("[INFO] Server is now listening for connections...")
        while True:
            try:
                conn, addr = self.server.accept()
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
                # Ontvang de lengte van het bericht
                msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    msg = conn.recv(msg_length).decode(self.FORMAT)

                    print(f"[RECEIVED] From {addr}: {msg}")  # Debugging logs voor elke ontvangen command

                    if msg == self.DISCONNECTED_MESSAGE:
                        connected = False
                        print(f"[DISCONNECT] {addr} disconnected.")
                    elif msg.startswith("LOGIN"):
                        logged_in_user = self.handle_login(conn, msg)
                        print(f"[DEBUG] Logged in user: {logged_in_user}")
                        if logged_in_user:
                            conn.send("LOGIN_SUCCESS".encode(self.FORMAT))
                        else:
                            conn.send("LOGIN_FAILED".encode(self.FORMAT))
                    elif not logged_in_user:
                        conn.send("LOGIN_REQUIRED".encode(self.FORMAT))
                        print(f"[LOGIN REQUIRED] {addr} attempted a command before logging in.")
                    elif msg == "LIST":
                        self.handle_list(conn)
                    elif msg.startswith("DOWNLOAD"):
                        self.handle_download(conn, msg)
                    elif msg.startswith("UPLOAD"):
                        self.handle_upload(conn, msg)
                    elif msg == "LOGOUT":
                        logged_in_user = None
                        conn.send("LOGOUT_SUCCESS".encode(self.FORMAT))
                        print(f"[LOGOUT] {addr} successfully logged out.")
                    else:
                        conn.send("INVALID_COMMAND".encode(self.FORMAT))
                        print(f"[INVALID COMMAND] Received invalid command from {addr}: {msg}")
            except Exception as e:
                print(f"[ERROR] An error occurred while handling the client {addr}: {e}. Closing connection...")
                connected = False
                connected = False
                try:
                    if conn.fileno() != -1:  # Check if connection is still open
                        conn.shutdown(socket.SHUT_RDWR)
                except Exception as ex:
                    print(f"[WARN] Unable to shutdown connection {addr}: {ex}")
                finally:
                    conn.close()
                break

        try:
            if conn.fileno() != -1:  # Check if the connection is still valid
                conn.shutdown(socket.SHUT_RDWR)
        except Exception as ex:
            print(f"[WARN] Unable to shutdown connection {addr}: {ex}")
        finally:
            conn.close()
        print(f"[CLOSED] Connection with {addr} closed.")

    def handle_login(self, conn, msg):
        """Afhandelen van de login-verzoek van een client."""
        try:
            print(f"[LOGIN] Login attempt with message: {msg}")  # Debugging
            _, username, password = msg.split(" ", 2)
            if username in self.users and self.users[username] == password:
                print(f"[LOGIN SUCCESS] User {username} logged in.")
                return username
            else:
                print(f"[LOGIN FAILED] Invalid credentials for user {username}.")
                return None
        except ValueError:
            print("[LOGIN ERROR] Invalid login format received. Expected 'LOGIN <username> <password>'.")
            conn.send("INVALID_LOGIN_FORMAT".encode(self.FORMAT))
            return None

    def handle_list(self, conn):
        """Stuur een lijst van bestanden in de serverdirectory naar de client."""
        try:
            files = os.listdir(self.SERVER_FILES_DIR)
        except OSError as e:
            print(f"[ERROR] Unable to list files: {e}")
            conn.send("LIST_FAILED".encode(self.FORMAT))
            return
        files_list = "\n".join(files) if files else "No files available."
        conn.send(files_list.encode(self.FORMAT))
        print("[LIST] Sent file list to client.")

    def handle_download(self, conn, msg):
        """Stuur een aanvraag van de client om een bestand te downloaden."""
        try:
            _, file_name = msg.split(" ", 1)
            file_path = os.path.join(self.SERVER_FILES_DIR, file_name)
            if os.path.exists(file_path):
                conn.send("FILE_FOUND".encode(self.FORMAT))
                with open(file_path, 'rb') as f:
                    while chunk := f.read(1024):  # Send file in chunks to prevent memory issues
                        conn.sendall(chunk)
                print(f"[DOWNLOAD] File '{file_name}' successfully sent.")
            else:
                conn.send("FILE_NOT_FOUND".encode(self.FORMAT))
                conn.shutdown(socket.SHUT_WR)  # Gracefully close write connection
                print(f"[DOWNLOAD ERROR] File '{file_name}' not found.")
        except ValueError:
            conn.send("INVALID_DOWNLOAD_COMMAND".encode(self.FORMAT))
            print("[DOWNLOAD ERROR] Invalid command format.")

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
                print(f"[DOWNLOAD] File '{file_name}' successfully sent.")
            else:
                conn.send("FILE_NOT_FOUND".encode(self.FORMAT))
                print(f"[DOWNLOAD ERROR] File '{file_name}' not found.")
        except ValueError:
            conn.send("INVALID_DOWNLOAD_COMMAND".encode(self.FORMAT))
            print("[DOWNLOAD ERROR] Invalid command format.")
        except Exception as e:
            print(f"[DOWNLOAD ERROR] Unexpected error during download: {e}")

    def handle_upload(self, conn, msg):  # Add refactored upload method
        """Ontvang en sla een bestand van de client op."""
        try:
            print(f"[UPLOAD] Received command: {msg}")  # Debugging

            # Controleer format van het commando
            if len(msg.split(" ", 1)) != 2:
                conn.send("INVALID_UPLOAD_COMMAND".encode(self.FORMAT))
                print("[UPLOAD ERROR] Invalid upload command format. Expected 'UPLOAD <filename>'.")
                return

            _, file_name = msg.split(" ", 1)  # Haal de bestandsnaam eruit
            file_path = os.path.join(self.SERVER_FILES_DIR, file_name)

            # Debugging: Toon de bestandsnaam die wordt geüpload
            print(f"[UPLOAD] Preparing to receive file: {file_name}")
            # Increase the timeout to handle large files without premature termination
            conn.settimeout(30)
            # Zet een timeout als de client geen data stuurt
            conn.settimeout(10)  # Maximaal 10 seconden wachten op data

            # Voorbereiden om het bestand te ontvangen
            with open(file_path, 'wb') as f:
                while True:
                    try:
                        data = conn.recv(1024)  # Ontvang data in chunks van 1024 bytes
                        if not data:  # Geen data ontvangen, verbreek de verbinding
                            print(f"[UPLOAD ERROR] No data received. Closing connection.")
                            conn.send("UPLOAD_FAILED".encode(self.FORMAT))
                            return

                        print(
                            f"[UPLOAD] Received data: {data[:50]}...")  # Debugging - Laat het eerste deel van de data zien

                        if data.endswith(b"END"):  # Zoek naar de eindmarker
                            f.write(data[:-3].rstrip(b"\x00"))  # Clean up padding bytes
                            f.write(data[:-3])  # Schrijf alle data behalve "END"
                            break

                        f.write(data)  # Schrijf ontvangen data naar een bestand
                    except socket.timeout:
                        print("[UPLOAD ERROR] Client took too long to send data.")
                        conn.send("UPLOAD_TIMEOUT".encode(self.FORMAT))
                        return

            # Upload succesvol
            conn.send("UPLOAD_SUCCESS".encode(self.FORMAT))
            print(f"[UPLOAD SUCCESS] File '{file_name}' successfully uploaded and saved to {self.SERVER_FILES_DIR}.")
        except Exception as e:
            print(f"[UPLOAD ERROR] Error occurred during upload '{file_name}': {e}")
            if os.path.exists(file_path):  # Cleanup partially uploaded files
                print("[UPLOAD ERROR] Cleaning up incomplete upload.")
                os.remove(file_path)
            conn.send("UPLOAD_FAILED".encode(self.FORMAT))


if __name__ == "__main__":
    # Configureer het serveradres en start
    try:
        server = Server(socket.gethostbyname(socket.gethostname()), Server.PORT)
    except OSError as e:
        print(f"[CRITICAL] Failed to initialize server: {e}")
        exit(1)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server shutting down gracefully.")
        try:
            server.server.shutdown(socket.SHUT_RDWR)
        except Exception as ex:
            print(f"[WARN] Unable to shutdown server socket: {ex}")
        finally:
            server.server.close()
    finally:
        server.server.close()
