import socket
import subprocess
import os
import time

SERVER_IP = '127.0.0.1'  # Adjust this to your server's IP
SERVER_PORT = 12345

def run_work_command(range_assigned):
    command = [
        "/Rotor",
        "-m", "address",
        "-g",
        "--gpux", "18,128",  # 18,128 for multiple files on the 3070 to keep heat down.  36,128 for single address is okay
        "--coin", "BTC",
        "--range", range_assigned,
        "BTCADDRESS",
        "-o", "found.txt"
    ]
    subprocess.run(command)

def main():
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))
            
            # Receive range assignment
            range_assigned = client_socket.recv(1024).decode()
            
            if range_assigned == "no_more_chunks":
                print("No more chunks left to process. Exiting.")
                client_socket.close()
                break

            print(f"Assigned range: {range_assigned}")

            # Send acknowledgment of receipt
            client_socket.send("ack".encode())

            # Begin work
            run_work_command(range_assigned)

            # Check results and report back
            if os.path.exists("found.txt"):
                with open("found.txt", 'r') as f:
                    results = f.read()
                    if results:
                        client_socket.send(results.encode())
                    else:
                        client_socket.send("completed".encode())
            else:
                client_socket.send("completed".encode())

            # Close the current connection
            client_socket.close()

            # Wait for x seconds before requesting the next chunk
            time.sleep(3)

        except ConnectionError:
            print("Failed to connect to the server. Retrying in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()
