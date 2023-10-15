#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <openssl/sha.h>
#include <openssl/ripemd.h>
#include <secp256k1.h>
#include <libbase58.h>
#include <time.h>

#define PRIVATE_KEY_SIZE 32

void base58_encode(unsigned char *bytes, int bytes_len, char *encoded) {
    size_t enc_len = 128;
    b58enc(encoded, &enc_len, bytes, bytes_len);
}

void private_key_to_public_key(const unsigned char *private_key, unsigned char *public_key_compressed) {
    secp256k1_context *ctx = secp256k1_context_create(SECP256K1_CONTEXT_SIGN);
    secp256k1_pubkey pubkey;

    if (!secp256k1_ec_pubkey_create(ctx, &pubkey, private_key)) {
        printf("Error creating public key\n");
        return;
    }

    size_t output_length_compressed = 33;
    secp256k1_ec_pubkey_serialize(ctx, public_key_compressed, &output_length_compressed, &pubkey, SECP256K1_EC_COMPRESSED);

    secp256k1_context_destroy(ctx);
}

void public_key_to_address(const unsigned char *public_key, size_t public_key_size, char *address) {
    unsigned char sha256_hash[SHA256_DIGEST_LENGTH];
    unsigned char ripemd160_hash[RIPEMD160_DIGEST_LENGTH];
    unsigned char extended_ripemd160[25];

    SHA256(public_key, public_key_size, sha256_hash);
    RIPEMD160(sha256_hash, SHA256_DIGEST_LENGTH, ripemd160_hash);

    extended_ripemd160[0] = 0x00;
    memcpy(extended_ripemd160 + 1, ripemd160_hash, RIPEMD160_DIGEST_LENGTH);

    unsigned char checksum[SHA256_DIGEST_LENGTH];
    SHA256(extended_ripemd160, 21, checksum);
    SHA256(checksum, SHA256_DIGEST_LENGTH, checksum);
    memcpy(extended_ripemd160 + 21, checksum, 4);

    base58_encode(extended_ripemd160, 25, address);
}

// Convert hex string to 256-bit number
void hex_to_256bit(const char *hex, unsigned char *output) {
    memset(output, 0, 32);  // Initialize the output to all zeros
    size_t len = strlen(hex);
    size_t start_byte = 32 - len / 2;  // Calculate the starting byte for the conversion

    for (size_t i = 0; i < len; i += 2) {
        char byte[3];
        byte[0] = hex[i];
        byte[1] = hex[i + 1];
        byte[2] = '\0';
        output[start_byte + i / 2] = (unsigned char)strtol(byte, NULL, 16);
    }
}

// Increment a 256-bit number
void increment_256bit(unsigned char *number) {
    for (int i = 31; i >= 0; i--) {
        if (number[i] < 0xFF) {
            number[i]++;
            break;
        } else {
            number[i] = 0;
        }
    }
}

// Check if two 256-bit numbers are equal
int is_equal_256bit(const unsigned char *a, const unsigned char *b) {
    for (int i = 0; i < 32; i++) {
        if (a[i] != b[i]) {
            return 0;
        }
    }
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Usage: %s -A <target_address> -R <start_range>:<end_range>\n", argv[0]);
        return 1;
    }

    char *target_address = argv[2];
    char *range_arg = argv[4];
    char *start_hex = strtok(range_arg, ":");
    char *end_hex = strtok(NULL, ":");

    unsigned char start_val[32] = {0};
    unsigned char end_val[32] = {0};
    hex_to_256bit(start_hex, start_val);
    hex_to_256bit(end_hex, end_val);
    unsigned long long attempts = 0;
    time_t start_time = time(NULL);
    char *log_filename = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-f") == 0 && i + 1 < argc) {
            log_filename = argv[i + 1];
            break;
        }
    }

    FILE *log_file = NULL;
    if (log_filename) {
        log_file = fopen(log_filename, "w");
        if (!log_file) {
            printf("Error opening log file: %s\n", log_filename);
            return 1;
        }
    }

    while (!is_equal_256bit(start_val, end_val)) {
        unsigned char public_key_compressed[33];
        char address_compressed[35];

        private_key_to_public_key(start_val, public_key_compressed);
        public_key_to_address(public_key_compressed, 33, address_compressed);

        if (strcmp(address_compressed, target_address) == 0) {
        printf("\nMatch found!\nPrivate Key: ");
        for (int i = 0; i < 32; i++) {
            printf("%02x", start_val[i]);
        }
        printf("\n");

        if (log_file) {
            fprintf(log_file, "Match found!\nPrivate Key: ");
            for (int i = 0; i < 32; i++) {
                fprintf(log_file, "%02x", start_val[i]);
            }
            fprintf(log_file, "\n");
        }
        break;
    }

        increment_256bit(start_val);
        attempts++;

        if (attempts % 10000 == 0) {  // Update every 10,000 attempts for performance reasons
            time_t current_time = time(NULL);
            double elapsed_seconds = difftime(current_time, start_time);
            double speed = attempts / elapsed_seconds;
            printf("\rAttempts: %llu | Speed: %.2f keys/sec | Latest key: ", attempts, speed);
            for (int i = 0; i < 32; i++) {
                printf("%02x", start_val[i]);
            }
            fflush(stdout);  // Force update the console output
        }
    }

    printf("\n");  // Print a newline at the end for clarity
    if (log_file) {
        fclose(log_file);
    }

    return 0;
}
