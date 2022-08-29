#ifndef _CACHE_H
#define _CACHE_H

#include <stdint.h>


// cache geometry
// ------------------------------
#define SETS (256)
#define WAYS (8)
#define LINE_LEN (16)

//(32 * 1024)
#define CACHE_SIZE (WAYS * SETS * LINE_LEN)


// cache state structure
// ------------------------------
typedef struct cache_state {
  uint8_t evicted[SETS][WAYS];
} cache_state;


// cache interface functions (flushing, priming, probing, comparing, and printing)
// ------------------------------
void flush_cache();
void flush_cache_not_bp();
void cache_func_prime();
void cache_func_probe(cache_state* c);
uint8_t compare_cache(cache_state* c1, cache_state* c2);

void print_cache_state(cache_state* c);
void validate_cache_aligned_memory(char* name, uint64_t addr);

void cache_func_start_clock(cache_state* cache_state);
void cache_func_stop_clock(cache_state* cache_state);
uint8_t compare_cache_time(cache_state* c1, cache_state* c2);
void print_cache_time(cache_state* c);

// utility cache functions (fence and performance counters)
// ------------------------------
#define asm_fence() (asm volatile("fence iorw, iorw"))
uint64_t get_cycles();
uint64_t get_number_dcache_read_misses();
uint64_t get_number_icache_misses();
uint64_t get_number_mispredictions();
void print_perf();


#endif
