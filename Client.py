import socket
import os
import time

# Client configuration
PORT = 5050
HEADER = 64
FORMAT = 'utf-8'
DISCONNECTED_MESSAGE = "DISCONNECT"

class Client:
    def __init__(self, host, port):
        self.address = (host, port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.address)
        os.makedirs('client_files', exist_ok=True)

    def send(self, msg):
        """Send a message to the server and return the response."""
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)
        return self.client.recv(1024).decode(FORMAT)

    def login(self, username, password):
        return self.send(f"LOGIN {username} {password}")

    def list_files(self):
        return self.send("LIST")

    def download_file(self, file_name):
        response = self.send(f"DOWNLOAD {file_name}")
        if response == "FILE_FOUND":
            file_path = os.path.join('client_files', file_name)
            try:
                self.client.settimeout(30)  # Extend timeout for large files
                with open(file_path, 'wb') as f:
                    print(f"Downloading {file_name}...")
                    while True:
                        data = self.client.recv(1024)
                        if data.endswith(b"EOF"):  # Check voor einde-bestand markering
                            f.write(data[:-3])  # Schrijf alles behalve "EOF"
                            break
                        if not data:
                            print("Connection closed by server before EOF.")
                            return f"Download failed: connection closed by server."
                        f.write(data)  # Write each chunk to the file
                print(f"File '{file_name}' downloaded successfully to {file_path}.")
                return f"File '{file_name}' downloaded successfully."
            except socket.timeout:
                print(f"Timeout while downloading '{file_name}'.")
                return f"Download failed due to server timeout."
            except Exception as e:
                print(f"Error while downloading '{file_name}': {e}")
                return f"Download failed due to an error: {e}"
        elif response == "FILE_NOT_FOUND":
            return f"File '{file_name}' was not found on the server."
        else:
            return f"Unexpected response from server: {response}"

    def upload_file(self, file_name):
        """Upload a file to the server."""
        file_path = os.path.join('client_files', file_name)
        if os.path.exists(file_path):
            response = self.send(f"UPLOAD {file_name}")
            if response == "READY_TO_RECEIVE":
                with open(file_path, 'rb') as f:
                    while chunk := f.read(1024):
                        self.client.sendall(chunk)
                self.client.send(b"EOF")
                print(f"File '{file_name}' uploaded successfully.")
                return "Upload completed."
            else:
                return f"Unexpected server response: {response}"
        return "File not found for upload."

    def logout(self):
        return self.send("LOGOUT")

    def disconnect(self):
        self.send(DISCONNECTED_MESSAGE)
        self.client.close()

    def batch_download_files(self, file_names):
        start_time = time.time()
        download_results = {}
        for file_name in file_names:
            print(f"Starting download for: {file_name}")
            response = self.download_file(file_name)
            download_results[file_name] = response
            print(response)
        total_time = time.time() - start_time
        print(f"\nBatch download completed in {total_time:.2f} seconds.")
        return {"results": download_results, "time_taken": total_time}


if __name__ == "__main__":
    client = Client(socket.gethostbyname(socket.gethostname()), PORT)
    try:
        while True:
            logged_in = False
            while not logged_in:
                username = input("Username: ")
                password = input("Password: ")
                response = client.login(username, password)
                if response == "LOGIN_SUCCESS":
                    print("Login successful!")
                    logged_in = True
                else:
                    print("Login failed. Try again.")

            while logged_in:
                print("\nMenu:")
                print("1. List files on server")
                print("2. Download a file")
                print("3. Upload a file")
                print("4. Batch download files")
                print("5. Logout")
                print("6. Disconnect")
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
                    if file_names:
                        results = client.batch_download_files(file_names)
                        for file_name, result in results["results"].items():
                            print(f"{file_name}: {result}")
                        print(f"Total time: {results['time_taken']:.2f} seconds")
                    else:
                        print("No files specified for batch download.")
                elif choice == "5":
                    print(client.logout())
                    logged_in = False
                elif choice == "6":
                    client.disconnect()
                    print("Disconnected from server.")
                    exit(0)
                else:
                    print("Invalid choice. Try again.")
    except KeyboardInterrupt:
        print("\n[INFO] Client exiting...")
        client.disconnect()
