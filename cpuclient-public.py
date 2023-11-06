import socket
import subprocess
import time

# Constants
SERVER_HOST = '54.x.x.x'  # Replace with the actual server IP address
SERVER_PORT = xxxx
PROGRAM_RUN_TIME = 1800  # Run the brainflayer program for 30 minutes (1800 seconds)

def run_brainflayer(range_str):
    """Run the brainflayer program with the provided range."""
    # Format the range to a BTC hex private key string
    start_range, end_range = range_str.split(':')
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
    
    # Start brainflayer and let it run for the specified time
    process = subprocess.Popen(cmd)
    time.sleep(PROGRAM_RUN_TIME)
    
    # Stop brainflayer after the specified time
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    
    # Read results from found.txt
    try:
        with open('found.txt', 'r') as file:
            results = file.read().strip()
            return results
    except FileNotFoundError:
        return ""

def report_results_to_server(connection, results):
    """Send results back to the server."""
    if results:
        message = f'Range Completed with results: {results}\n'
        print(f"Sending message to server: {message}")  # Print the message before sending
        connection.sendall(message.encode())
    # If there are no results, don't send any message



def cpu_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            # Connect to the server
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            
            # Receive and ignore the welcome message
            welcome_message = client_socket.recv(1024).decode().strip()
            print(welcome_message)

            # Identify itself as a CPU client
            client_socket.sendall(b'CPU\n')
            
            # Handle the server response after identifying as a CPU client
            server_response = client_socket.recv(1024).decode().strip()
            print(server_response)
            
            # Check if server response is as expected
            if "Connected as CPU client" in server_response:
                # Infinite loop to continuously ask for ranges and process them
                while True:
                    # Ask for a new range to process
                    client_socket.sendall(b"Requesting range\n")
                    next_range_message = client_socket.recv(1024).decode().strip()

                    if "Assigned CPU range" in next_range_message:
                        # Extract the range "X:X"
                        _, range_str = next_range_message.split('Assigned CPU range: ')
                        range_str = range_str.strip()
                        print(f"Processing range: {range_str}")

                        # Run brainflayer
                        results = run_brainflayer(range_str)

                        # Report results to server
                        if results:
                            report_results_to_server(client_socket, results)
                            # Wait for a response from the server
                            server_ack = client_socket.recv(1024).decode().strip()
                            if server_ack == "Results logged.":
                                print(f"Server acknowledged results: {server_ack}")
                            else:
                                print(f"Unexpected acknowledgment from server: {server_ack}")
                        else:
                            # If there are no results, don't send any message and just request a new range
                            print("No results found, requesting new range.")

                    elif "No CPU range available at the moment" in next_range_message:
                        print(next_range_message)
                        time.sleep(30)  # Wait a bit before retrying to request a range
                    else:
                        print(f"Unexpected message: {next_range_message}")
                        break  # Exit on unexpected message

            else:
                print("Did not receive expected server response after identifying as CPU client.")
                # Handle the unexpected server response

        except (ConnectionError, socket.timeout) as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    cpu_client()

