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

def report_results_to_server(connection, results):
    if results:
        message = f'Range Completed with results: {results}\n'
    else:
        message = 'Range completed no results\n'
    connection.sendall(message.encode())

def run_gpu_program(range_str, btc_address):
    print(f"Received range string: {range_str}")  # Debug print statement
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
    print(f"Running GPU program with command: {' '.join(cmd)}")  # Debug print statement
    subprocess.run(cmd)  # Run the GPU program with the provided command


def gpu_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # Connect to the server
        client_socket.connect((SERVER_HOST, SERVER_PORT))

        # Identify itself as a GPU client
        client_socket.sendall(b'GPU\n')

        # Handle the welcome message
        welcome_message = client_socket.recv(1024).decode().strip()
        print(welcome_message)  # Or handle as needed

        # Receive BTC Address from the server
        btc_address_message = client_socket.recv(1024).decode().strip()
        btc_address = btc_address_message.split(':')[1].strip()  # Extract the BTC address from the server response
        print(f"Received BTC address: {btc_address}")

        # Infinite loop to continuously ask for ranges and process them
        while True:
            # Ask for a new range to hunt
            client_socket.sendall(b"Requesting range\n")
            next_range_message = client_socket.recv(1024).decode().strip()
            print(f"Received range: {next_range_message}")
            if "Assigned GPU range" in next_range_message:
                print(f"Full message received for range assignment: {next_range_message}")
                _, range_str = next_range_message.split(':', 1)
                range_str = range_str.strip()
                print(f"Extracted range string: {range_str}")  # This should print the full range


                # Run the GPU program
                run_gpu_program(range_str, btc_address)

                # Read results from found.txt
                results = read_results('found.txt')

                # Report results to server
                report_results_to_server(client_socket, results)

                # Clean up found.txt for the next iteration
                open('found.txt', 'w').close()
            else:
                print(f"Unexpected message: {next_range_message}")

if __name__ == '__main__':
    gpu_client()

