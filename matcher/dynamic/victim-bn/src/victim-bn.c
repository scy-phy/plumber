#define _GNU_SOURCE

#include <inttypes.h>
#include <openssl/bn.h>

#include "common_test.h"

// The following offsets are used to compute the address of SQR_tb at
// runtime. Since OpenSSL does not export SQR_tb as a symbol, there is no
// way to find the address directly. Therefore, I inspected libcrypto.so
// (objdump -D libcrypto.so), extracted the offset of an exported symbol as
// reference and the offset of SQR_tb.
#define OFFSET_BN_GCD (0x9c500)
#define OFFSET_SQR_TB (0x19f620)

// sum of all elements in SQR_tb should be 680. Will be used to verify that
// the computed address is correct.
#define SQR_TB_EXPECTED_SUM (680)

// Flush & Reload Threshold
#define FNR_THRESHOLD (150)

BIGNUM* make_bn() {
	BIGNUM* bn;
	if (NULL == (bn = BN_new())) {
		fprintf(stderr, "Could not create bignum\n");
		exit(1);
	}
	return bn;
}

int main(int argc, char** argv) {
	// Compute address of SQR_tb
	uint8_t* const SQR_tb_ptr = ((uint8_t*)&BN_gcd) - OFFSET_BN_GCD + OFFSET_SQR_TB;
	uint8_t* const SQR_tb_cl_begin = (uint8_t*)((uintptr_t)SQR_tb_ptr & ~0b111111);
	printf("SQR_tb_ptr:        %p\n", SQR_tb_ptr);
	printf("SQR_tb_ptr offset from cache line begin: %zu\n", (SQR_tb_ptr - SQR_tb_cl_begin));

	// verify the computed address by computing the sum of all elements and
	// comparing it with the expected value.
	{
		uint64_t sum = 0;
		for (size_t i = 0; i < 16; i++) {
			sum += ((uint64_t*)SQR_tb_ptr)[i];;
		}
		if (sum != SQR_TB_EXPECTED_SUM) {
			fprintf(stderr, "SQR_tb did not pass sum validation check. Please check OFFSET_BN_GCD and OFFSET_SQR_TB.\n");
			return 1;
		}
	}

	// cache lines to probe
	uint8_t* const lines_to_probe[] = {
		// lines before SQR_tb
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) - 7*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) - 6*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) - 5*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) - 4*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) - 3*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) - 2*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) - 1*64),
		
		// lines containing SQR_tb
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin)),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128),

		// lines after SQR_tb
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128 + 1*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128 + 2*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128 + 3*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128 + 4*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128 + 5*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128 + 6*64),
		(uint8_t*)(((uintptr_t)SQR_tb_cl_begin) + 128 + 7*64)
	};
	// number of elements in lines_to_probe
	size_t n_lines_to_probe = sizeof(lines_to_probe)/sizeof(lines_to_probe[0]);

	// ensure we have at least one command line argument
	if (argc < 2) {
		fprintf(stderr,
			"Please provide a hexadecimal number to put into bn1 as first "
			"command line parameter. Do not use any prefix (like '0x').\n"
			"Optionally provide the number of a cache line to probe as "
			"second command line parameter.\n"
		);
		return 1;
	}

	// if second command line argument (cache line no. to probe), parse and
	// store it.
	ssize_t line_no = -1;
	if (argc >= 3) {
		line_no = atoll(argv[2]);
	}

	// set up openssl bignum context
	BN_CTX* bn_ctx;
	bn_ctx = BN_CTX_new();
	if (NULL == (bn_ctx = BN_CTX_new())) {
		fprintf(stderr, "Error creating the context.\n");
		return 2;
	}

	// create two BIGNUMs
	BIGNUM* bn1 = make_bn();
	BIGNUM* bn2 = make_bn();
	
	// set bn1 to a specific value (provided by command line argument 1)
	{
		int ret = BN_hex2bn(&bn1, argv[1]);
		if (ret == 0) {
			// error
			fprintf(stderr, "could not parse command line argument 1 as BIGNUM.\n");
			return 1;
		} else {
			// success; echo the resulting value of bn1.
			char* scalar_str = BN_bn2hex(bn1);
			printf("bn hex value: %s\n", scalar_str);
			OPENSSL_free(scalar_str);
		}
	}

	// parameter p is not really relevant for our experiment since it is not involved
	// in the lookup address computation. Just set it to any value that does not crash
	// the program
	const int p[] = {0};

	// before the actual function call to trace, ensure the cache lines
	// around SQR_tb are uncached (if we are probing)
	if (line_no >= 0) {
		for (size_t i = 0; i < n_lines_to_probe; i++) {
			flush(lines_to_probe[i]);
		}
		mfence();
	}

	// call the openssl function to trace
	{
		int ret = BN_GF2m_mod_sqr_arr(bn2, bn1, p, bn_ctx);
		if (ret != 1) {
			fprintf(stderr, "Error in BN_GF2m_mod_sqr_arr, error code: %d\n", ret);
		}
	}

	// cache inspection
	if (line_no >= 0 && line_no < sizeof(lines_to_probe)/sizeof(lines_to_probe[0])) {
		uint64_t time = reload_t(lines_to_probe[line_no]);
		printf("time: %lu (%s)\n", time, time < FNR_THRESHOLD ? "hit" : "miss");
	}

	puts("Execution successful.");

	// cleanup
	BN_free(bn1);
	BN_free(bn2);
	BN_CTX_free(bn_ctx);

	return 0;
}

