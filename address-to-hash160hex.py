import base58
import sys

def address_to_hash160(address):
    """Convert a BTC address to its hash160 representation."""
    try:
        decoded = base58.b58decode_check(address)
        # Remove the version byte (first byte)
        return decoded[1:]
    except Exception as e:
        print(f"Error decoding address {address}: {e}")
        return None

def main(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            address = line.strip()
            hash160 = address_to_hash160(address)
            if hash160:
                outfile.write(hash160.hex() + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script_name.py input_file output_file")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)

