import os

def leading_zeros(i: int) -> int:
	count = 0
	while i != 0:
		if i & 1 == 1:
			break
		else:
			count += 1
			i >>= 1
	return count

# constants for the ARM architecture
CACHE_LINE_WIDTH = 64
CACHE_LINE_MASK = ~(CACHE_LINE_WIDTH-1)
CACHE_LINE_SHIFT = leading_zeros(CACHE_LINE_MASK)
PAGE_SIZE = 4096
PAGE_MASK = ~(PAGE_SIZE-1)
PAGE_SHIFT = leading_zeros(PAGE_MASK)
BUS_MASK = 0b00000000000000000000000000110000
BUS_SHIFT = leading_zeros(BUS_MASK) # 4
SET_MASK = 0b00000000000000000001111111000000
SET_SHIFT = leading_zeros(SET_MASK) # 6
TAG_MASK = 0b11111111111111111110000000000000
TAG_SHIFT = leading_zeros(TAG_MASK) # 13

PREFETCH_DELTA_MAX = 4

# number of repetitions for cache tracing experiments
NUM_REPETITIONS = 50

# number of cache lines to probe in the binary
NUM_CACHE_LINES = 17

# Path to the compiled OpenSSL library (e.g. base directory of the openssl git repo)
PATH_OPENSSL = os.path.abspath("../openssl")

# Path to the file containing the GDB commands to execute
PATH_GDB_BATCHFILE = os.path.abspath("./batch.gdb")

# Path to the program executable to trace
PATH_BINARY = os.path.abspath("../victim-bn/build/victim-bn")

# Path to store result logs
PATH_RESULTS = os.path.abspath("./results")
