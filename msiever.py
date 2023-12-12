import argparse
import random
import subprocess
import os
import re
import multiprocessing
import time
import sys  # Import sys for accessing command line arguments

def generate_sub_range(overall_range):
    """Generate a random subrange within the overall range."""
    start, end = overall_range
    random_start = random.randint(start, end - 10000)
    print(f"Generated subrange: {random_start} to {random_start + 10000}")
    return (random_start, random_start + 10000)

def run_msieve(number):
    #print(f"Running msieve on number: {number}")
    try:
        result = subprocess.run(
            ['MATH/msieve/msieve', '-q', '-v', '-e', str(number)], 
            check=True, capture_output=True, text=True
        )
        time.sleep(0.1)  # Add a delay
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running msieve for number {number}: {e}")
        return ""

def load_scanned_numbers():
    """Load scanned numbers from file into a set."""
    if os.path.exists('scanned.txt'):
        with open('scanned.txt', 'r') as file:
            scanned = set(map(int, file.read().splitlines()))
            return scanned
    return set()

def write_to_file(filename, number, digit_length=None):
    """Write a number to the specified file and update scanned_numbers if necessary."""
    # Determine the correct file based on digit length, if provided
    if digit_length is not None:
        filename = 'GPU.txt' if digit_length <= 13 else 'BF.txt'

    with open(filename, 'a') as file:
        file.write(f"{number}\n")
    
    if filename == 'scanned.txt':
        scanned_numbers.add(number)

def process_msieve_output(output, hex_range):
    primes = re.findall(r'p(\d+) factor: (\d+)', output)
    if not primes:
        print("No primes found in msieve output.")
    for digit_length, prime in primes:
        
        digit_length = int(digit_length)
        prime = int(prime)

        # Skip primes already in scanned_numbers
        if prime in scanned_numbers:
            print(f"\033[91m{prime} already in scanned.txt\033[0m")
            continue

        # Process only if digit length is 10 or more
        if digit_length >= 10:
            if mode == 'mo':
                filename = 'GPU.txt' if digit_length <= 13 else 'BF.txt'
                write_to_file(filename, prime)
                #print(f"Writing prime {prime} to {filename}")
            elif mode == 'bf':
                if digit_length <= 13:
                    write_to_file('GPU.txt', prime)
                    #print(f"Writing prime {prime} to GPU.txt")
                else:
                    run_prime_cpu_printer(prime, hex_range)
                    write_to_file('scanned.txt', prime)
                    #print(f"Wrote Prime {prime} to Scanned.txt")
                    scanned_numbers.add(prime)

                   
def run_prime_cpu_printer(prime, hex_range):
    
    try:
        # Construct the command for prime-CPU-printer
        prime_cpu_printer_command = [
            "python3",
            " prime-CPU-printer.py",
            "-r", hex_range,
            "-p", str(prime),
            "-w", "1"
        ]

        # Construct the command for brainflayer
        brainflayer_command = [
            " brainflayer/brainflayer",
            "-v", "-t", "priv", "-x", "-a",
            "-b", " brainflayer/puzzle-addresses.blf",
            "-o", "found.txt"
        ]

        # Start prime-CPU-printer asynchronously and pipe its output to brainflayer
        prime_cpu_printer_process = subprocess.Popen(prime_cpu_printer_command, stdout=subprocess.PIPE, text=True)
        brainflayer_process = subprocess.Popen(brainflayer_command, stdin=prime_cpu_printer_process.stdout, text=True)
        prime_cpu_printer_process.stdout.close()

        #print(f"Started prime-CPU-printer and brainflayer for prime: {prime}")

    except subprocess.SubprocessError as e:
        print(f"Error running prime-CPU-printer or brainflayer: {e}")



def write_factor(prime, digit_length):
    """Write prime to appropriate file."""
    file_to_write = 'GPU.txt' if digit_length <= 13 else 'BF.txt'
    write_to_file(file_to_write, prime)
    scanned_numbers.add(prime)

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
        sub_range = generate_sub_range(overall_range)
        print("Processing new subrange")

        for number in range(sub_range[0], sub_range[1]):
            process_number(number)

        print("Subrange processing complete")

if __name__ == "__main__":
    main()
