#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <openssl/sha.h>
#include <openssl/ripemd.h>
#include <secp256k1.h>
#include <libbase58.h>
#include <time.h>
#include <pthread.h>

#define PRIVATE_KEY_SIZE 32

void base58_encode(unsigned char *bytes, int bytes_len, char *encoded) {
    size_t enc_len = 128;
    b58enc(encoded, &enc_len, bytes, bytes_len);
}

void private_key_to_public_key(const unsigned char *private_key, unsigned char *public_key_compressed, secp256k1_context *ctx) {
    secp256k1_pubkey pubkey;

    if (!secp256k1_ec_pubkey_create(ctx, &pubkey, private_key)) {
        printf("Error creating public key\n");
        return;
    }

    size_t output_length_compressed = 33;
    secp256k1_ec_pubkey_serialize(ctx, public_key_compressed, &output_length_compressed, &pubkey, SECP256K1_EC_COMPRESSED);
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

typedef struct {
    unsigned char start_val[32];
    unsigned char end_val[32];
    char *target_address;
    secp256k1_context *ctx;
} ThreadData;

void *thread_search(void *arg) {
    ThreadData *data = (ThreadData *)arg;
    unsigned char public_key_compressed[33];
    char address_compressed[35];
    unsigned long long attempts = 0;

    while (!is_equal_256bit(data->start_val, data->end_val)) {
    private_key_to_public_key(data->start_val, public_key_compressed, data->ctx);
    public_key_to_address(public_key_compressed, 33, address_compressed);

    if (strcmp(address_compressed, data->target_address) == 0) {
        printf("\nMatch found in thread!\nPrivate Key: ");
        for (int i = 0; i < 32; i++) {
            printf("%02x", data->start_val[i]);
        }
        printf("\n");
        pthread_exit(NULL);  // Exit the thread when a match is found
    }

    increment_256bit(data->start_val);
    attempts++;

    // Display stats every 5,000 attempts (or adjust as needed)
    if (attempts % 5000 == 0) {
        printf("\rThread %lu: %llu attempts. Last key: ", pthread_self(), attempts);
        for (int i = 0; i < 32; i++) {
            printf("%02x", data->start_val[i]);
        }
        fflush(stdout);  // Ensure the line is printed immediately
    }
}
    pthread_exit(NULL);
}


// Subtract two 256-bit numbers: result = a - b
void subtract_256bit(const unsigned char *a, const unsigned char *b, unsigned char *result) {
    int borrow = 0;
    for (int i = 31; i >= 0; i--) {
        int diff = a[i] - b[i] - borrow;
        if (diff < 0) {
            diff += 256;
            borrow = 1;
        } else {
            borrow = 0;
        }
        result[i] = (unsigned char)diff;
    }
}

// Add two 256-bit numbers: result = a + b
void add_256bit(const unsigned char *a, const unsigned char *b, unsigned char *result) {
    int carry = 0;
    for (int i = 31; i >= 0; i--) {
        int sum = a[i] + b[i] + carry;
        result[i] = (unsigned char)sum;
        if (sum > 255) {
            carry = 1;
        } else {
            carry = 0;
        }
    }
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

    secp256k1_context *ctx = secp256k1_context_create(SECP256K1_CONTEXT_SIGN);
    if (!ctx) {
        printf("Failed to create secp256k1 context.\n");
        return 1;
    }

    // Define the number of threads
    int num_threads = 4;  // Adjust as needed
    pthread_t threads[num_threads];
    ThreadData thread_data[num_threads];

    // Divide the range among the threads
    for (int i = 0; i < num_threads; i++) {
        memcpy(thread_data[i].start_val, start_val, 32);

        // Calculate the end value for this thread
        unsigned char total_range[32];
        subtract_256bit(end_val, start_val, total_range);
        thread_data[i].ctx = ctx;  // Set the context for this thread
        thread_data[i].target_address = target_address;  // Set the target address for this thread

        unsigned char sub_range[32] = {0};
        unsigned char quotient = total_range[31] / num_threads;
        unsigned char remainder = total_range[31] % num_threads;
        sub_range[31] = quotient;
        if (i < remainder) {
            increment_256bit(sub_range);
        }

        unsigned char end_for_this_thread[32];
        add_256bit(start_val, sub_range, end_for_this_thread);
        if (i == num_threads - 1) {
            // Ensure the last thread goes up to the end value
            memcpy(end_for_this_thread, end_val, 32);
        }

        memcpy(thread_data[i].end_val, end_for_this_thread, 32);
        memcpy(start_val, end_for_this_thread, 32);
    }

    // Create the threads
    for (int i = 0; i < num_threads; i++) {
        pthread_create(&threads[i], NULL, thread_search, &thread_data[i]);
    }

    // Wait for all threads to finish
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    secp256k1_context_destroy(ctx);

    return 0;
}

