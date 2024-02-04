import argparse
import random
import subprocess
import os
import re
import multiprocessing
import time
import sys

# Helper function to convert a number to hexadecimal
def number_to_hex(number):
    return hex(number)[2:]  # Remove the '0x' prefix

# Helper function to convert a hexadecimal string back to a number
def hex_to_number(hex_string):
    return int(hex_string, 16)

def generate_sub_range(overall_range):
    """Generate the next number in the overall range, starting from the end and working backwards."""
    global current_end  # Global variable to keep track of the current end of the range

    start, end = overall_range

    # Initialize current_end at the first call
    if 'current_end' not in globals():
        current_end = end

    # If the current end is less than the start, the range is exhausted
    if current_end < start:
        print("Range is exhausted.")
        return None

    #print(f"Processing number: {current_end}")
    time.sleep(0.15)  # Add a small delay for monitoring

    # Decrement current_end for the next call
    current_end -= 1

    return current_end


def run_msieve(number):
    #print(f"Running msieve on number: {number}")
    try:
        result = subprocess.run(
            ['/CPU-Primes/MATH/msieve/msieve', '-q', '-v', '-e', str(number)], 
            check=True, capture_output=True, text=True
        )
        time.sleep(.05)  # Add a delay for monitoring
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running msieve for number {number}: {e}")
        return ""

def load_scanned_numbers():
    print("Loading scanned numbers from file...")
    if os.path.exists('scanned.txt'):
        with open('scanned.txt', 'r') as file:
            scanned = set(line.strip() for line in file)
            print(f"Loaded {len(scanned)} numbers.")
            return scanned
    print("No scanned numbers file found.")
    return set()



def write_to_file(filename, number, digit_length=None, mode='mo'):
    if mode == 'mo':
        if digit_length is not None:
            filename = 'GPU.txt' if digit_length <= 13 else 'BF.txt'
    elif mode == 'bf':
        if digit_length is not None and digit_length > 13:
            filename = 'scanned.txt'

    encoded_number = number_to_hex(number)  # Convert number to hexadecimal

    with open(filename, 'a') as file:
        file.write(f"{encoded_number}\n")
        #print(f"Written {number} (Base10) / {encoded_number} (Hex) to {filename}")

    if filename == 'scanned.txt':
        scanned_numbers.add(number)

def process_msieve_output(output, hex_range):
    primes = re.findall(r'p(\d+) factor: (\d+)', output)
    
    # Check if no primes found
    if not primes:
        print("No primes found in msieve output.")
        return  # Return from the function if no primes are found

    # If primes are found, process them
    for digit_length, prime in primes:
        
        digit_length = int(digit_length)
        prime = int(prime)

        # Skip primes already in scanned_numbers
        encoded_prime = number_to_hex(prime)
        if encoded_prime in scanned_numbers:
            print(f"\033[91m{prime} already in scanned.txt\033[0m")
            continue

        # Process only if digit length is 10 or more
        if digit_length >= 10:
            if mode == 'mo':
                write_to_file('GPU.txt' if digit_length <= 13 else 'BF.txt', prime, digit_length, mode)
            elif mode == 'bf':
                if digit_length <= 13: #Edit here for processing digits with bf mode
                    write_to_file('GPU.txt', prime, digit_length, mode)
                else:
                    run_prime_cpu_printer(prime, hex_range)
                    write_to_file('scanned.txt', prime, digit_length, mode)  # Ensure mode is passed

def run_prime_cpu_printer(prime, hex_range):
    
    try:
        # Construct the command for prime-CPU-printer
        prime_cpu_printer_command = [
            "python3",
            "/CPU-Primes/prime-CPU-printer.py",
            "-r", hex_range,
            "-p", str(prime),
            "-w", "1"
        ]

        # Print the prime-CPU-printer command for verification
        #print(f"Running prime-CPU-printer with command: {' '.join(prime_cpu_printer_command)}")

        # Construct the command for brainflayer
        brainflayer_command = [
            "/CPU-Primes/brainflayer/brainflayer",
            "-v", "-t", "priv", "-x", "-a",
            "-b", "/CPU-Primes/brainflayer/puzzle-addresses.blf",
            "-o", "found.txt"
        ]

        # Print the brainflayer command for verification
        #print(f"Running brainflayer with command: {' '.join(brainflayer_command)}")

        # Start prime-CPU-printer asynchronously and pipe its output to brainflayer
        prime_cpu_printer_process = subprocess.Popen(prime_cpu_printer_command, stdout=subprocess.PIPE, text=True)
        brainflayer_process = subprocess.Popen(brainflayer_command, stdin=prime_cpu_printer_process.stdout, text=True)
        prime_cpu_printer_process.stdout.close()

    except subprocess.SubprocessError as e:
        print(f"Error running prime-CPU-printer or brainflayer: {e}")



def write_factor(prime, digit_length):
    """Write prime to appropriate file and update scanned_numbers in hexadecimal format."""
    file_to_write = 'GPU.txt' if digit_length <= 13 else 'BF.txt'
    
    # Write the prime number to the file in hexadecimal format
    write_to_file(file_to_write, prime, digit_length)
    
    # Update scanned_numbers with the hexadecimal encoded prime
    encoded_prime = number_to_hex(prime)
    scanned_numbers.add(encoded_prime)

def process_number(number):
    
    msieve_output = run_msieve(number)
    if msieve_output:  # Process only if msieve_output is not None
        process_msieve_output(msieve_output, hex_range)
    


def main():
    
    parser = argparse.ArgumentParser(
        description='Process a range of numbers using msieve.',
        formatter_class=argparse.RawTextHelpFormatter  # This will help in displaying the help text as it is written
    )
    parser.add_argument(
        '-R', '--range', 
        type=str, 
        required=True, 
        help="Specify the overall working range in format 'start:end'.\n"
             "Example: -R 10000000000:20000000000"
    )
    
    parser.add_argument(
        '-M', '--mode', 
        type=str, 
        choices=['mo', 'bf'], 
        required=True, 
        help="Set the mode of operation.\n"
             "  'mo': Mode for writing numbers to files based on digit length.\n"
             "  'bf': Mode for processing numbers with external programs.\n"
             "Example: -M mo"
    )
    
    parser.add_argument(
        '-H', '--hexrange',
        type=str,
        required=True,
        help="Specify the hexadecimal range in format 'start:end'.\n"
             "Example: -H 240C5C99449356A7B:3BFA00004F8C317FF"
    )

    # Check if no arguments were provided
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    global mode, scanned_numbers, sub_range, hex_range  # Include hex_range
    mode = args.mode
    overall_range = tuple(map(int, args.range.split(':')))
    hex_range = args.hexrange  # Ensure this argument is correctly obtained
    scanned_numbers = load_scanned_numbers()

    while True:
        current_number = generate_sub_range(overall_range)
        if current_number is None:
            print("Completed processing the entire range.")
            break

        #print(f"Processing number: {current_number}")
        process_number(current_number)

        #print("Number processing complete")

if __name__ == "__main__":
    main()
