def convert_to_hex(input_file_path, output_file_path):
    with open(input_file_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
        for line in input_file:
            # Removing any whitespace and converting to integer
            number = int(line.strip())
            # Converting to hexadecimal and writing to output file
            hex_number = hex(number)[2:]  # [2:] is used to remove the '0x' prefix
            output_file.write(hex_number + '\n')

# Example usage
input_file_path = 'scanned.txt'  # Replace with your input file path
output_file_path = 'scanned-converted.txt'  # Replace with your desired output file path

convert_to_hex(input_file_path, output_file_path)
