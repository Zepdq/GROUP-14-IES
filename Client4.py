# Client Code
import socket
import os
import threading
import time

class Client:
    PORT = 5050
    HEADER = 64
    FORMAT = 'utf-8'
    DISCONNECTED_MESSAGE = "DISCONNECT"

    def __init__(self, host, port):
        self.address = (host, port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.address)
        os.makedirs('client_files', exist_ok=True)

    def send(self, msg):
        try:
            message = msg.encode(self.FORMAT)
            msg_length = len(message)
            send_length = str(msg_length).encode(self.FORMAT)
            send_length += b' ' * (self.HEADER - len(send_length))
            self.client.send(send_length)
            self.client.send(message)
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")

    def login(self, username, password):
        self.send(f"LOGIN {username} {password}")
        try:
            response = self.client.recv(1024).decode(self.FORMAT)
            if response == "LOGIN_SUCCESS":
                print("[INFO] Login successful!")
            elif response == "LOGIN_FAILED":
                print("[ERROR] Invalid username or password.")
            else:
                print(f"[ERROR] Unexpected server response: {response}")
            return response
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return "LOGIN_FAILED"

    def list_files(self):
        self.send("LIST")
        try:
            response = self.client.recv(1024).decode(self.FORMAT)
            return response
        except Exception as e:
            print(f"[ERROR] Failed to list files: {e}")
            return "LIST_FAILED"

    def download_file(self, file_name):
        self.send(f"DOWNLOAD {file_name}")
        try:
            response = self.client.recv(1024).decode(self.FORMAT)
            if response == "FILE_FOUND":
                file_path = os.path.join('client_files', file_name)
                with open(file_path, 'wb') as f:
                    while True:
                        data = self.client.recv(1024)
                        if data.endswith(b"EOF"):
                            f.write(data[:-3])
                            break
                        f.write(data)
                return f"File '{file_name}' downloaded successfully."
            elif response == "FILE_NOT_FOUND":
                return f"File '{file_name}' was not found on the server."
            else:
                return f"Unexpected response from server: {response}"
        except Exception as e:
            print(f"[ERROR] Failed to download file: {e}")
            return "DOWNLOAD_FAILED"

    def upload_file(self, file_name):
        file_path = os.path.join('client_files', file_name)
        if os.path.exists(file_path):
            self.send(f"UPLOAD {file_name}")
            try:
                with open(file_path, 'rb') as f:
                    while chunk := f.read(1024):
                        self.client.sendall(chunk)
                self.client.send(b"EOF")
                response = self.client.recv(1024).decode(self.FORMAT)
                return response
            except Exception as e:
                print(f"[ERROR] Failed to upload file: {e}")
                return "UPLOAD_FAILED"
        return "File not found for upload."

    def batch_download_files(self, file_names_input):
        start_time = time.time()
        download_results = {}

        # Check if the input is correct
        if isinstance(file_names_input, list):
            file_names = [file_name.strip() for file_name in file_names_input]
        else:
            raise ValueError("The input must be a list of filenames.")

        for file_name in file_names:
            attempts = 0
            max_attempts = 3
            while attempts < max_attempts:
                response = self.download_file(file_name)
                if "downloaded successfully" in response.lower():
                    download_results[file_name] = response
                    break
                elif "not found" in response.lower(): # if file is not found
                    attempts += 1
                    print(f"The file '{file_name}' does not exist. Attempts remaining: {max_attempts - attempts}.")
                    file_name = input("Input a correct filename: ").strip()

                # Unexpected server response
                else:
                    print(f"Unexpected server response: {response}")
                    break

            # When limit is overdue
            if attempts == max_attempts:
                print(f"Skipping file '{file_name}' after {max_attempts} failed attempts.")

        total_time = time.time() - start_time
        return {"results": download_results, "time_taken": total_time}


    def logout(self):
        self.send("LOGOUT")
        try:
            response = self.client.recv(1024).decode(self.FORMAT)
            return response
        except Exception as e:
            print(f"[ERROR] Failed to logout: {e}")
            return "LOGOUT_FAILED"

    def disconnect(self):
        try:
            self.send(self.DISCONNECTED_MESSAGE)
            self.client.close()
        except Exception as e:
            print(f"[ERROR] Failed to disconnect: {e}")

    def chat(self):
        print("\nType your messages below. Type 'exit' to leave the chat.")
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()
        while True:
            message = input()
            if message.lower() == "exit":
                break
            self.send(f"CHAT {message}")

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode(self.FORMAT)
                if message:
                    print(message)
            except Exception as e:
                print("[ERROR] Lost connection to the server.")
                break

if __name__ == "__main__":
    client = Client(socket.gethostbyname(socket.gethostname()), Client.PORT)
    try:
        while True:
            logged_in = False
            while not logged_in:
                username = input("Username: ")
                password = input("Password: ")
                response = client.login(username, password)
                if response == "LOGIN_SUCCESS":
                    logged_in = True

            while logged_in:
                print("\nMenu:")
                print("1. List files on server")
                print("2. Download a file")
                print("3. Upload a file")
                print("4. Batch download files")
                print("5. Chat")
                print("6. Logout")
                print("7. Disconnect")
                choice = input("Enter your choice: ")

                if choice == "1":
                    print(client.list_files())
                elif choice == "2":
                    file_name = input("Enter file name to download: ")
                    print(client.download_file(file_name))
                elif choice == "3":
                    file_name = input("Enter file name to upload: ")
                    print(client.upload_file(file_name))
                elif choice == "4":
                    file_names = input("Enter file names (comma-separated): ").split(",")
                    file_names = [name.strip() for name in file_names]
                    results = client.batch_download_files(file_names)
                    for file_name, result in results["results"].items():
                        print(f"{file_name}: {result}")
                    print(f"Total time: {results['time_taken']:.2f} seconds")
                elif choice == "5":
                    client.chat()
                elif choice == "6":
                    print(client.logout())
                    logged_in = False
                elif choice == "7":
                    client.disconnect()
                    print("Disconnected from server.")
                    exit(0)
                else:
                    print("Invalid choice. Try again.")
    except KeyboardInterrupt:
        print("\n[INFO] Client exiting...")
        client.disconnect()
