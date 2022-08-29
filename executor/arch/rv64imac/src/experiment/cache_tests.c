#include "config.h"
#ifdef RUN_CACHE
#include "lib/printf.h"
#include "cache.h"
#include <stdint.h>

#include "experiment/exp_cache_runner.h"

#define __UNUSED __attribute__((unused))
#define __ALIGN(x) __attribute__ ((aligned (x)))
#define PAGE_SIZE (4096)
// Need to tinker this dependingon start area. +0x20000000 assumes for 0x80000000.
#define CACHEABLE(x) ((void *)(((uint64_t)(&x)) + 0x20000000))
#define ALIAS(x)     ((void *)(((uint64_t)(&x)) + 0x00000000))

// Changed for RISC-V, Ariane.
// Only for RUN_1EXPS at the moment.

void reset_cache_experiment() {
  // Only runs when the board is starting.
}

// allocated data for cache state data structures
#ifdef RUN_2EXPS
static cache_state cache1;
static cache_state cache2;
#elif defined RUN_1EXPS
static cache_state cache;
#else
  #error "no experiment type selected"
#endif

extern volatile uint8_t _experiment_memory;
extern volatile uint8_t _probing_memory;

#ifndef SINGLE_EXPERIMENTS
void run_cache_experiment() {
  uint16_t diff = 0;

  //remove This
  cache_exp_all();


  validate_cache_aligned_memory("_experiment_memory", (uint64_t)&_experiment_memory);
  validate_cache_aligned_memory("_probing_memory", (uint64_t)&_probing_memory);

#ifdef RUN_2EXPS
  // run 2 cache experiments
  diff += cache_run_mult_compare(1, &cache1, NUM_MUL_RUNS);
  //  print_cache_valid(cache1);
  diff += cache_run_mult_compare(2, &cache2, NUM_MUL_RUNS);
  //  print_cache_valid(cache2);
  //debug_set(cache1[0], 0);
  //debug_set(cache2[0], 0);

#ifdef RUN_CACHE_MULTIW
  #define CACHE_EQ_FUN compare_cache_bounds
  #define CACHE_SET_LOWER 0
  #define CACHE_SET_UPPER (SETS)
#elif defined RUN_CACHE_MULTIW_NUMINSET
  #define CACHE_EQ_FUN compare_cache_num_bounds
  #define CACHE_SET_LOWER 0
  #define CACHE_SET_UPPER (SETS)
#elif defined RUN_CACHE_MULTIW_SUBSET
  #define CACHE_EQ_FUN compare_cache_bounds
  #define CACHE_SET_LOWER (((SETS)/2)-3)
  #define CACHE_SET_UPPER (SETS)
#elif defined RUN_CACHE_MULTIW_SUBSET_PAGE_BOUNDARY
  #define CACHE_EQ_FUN compare_cache_bounds
  #define CACHE_SET_LOWER ((SETS)/2)
  #define CACHE_SET_UPPER (SETS)
#else
  #error "no cache experiment parameters selected"
#endif
  if (diff == 0) {
    // compare and print result of comparison
    if (CACHE_EQ_FUN(&cache1, &cache2, CACHE_SET_LOWER, CACHE_SET_UPPER) == 0)
      printf("RESULT: EQUAL\n");
    else
      printf("RESULT: UNEQUAL\n");
  } else {
    printf("INCONCLUSIVE: %d\n", diff);
  }
#elif defined RUN_1EXPS
  diff += cache_run_mult_compare(1, &cache, NUM_MUL_RUNS);
  print_cache_state(&cache);
  if (diff != 0)
    printf("INCONCLUSIVE: %d\n", diff);
#else
  #error "no experiment type selected"
#endif
}
#endif // !SINGLE_EXPERIMENTS

#endif // RUN_CACHE
