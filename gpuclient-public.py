import socket
import subprocess

# Constants
SERVER_HOST = '54.xx.xx.xx'  # Replace with the actual server IP address
SERVER_PORT = xx
GPU_PROGRAM_PATH = './Rotor'  # Replace with the actual path to the Rotor program

def read_results(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None  # If the file does not exist, no results to report

def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    return client_socket

def get_btc_address(client_socket):
    # Identify as a GPU client
    client_socket.sendall(b'GPU\n')
    print("Sent GPU identification to server")
    
    # Handle the welcome message
    welcome_message = client_socket.recv(1024).decode().strip()
    print(f"Received welcome message: {welcome_message}")
    
    # Now, expect to receive the BTC address
    btc_address_message = client_socket.recv(1024).decode().strip()
    print(f"Received BTC address message: {btc_address_message}")
    
    btc_address = btc_address_message.split(':')[1].strip()  # Extract the BTC address from the server response
    return btc_address

def request_range(client_socket):
    print("Sent range request to server")
    client_socket.sendall(b"Requesting range\n")
    
    # Receive the next range assignment from the server
    next_range_message = client_socket.recv(1024).decode().strip()
    print(f"Received range assignment: {next_range_message}")
    
    return next_range_message


def report_results(client_socket, range_str, results):
    
    # Identify itself as a GPU client again
    client_socket.sendall(b'GPU\n')
    print("Sent GPU identification to server again")
    
    if results:
        message = f'Range Completed: {range_str}:{results}\n'
    else:
        message = f'Range Completed no results: {range_str}\n'
    
    # Send the results to the server
    client_socket.sendall(message.encode())
    print(f"Sent results to server: {message}")


def run_gpu_program(range_str, btc_address):
    start_range, end_range = range_str.split(':')
    cmd = [
        GPU_PROGRAM_PATH,
        '-g',
        '--gpui', '0,1,2,3',
        '--gpux', '44,128,44,128,38,128,28,128',
        '-m', 'address',
        '--coin', 'BTC',
        '--range', f"{start_range}:{end_range}",
        btc_address,
        '-o', 'found.txt'
    ]
    subprocess.run(cmd)  # Run the GPU program with the provided command

def clean_up():
    open('found.txt', 'w').close()  # Clean up found.txt for the next iteration

if __name__ == '__main__':
    try:
        with connect_to_server() as client_socket:
            btc_address = get_btc_address(client_socket)
            # Now we keep the socket open and use the same connection to request ranges and send results
            while True:
                try:
                    next_range_message = request_range(client_socket)
                    if "Assigned GPU range" in next_range_message:
                        _, range_str = next_range_message.split(':', 1)
                        range_str = range_str.strip()
                        run_gpu_program(range_str, btc_address)
                        results = read_results('found.txt')
                        report_results(client_socket, range_str, results)
                        clean_up()
                    else:
                        time.sleep(RETRY_INTERVAL)  # Wait before retrying if no range was assigned
                except Exception as e:
                    print(f"An error occurred during range request or processing: {e}")
                    time.sleep(RETRY_INTERVAL)  # Wait before retrying if an error occurred
    except Exception as e:
        print(f"An error occurred during initial connection or BTC address retrieval: {e}")

