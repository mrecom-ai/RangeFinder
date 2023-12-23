#This program reads a list of prime numbers from a file or takes a specific prime number with -p and iterates through a range (can also read through a range file in format x:x with -R flag.  This can be used with brainflayer like:
#python3 prime-CPU-printer.py -r 20000000000000000:3ffffffffffffffff -f ../10-digit-primes-00 -w 1 | brainflayer/brainflayer -v -a -t priv -x -b brainflayer/puzzle-addresses.blf 

import argparse
import concurrent.futures
import sys
from concurrent.futures import ProcessPoolExecutor
import math


def read_primes_in_chunks(file_path, chunk_size):
    """Generator function to read primes from a file in chunks."""
    with open(file_path, 'r') as file:
        primes = file.readlines()
        for i in range(0, len(primes), chunk_size):
            yield primes[i:i + chunk_size]
            
def decimal_to_256bit_hex(value):
    """Convert a decimal value to a 256-bit hex string."""
    hex_value = hex(value)[2:]
    padded_hex = hex_value.zfill(64)
    return padded_hex

def read_primes(file_path, reverse_order=False):
    """Generator function to read primes from a file one at a time."""
    with open(file_path, 'r') as file:
        if reverse_order:
            lines = reversed(list(file))
        else:
            lines = file.readlines()
        for line in lines:
            prime = int(line.strip())
            yield prime

def read_ranges(file_path):
    """Generator function to read ranges from a file one at a time."""
    with open(file_path, 'r') as file:
        for line in file:
            yield line.strip()

def calculate_hex_values_batch(prime_batch, start_range, end_range):
    for prime in prime_batch:
        calculate_hex_values(prime, start_range, end_range)

def calculate_hex_values(prime, start_range, end_range):
    """Calculate and print hex values for a given prime within the range."""
    current_value = ((start_range + prime - 1) // prime) * prime
    if current_value > end_range:
        # Prime is too large for the given range, so we silently ignore it.
        return
    while current_value <= end_range:
        hex_value = decimal_to_256bit_hex(current_value)
        print(f"{hex_value}")
        current_value += prime


def main():
    parser = argparse.ArgumentParser(description="Find hex values for primes within given hex ranges. Check code for example.")
    parser.add_argument("-r", type=str, help="Hex range in the format start:end.")
    parser.add_argument("-R", type=str, help="File with hex ranges, one per line in the format X:X.")
    parser.add_argument("-f", type=str, help="File with prime numbers.")
    parser.add_argument("-p", type=int, help="Specific prime number.")
    parser.add_argument("-w", type=int, default=1, help="Maximum number of concurrent workers. Default is 1.")
    parser.add_argument("-reverse", action="store_true", help="Read prime numbers from the file in reverse order.")
    parser.add_argument("-C", type=int, help="Count of multiprocessing units. Only valid with -f flag.")

    args = parser.parse_args()

    if args.C and not args.f:
        parser.error("-C requires -f.")
        return

    executor = ProcessPoolExecutor(max_workers=args.w)
    futures = []

    try:
        if args.R:
            range_generator = read_ranges(args.R)
        else:
            range_generator = [args.r]

        for hex_range in range_generator:
            start_hex, end_hex = hex_range.split(':')
            start_range = int(start_hex, 16)
            end_range = int(end_hex, 16)

            if args.p:
                executor.submit(calculate_hex_values, args.p, start_range, end_range)
            elif args.f:
                if args.C:
                    file_size = sum(1 for _ in open(args.f))
                    chunk_size = math.ceil(file_size / args.C)

                    for prime_batch in read_primes_in_chunks(args.f, chunk_size):
                        primes = [int(prime.strip()) for prime in prime_batch]
                        future = executor.submit(calculate_hex_values_batch, primes, start_range, end_range)
                        futures.append(future)
                else:
                    prime_batch = []
                    for prime in read_primes(args.f, args.reverse):
                        prime_batch.append(prime)
                        if len(prime_batch) >= batch_size:
                            future = executor.submit(calculate_hex_values_batch, prime_batch, start_range, end_range)
                            futures.append(future)
                            prime_batch = []

                    if prime_batch:
                        future = executor.submit(calculate_hex_values_batch, prime_batch, start_range, end_range)
                        futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                future.result()

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        executor.shutdown(wait=False)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        executor.shutdown(wait=True)

if __name__ == "__main__":
    main()
