import socket
import subprocess
import time

# Constants
SERVER_HOST = '54.x.x.x'  # Replace with the actual server IP address
SERVER_PORT = xxxx
PROGRAM_RUN_TIME = 1800  # Run the brainflayer program for 30 minutes (1800 seconds)

def run_brainflayer(start_range):
    """Run the brainflayer program with the provided start range."""
    # Format the start range to a BTC hex private key string
    start_range = start_range.rjust(64, '0')
    print(f"Starting brainflayer with start range: {start_range}")
    
    # Command to run brainflayer
    cmd = [
        './brainflayer',
        '-v', '-x', '-a', 
        '-I', start_range, 
        '-b', 'puzzle-address.blf',
        '-o', 'found.txt'
    ]
    
    # Start brainflayer and let it run for 30 minutes
    process = subprocess.Popen(cmd)
    time.sleep(PROGRAM_RUN_TIME)
    
    # Stop brainflayer after 30 minutes
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    
    # Read results from found.txt
    try:
        with open('found.txt', 'r') as file:
            results = file.read().strip()
            return results if results else "Nothing found"
    except FileNotFoundError:
        return "Nothing found"

def report_results_to_server(connection, results):
    """Send results back to the server."""
    message = f'Range completed: {results}\n'
    connection.sendall(message.encode())

def cpu_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # Connect to the server
        client_socket.connect((SERVER_HOST, SERVER_PORT))

        # Identify itself as a CPU client
        client_socket.sendall(b'CPU\n')

        # Handle the welcome message
        welcome_message = client_socket.recv(1024).decode().strip()
        print(welcome_message)

        # Infinite loop to continuously ask for ranges and process them
        while True:
            # Ask for a new range to hunt
            client_socket.sendall(b"Requesting range\n")
            next_range_message = client_socket.recv(1024).decode().strip()
            print(f"Received range: {next_range_message}")
            if "Assigned CPU range" in next_range_message:
                range_str = next_range_message.split(':')[1].strip()  # Extract the range "X:X"
                print(f"Processing range: {range_str}")

                # Run brainflayer
                results = run_brainflayer(range_str)

                # Report results to server
                if results and results != "Nothing found":
                    report_results_to_server(client_socket, results)

            else:
                print(f"Unexpected message: {next_range_message}")
                time.sleep(5)  # Wait a bit before retrying

if __name__ == '__main__':
    cpu_client()

