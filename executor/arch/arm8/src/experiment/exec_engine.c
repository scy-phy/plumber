#include "config.h"

#ifdef RUN_CACHE

#include "lib/printf.h"
#include "mmu.h"
#include "cache.h"

#include "experiment/exp_cache_runner.h"


#define __UNUSED __attribute__((unused))
#define __ALIGN(x) __attribute__ ((aligned (x)))
#define PAGE_SIZE (4096)
/* page table memory */
uint64_t page_table_l1[4] __ALIGN(PAGE_SIZE);

void reset_cache_experiment() {
  disable_mmu();
}

static void basic_mmu() {
  init_mmu();
  set_l1(page_table_l1);
  // Set up translation table entries in memory with looped store
  // instructions.
  // Set the level 1 translation table.
  l1_set_translation(page_table_l1, 0, 0, 0);
  l1_set_translation(page_table_l1, 0x40000000, 0, 0);
  // Executable Inner and Outer Shareable.
  // R/W at all ELs secure memory
  // AttrIdx=000 Device-nGnRnE.
  // The third entry is 1GB block from 0x80000000 to 0xBFFFFFFF.
  l1_set_translation(page_table_l1, 0x80000000, 0, 1);
  //l1_set_translation(page_table_l1, 0xC0000000, 0, 1);

  // TODO: dirty quick fix for rpi4, overwrites the last mapping, second cacheable alias
  l1_set_translation(page_table_l1, 0xC0000000, 0xC0000000, 0);

  enable_mmu();
}

#define CACHEABLE(x) ((void *)(((uint64_t)(&x)) + 0x80000000))
#define ALIAS(x)     ((void *)(((uint64_t)(&x)) + 0x40000000))


/* static cache_state cache; */

#ifndef SINGLE_EXPERIMENTS
void run_cache_experiment() {
  // setup and enable mmu
  basic_mmu();


#ifdef __MEASUREMENT__CACHE
  flush_d_cache(0); // flush L1
  flush_d_cache(1); // flush L2
 
  static cache_state cache1;
  // static cache_l2_state cache2;

  cache_run_mult_compare(1, cache1, NUM_MUL_RUNS);
  // save_cache_l2_state(cache2);
  print_cache_valid(cache1);
  // print_cache_l2_valid(cache2);
#endif


#ifdef __MEASUREMENT__BRANCH_PREDICTOR
  branch_rev();
#endif
 
}
#endif // !SINGLE_EXPERIMENTS

#endif // RUN_CACHE
