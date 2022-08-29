// TODO
// ------------------------------------------------------------------------
// todo: Move non-experiment code to another file, like test cases. Include this file should be enough?
// Do I want the results in appendix? The code can be linked from thesis to github. Maybe only use prime and probe code in report.
// The results of the test cases ( cache_exp_all() ), can be found in the appendix of the thesis.


#include <stdint.h>

#include "cache.h"
#include "lib/printf.h"

uint8_t probe_set_way_miss(int set, int way);

// basic experiments
// ------------------------------------------------------------------------
void check_cacheability_print(uint8_t flushfirst, uint64_t addr) {
  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;

  if (flushfirst) {
    asm volatile(
     //".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw\n"
     ".word 0xfffff00b\n"
     "fence iorw, iorw\n");
  }

  asm volatile(
     //".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lb t0, 0(%2);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     "fence iorw, iorw;\n"
     : "=r"(dcache_misses0), "=r"(cycles0)
     : "r"(addr)
     :
   );
   printf("[Exp time: l1dc miss: %d, cycles: %d. Address: 0x%x] \n", dcache_misses0, cycles0, addr);
}

uint8_t load8now(uint64_t addr) {
  uint8_t v;
  asm volatile(
     "lb %0, 0(%1)"
     : "=r"(v)
     : "r"(addr)
     :
   );
  return v;
}

uint8_t load8now2(uint64_t addr) {
  uint8_t volatile * p = (uint8_t volatile *) addr;
  uint8_t v = *p;
  return v;
}

uint8_t load8now3(uint64_t addr) {
  volatile uint8_t * p = (uint8_t *) addr;
  *p;
  return 0;
}

uint8_t check_address_is_in_cache2(uint64_t x){
  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;

  flush_cache();


  uint64_t addr1_0 = 0x90000000;
  uint64_t addr2_0 = 0xA0000000;


  printf("\n\n\n");

  printf("\nprime:\n");
  for (int i = 0; i < 8; i++) {
    //uint64_t addr = addr2_0 + (i * SETS * LINE_LEN);
    //volatile uint8_t * p = (uint8_t *) addr;
    // *p;
    //load8now3(addr);
    //printf("0x%x\n", addr);
    //prime_set_way(0, i);
    printf("%d\n", probe_set_way_miss(0, i));
    //check_cacheability_print(0, addr);
  }

  printf("\nvictim:\n");
  check_cacheability_print(0, addr1_0);
  check_cacheability_print(0, addr2_0);
  check_cacheability_print(0, addr1_0);
  check_cacheability_print(0, addr1_0);

  printf("\nprobe:\n");
  for (int i = 0; i < 8; i++) {
    printf("%d\n", probe_set_way_miss(0, i));
    //check_cacheability_print(0, addr2_0 + (i * SETS * LINE_LEN));
  }


  printf("\n\n\n");

/*
  printf("\n\n\n");

  volatile uint8_t* _experiment_memory = (uint8_t*)0xA0000000;

#define addr_of_way(way) (way * SETS * LINE_LEN)

  for (int way = 0; way < 1; way++) {
    uint64_t addr = addr_of_way(way%1);
    printf("addr = 0x%x (0x%x)\n", addr, _experiment_memory+addr);
    volatile uint8_t* pxyz = _experiment_memory+addr;
    *pxyz;
    // *(_experiment_memory + addr) = 1;
  }
  x = (uint64_t) _experiment_memory;

  check_cacheability_print(0, x);
  printf("\n\n\n");
*/
  asm volatile(
     //"0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "fence iorw, iorw;\n"
     "lw t0, 0(%2);\n"
     "fence iorw, iorw;\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     "fence iorw, iorw;\n"
     : "=r"(dcache_misses0), "=r"(cycles0)
     : "r"(x)
     :
   );

   printf("[Exp time: l1dc miss: %d, cycles: %d. Address: 0x%x] \n", dcache_misses0, cycles0, x);
  printf("\n\n\n");
   if(dcache_misses0){ // 1 == true
     return 0; // if miss, it is in not in cache
   }else{
     return 1; // if hit, it was in the cache
   }
}

uint8_t check_address_is_in_cache(uint64_t x){
  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;

  asm volatile(
     //"0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 0(%2);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     "fence iorw, iorw;\n"
     : "=r"(dcache_misses0), "=r"(cycles0)
     : "r"(x)
     :
   );
   if(dcache_misses0){ // 1 == true
     return 0; // if miss, it is in not in cache
   }else{
     return 1; // if hit, it was in the cache
   }
}

// experiment definitions
// ------------------------------------------------------------------------


#define __UNUSED __attribute__((unused))
#define __ALIGN(x) __attribute__ ((aligned (x)))
#define CACHEABLE(x) ((void *)(((uint64_t)(&x)) + 0x1c000090))
#define CACHEABLE2(x) ((void *)(((uint64_t)(&x)) + 0x20000000))
#define UNCACHEABLE(x) ((void *)(((uint64_t)(&x)) - 0x20000000))

// reserved memory used for basic experiments
uint64_t memory[CACHE_SIZE * 8 / 8] __ALIGN(CACHE_SIZE);
uint64_t somevalue = 512;

// experiments and test cases START
// ------------------------------------------------------------------------

void cache_exp_primeandprobe_two_executions(){
  printf("experiment: cache_exp_primeandprobe_two_executions\n");
  cache_state cache_state0;
  cache_state cache_state1;

  flush_cache(); // remove flush if not testing.
  cache_func_prime();
  // Arbitary Access
  volatile uint64_t xNew = 0;
  xNew = 0x1337;
  // access a cacheable value
  volatile uint64_t * xPNew = (uint64_t * )CACHEABLE2(xNew);
  __UNUSED uint8_t tmp = *xPNew;
    printf("address accessed: %x\n", xPNew);
  cache_func_probe(&cache_state0);


  printf("saved cache, flushing and executing again...\n");
  flush_cache(); // remove flush if not testing.
  cache_func_prime();
  // Arbitary Access
  volatile uint64_t yNew = 0;
  yNew = 0x1337;
  // access a cacheable value
  volatile uint64_t * yPNew = (uint64_t * )CACHEABLE2(yNew);
  tmp = *yPNew;
    printf("address accessed: %x\n", yPNew);
  cache_func_probe(&cache_state1);

  printf("saved cache, comparing cache...\n");
  uint8_t equal = compare_cache(&cache_state0, &cache_state1);
  if(equal){
    printf("Equal caches.\n");
  }else{
    printf("Unequal caches.\n");
  }
  // print the sets
  printf("rinting cache...\n");
  printf("cache_state0:\n");
  print_cache_state(&cache_state0);
  printf("cache_state1:\n");
  print_cache_state(&cache_state1);
}

void cache_exp_primeandprobe(){
  printf("experiment: cache_exp_primeandprobe\n");
  flush_cache(); // remove flush if not testing.

  cache_state cache_state;

  cache_func_prime();

  // Arbitary Access
  volatile uint64_t xNew = 0;
  xNew = 0x1337;
  // access a cacheable value
  volatile uint64_t * xPNew = (uint64_t * )CACHEABLE2(xNew);
  __UNUSED uint8_t tmp = *xPNew;
  printf("address accessed: %x\n", xPNew);

  // This is probe
  cache_func_probe(&cache_state);
  print_cache_state(&cache_state);
}

void cache_exp_primeandprobe_no_access(){
  printf("experiment: cache_exp_primeandprobe_no_access\n");
  flush_cache(); // remove flush if not testing.

  cache_state cache_state;

  cache_func_prime();

  // Arbitary Access

  // This is probe
  cache_func_probe(&cache_state);
  print_cache_state(&cache_state);
}

void test_value_in_cache() {
  // Basically shows that two accesses to the same memory address within the cacheable area will cause a miss and then a hit.

  printf("experiment: test_value_in_cache\n");
  //Modified from cache_experiment.c
  // check memory alias
  flush_cache();

  uint64_t addr2_0 = 0xA0000000;
  check_cacheability_print(0, addr2_0);
  check_cacheability_print(0, addr2_0);

}

void test_value_in_cache2() {
  // Basically shows that two accesses to the same memory address within the cacheable area will cause a miss and then a hit.
  printf("experiment: test_value_in_cache2\n");
  //Modified from cache_experiment.c
  // check memory alias

  // access a cacheable value
  flush_cache();

  uint64_t addr = 0xA0000000;
  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;

  asm volatile(
     //"0xfffff00b;\n" //fence.t
     "fence iorw, iorw\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lb t0, 0(%2);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     "fence iorw, iorw;\n"
     : "=r"(dcache_misses0), "=r"(cycles0)
     : "r"(addr)
     :
   );
   printf("[Exp time: l1dc miss: %d, cycles: %d. Address: 0x%x] \n", dcache_misses0, cycles0, addr);

   asm volatile(
      //"0xfffff00b;\n" //fence.t
      "fence iorw, iorw\n"
      "csrr t1, 0xb04;\n"
      "csrr t2, 0xb00;\n"
      "lb t0, 0(%2);\n"
      "csrr t3, 0xb00;\n"
      "csrr t4, 0xb04;\n"
      "sub %0, t4, t1;\n"
      "sub %1, t3, t2;\n"
      "fence iorw, iorw;\n"
      : "=r"(dcache_misses0), "=r"(cycles0)
      : "r"(addr)
      :
    );
    printf("[Exp time: l1dc miss: %d, cycles: %d. Address: 0x%x] \n", dcache_misses0, cycles0, addr);

}

void test_value_in_cache3() {
  // Basically shows that two accesses to the same memory address within the cacheable area will cause a miss and then a hit.
  printf("experiment: test_value_in_cache3\n");
  //Modified from cache_experiment.c
  // check memory alias
  volatile uint64_t x = 0;
  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;

  flush_cache();

  // access a cacheable value
  volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory);

  for(int i = 0; i < 10; i++){
  asm volatile(
     //"0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "fence iorw, iorw;\n"
     "lb t0, 0(%2);\n"
     "fence iorw, iorw;\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     "fence iorw, iorw;\n"
     : "=r"(dcache_misses0), "=r"(cycles0)
     : "r"(xP)
     :
   );
   printf("[Exp time: l1dc miss: %d, cycles: %d. Address: 0x%x]", dcache_misses0, cycles0, xP);
   }

   //printf("[Exp time: l1dc miss: %d, cycles: %d. Address: 0x%x] \n", dcache_misses0, cycles0, xP);

   if(dcache_misses1 == 0){
     printf(" x is in the cache \n");
   }else{
     printf(" x is NOT in the cache \n");
   }

}

void cache_exp_miss_and_hit_from_base(){
  printf("experiment: cache_exp_miss_and_hit_from_base\n");
  // cache_exp_miss_and_hit_from_base(); // This test shows miss and miss, when starting at 8000 0000, in uncacheable area
  uint64_t dcache_misses0;
  uint64_t dcache_misses1;
  uint64_t cycles0;
  uint64_t cycles1;



  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 256(sp);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 256(sp);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %2, t4, t1;\n"
     "sub %3, t3, t2;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(dcache_misses1), "=r"(cycles1)
     :
     :
   );

  printf("[First load: l1dc miss: %d, cycles: %d.] [Second load: l1dc miss: %d, cycles: %d.] \n", dcache_misses0, cycles0, dcache_misses1, cycles1);
}

void cache_exp_miss_and_hit_from_cacheable(){
  printf("experiment: cache_exp_miss_and_hit_from_cacheable\n");
  // cache_exp_miss_and_hit_from_base(); // This test shows miss and miss, when starting at 8000 0000, in uncacheable area
  uint64_t dcache_misses0;
  uint64_t dcache_misses1;
  uint64_t cycles0;
  uint64_t cycles1;
    volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory);

  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 0(%4);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 0(%4);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %2, t4, t1;\n"
     "sub %3, t3, t2;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(dcache_misses1), "=r"(cycles1)
     :"r"(xP)
     :
   );

  printf("[First load: l1dc miss: %d, cycles: %d.] [Second load: l1dc miss: %d, cycles: %d.] \n", dcache_misses0, cycles0, dcache_misses1, cycles1);
}

void cache_exp_timings_instructions(){
  printf("experiment: cache_exp_timings_instructions\n");
  // Tests Timings
  // OUTPUT:
  // experiment: cache_exp_timings_instructions
  // timing: fence
  // [Fence Instruction: cycles: 124.]
  // timing: flush
  // [Flush Instruction: cycles: 381.]
  // timing: load (no fence)
  // [Load (no fence): cycles: 49.]
  // timing: load (fence before and after)
  // [Load (fence before and after): cycles: 233.]
  // timing: load fence measure add measure
  // [load fence measure add measure: between load cycles: 102, between add cycles: 62..]

  uint64_t dcache_misses0;
  uint64_t dcache_misses1;
  uint64_t cycles0;
  uint64_t cycles1;
  volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory);

  printf("timing: fence\n");
  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t2, 0xb00;\n"
     "fence iorw, iorw;\n"
     "csrr t3, 0xb00;\n"
     "sub %0, t3, t2;\n"
     : "=r"(cycles0)
     :
     :
   );
  printf("[Fence Instruction: cycles: %d.]\n", cycles0);

  printf("timing: flush\n");
  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t2, 0xb00;\n"
     ".word 0xfffff00b;\n" //fence.t
     "csrr t3, 0xb00;\n"
     "sub %0, t3, t2;\n"
     : "=r"(cycles0)
     :
     :
   );
  printf("[Flush Instruction: cycles: %d.]\n", cycles0);

  printf("timing: load (no fence, from sp)\n");
  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 0(sp);\n"
     "csrr t3, 0xb00;\n"
     "sub %0, t3, t2;\n"
     : "=r"(cycles0)
     :
     :
   );
  printf("[Load (no fence, from sp)): cycles: %d.] \n", cycles0);

  printf("timing: load (fence before and after)\n");
  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t2, 0xb00;\n"
     "fence iorw, iorw;\n"
     "lw t0, 0(sp);\n"
     "fence iorw, iorw;\n"
     "csrr t3, 0xb00;\n"
     "sub %0, t3, t2;\n"
     : "=r"(cycles0)
     :
     :
   );
  printf("[Load (fence before and after): cycles: %d.] \n", cycles0);

  printf("timing: load fence measure add measure\n");
  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 0(sp);\n"
     "fence iorw, iorw;\n"
     "csrr t3, 0xb00;\n"
     "addi t0, t0, 1;\n"
     "csrr t4, 0xb00;\n"
     "sub %0, t3, t2;\n"
     "sub %1, t4, t3;\n"
     : "=r"(cycles0), "=r"(cycles1)
     :
     :
   );
  printf("[load fence measure add measure: between load cycles: %d, between add cycles: %d..] \n", cycles0, cycles1);


}


void test_two_ways() {
  // Shows that the 2 accesses to the same set are in the cache.
  printf("experiment: test_two_ways\n");
  //Modified from cache_experiment.c
  //Note experiment memory not changed at all, yet.
  flush_cache();
  cache_state cache_state;
  cache_func_prime();
  uint64_t a1 = 0;
  uint64_t a2 = a1 + CACHE_SIZE * 1 / 8;

  memory[a1] = 0x123;
  memory[a2] = 0x456;



  volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory[a1]);
  printf("addresses %x %x %x \n", &(memory[a1]), &(memory[a2]), xP);
  volatile uint64_t x = *(xP);
  volatile uint64_t * yP = (uint64_t * )CACHEABLE2(memory[a2]);
  volatile uint64_t y = *(yP);

  cache_func_probe(&cache_state);
  print_cache_state(&cache_state);

}

void test_eight_ways() {
  // // Shows that the 8 accesses to the same set are in the cache.
  printf("experiment: test_eigth_ways\n");
  //Modified from cache_experiment.c
  //Note experiment memory not changed at all, yet.
  flush_cache();


  uint64_t aarry[8];

  aarry[0] = 0;
  memory[0] = 0x123;
  for(int i = 1; i < 8; i++){
    aarry[i] = aarry[i-1] + CACHE_SIZE * i / 8;
    memory[aarry[i]] = memory[aarry[i-1]] + 0x123;
  }

  printf("addresses ");
  for(int i = 0; i < 8; i++){
    printf("%x ", &(memory[aarry[i]]));
  }
  printf("\n");

  printf("values ");
  for(int i = 0; i < 8; i++){
    volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory[aarry[i]]);
    volatile uint64_t x = *(xP);
    printf("%x ", x);
  }
  printf("\n");

  for(int i = 0; i < 8; i++){
    volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory[aarry[i]]);
    if(check_address_is_in_cache((uint64_t)(xP))){
      printf(" a%d is in the cache. ", i);
    }else{
      printf(" a%d is NOT in the cache. ", i);
    }
  }
  printf("\n");
  // cache_func_probe(&cache_state);
  // print_cache_state(&cache_state);
}

void test_nine_ways() {
  printf("experiment: test_nine_ways\n");
  // Shows that the 9 accesses to the same set are NOT all in the cache.
  // this case will cause more cache misses than thought due to the checking for cache hits

  //Modified from cache_experiment.c
  //Note experiment memory not changed at all, yet.
  flush_cache();

  uint64_t aarry[9];

  aarry[0] = 0;
  memory[0] = 0x123;
  for(int i = 1; i < 9; i++){
    aarry[i] = aarry[i-1] + CACHE_SIZE * i / 8;
    memory[aarry[i]] = memory[aarry[i-1]] + 0x123;
  }

  printf("addresses ");
  for(int i = 0; i < 9; i++){
    printf("%x ", &(memory[aarry[i]]));
  }
  printf("\n");

  printf("values ");
  for(int i = 0; i < 9; i++){
    volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory[aarry[i]]);
    volatile uint64_t x = *(xP);
    printf("%x ", x);
  }
  printf("\n");

  for(int i = 0; i < 9; i++){
    volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory[aarry[i]]);
    if(check_address_is_in_cache((uint64_t)(xP))){
      printf(" a%d is in the cache. ", i);
    }else{
      printf(" a%d is NOT in the cache. ", i);
    }
  }
  printf("\n");

  // cache_func_probe(&cache_state);
  // print_cache_state(&cache_state);
}


void cache_exp_flushinbetween(){
  printf("experiment: cache_exp_flushinbetween\n");
  uint64_t dcache_misses0;
  uint64_t dcache_misses1;
  uint64_t cycles0;
  uint64_t cycles1;

  asm volatile(
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 256(sp);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %0, t4, t1;\n"
     "sub %1, t3, t2;\n"
     ".word 0xfffff00b;\n" //fence.t
     "fence iorw, iorw;\n"
     "csrr t1, 0xb04;\n"
     "csrr t2, 0xb00;\n"
     "lw t0, 256(sp);\n"
     "csrr t3, 0xb00;\n"
     "csrr t4, 0xb04;\n"
     "sub %2, t4, t1;\n"
     "sub %3, t3, t2;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(dcache_misses1), "=r"(cycles1)
     :
     :
   );

  printf("[First load: l1dc miss: %d, cycles: %d.] [Second load: l1dc miss: %d, cycles: %d.] \n", dcache_misses0, cycles0, dcache_misses1, cycles1);
}

void cache_exp_mispredict_counters_0(){
  printf("experiment: cache_exp_mispredict_counters_0\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
     :
     :
   );

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
     :
     :
   );

   printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);
}

void cache_exp_mispredict_counters_loop(){
  printf("experiment: cache_exp_mispredict_counters_loop\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
     :
     :
   );

   int i,j;
   int c = 0;
   for(i = 0; i < 1000; i++){
     for (j = 0; j < 4; j++) {
       c++;
     }
   }

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
     :
     :
   );

   printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);
}

void cache_exp_mispredict_counters_if_1(){
  printf("experiment: cache_exp_mispredict_counters_if_1\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
     :
     :
   );

 int i = 0;
 int j = 0;
 if(i == j){
   i++;
 }
 if(i != j){
   i++;
 }

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
     :
     :
   );

   printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);
}

void cache_exp_mispredict_counters_if_2(){
  printf("experiment: cache_exp_mispredict_counters_if_2\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
     :
     :
   );

 int i = 0;
 int j = 0;
 if(i == j){
   i++;
 }
 if(i == j){
   i++;
 }
  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
     :
     :
   );

   printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);
}

void cache_exp_mispredict_counters_load(){
  printf("experiment: cache_exp_mispredict_counters_load\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;



  memory[0] = 0x456;
  volatile uint64_t * xP = (uint64_t * )CACHEABLE2(memory[0]);


  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
     :
     :
   );

 int i = 0;
 int j = 0;
 if(i == j){
   i++;
 }
 if(i != j){
   uint64_t x = *(xP);
 }

  asm volatile(
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
     : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
     :
     :
   );

   printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);
}


uint64_t cache_helper_spec2_noload(int value, uint64_t* x){
  uint64_t tmp = 0;
  //printf("%x\n", (x+value));
  tmp = memory[3];
  if(value > 256){
    //tmp = *(x);
    tmp = 1;
  }
  //printf("%d\n", tmp);
  return tmp;
}

void cache_exp_mispredict_counters_speculative_noload(){
  //experiment: cache_exp_mispredict_counters_speculative_load
  printf("experiment: cache_exp_mispredict_counters_speculative_noload\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;

  uint64_t * xP = (uint64_t * )CACHEABLE2(memory[0]);

  uint64_t abc = 100;
   abc=260;
   for(int i = 0; i < 10; i++){
    cache_helper_spec2_noload(abc,xP);
    }
  abc=64;

  flush_cache_not_bp();

  cache_state cache_state;
  cache_func_prime();

  asm volatile(
    "fence iorw, iorw;\n"
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
    "fence iorw, iorw;\n"
     : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
     :
     :
   );

   cache_helper_spec2_noload(abc,xP);

  asm volatile(
    "fence iorw, iorw;\n"
    "csrr %2, 0xb0e;\n"
    "csrr %0, 0xb04;\n"
    "csrr %1, 0xb00;\n"
    "fence iorw, iorw;\n"
     : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
     :
     :
   );

   printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);

   cache_func_probe(&cache_state);
   print_cache_state(&cache_state);
}

uint64_t cache_helper_spec2(int value, uint64_t* x){
  uint64_t tmp = 0;
  //printf("%x\n", (x+value));
  tmp = memory[3];
  if(value > 256){
    tmp = *(x);
  }
  //printf("%d\n", tmp);
  return tmp;
}

void cache_exp_mispredict_counters_speculative_load(){
  //experiment: cache_exp_mispredict_counters_speculative_load
  /*
  experiment: cache_exp_mispredict_counters_speculative_load
[Exp time: l1dc miss: 0, cycles: 979, mispredicts: 2.]
experiment: cache_exp_mispredict_counters_speculative_noload
[Exp time: l1dc miss: 0, cycles: 979, mispredicts: 2.]
  */

  printf("experiment: cache_exp_mispredict_counters_speculative_load\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;


  uint64_t * xP = (uint64_t * )CACHEABLE2(memory[0]);

  uint64_t abc = 100;
  memory[3] = 5;
   abc=260;
   for(int i = 0; i < 10; i++){
    cache_helper_spec2(abc,xP);
    }
  abc=64;

  flush_cache_not_bp();

    cache_state cache_state;
    cache_func_prime();

    // asm volatile(
    //   "fence iorw, iorw;\n"
    //   "csrr %2, 0xb0e;\n"
    //   "csrr %0, 0xb04;\n"
    //   "csrr %1, 0xb00;\n"
    //   "fence iorw, iorw;\n"
    //    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    //    :
    //    :
    //  );

     cache_helper_spec2(abc,xP);

   //  asm volatile(
   //    "fence iorw, iorw;\n"
   //    "csrr %2, 0xb0e;\n"
   //    "csrr %0, 0xb04;\n"
   //    "csrr %1, 0xb00;\n"
   //    "fence iorw, iorw;\n"
   //     : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
   //     :
   //     :
   //   );
   //
   // printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);
   int tmp;
   for(int i = 0; i < 1000; i++){
     tmp++;
   }
   cache_func_probe(&cache_state);
   print_cache_state(&cache_state);

}


void cache_helper_spec3(int value, uint64_t* x){
  // change default, try to train
  asm volatile(
    "addi t0, x0, 0;\n"
    "addi t1, x0, 0;\n"
    "sw t1,  0(t0);\n"
    "add t1, x0, %1;\n"
    "sw t1,  16(t0);\n"
    "lw t4,  0(t0);\n"
    "lw t5, 16(t0);\n"
    "bne t4, t5, viktorscrazylabel2;\n"
    "lb t1, 256(%0);\n"
    "viktorscrazylabel2:;\n"
    "nop;"
     :
     : "r"(x), "r"(value)
     :
   );
}

void cache_exp_mispredict_counters(){
  // if abc = 266;
// experiment: cache_exp_mispredict_counters_train2
// [Exp time: l1dc miss: 1, cycles: 996, mispredicts: 1.]
// set 16
// - way 0
// - way 5

//
//
// if abc = 0;
// experiment: cache_exp_mispredict_counters_train2
// [Exp time: l1dc miss: 1, cycles: 996, mispredicts: 1.]
// set 16
// - way 0
// - way 6


  printf("experiment: cache_exp_mispredict_counters_spec\n");

  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;


  uint64_t * xP = (uint64_t * )CACHEABLE2(memory[0]);
  // uint64_t * goodValue = &memory[1];
  // memory[1] = 123;
  //
   uint64_t abc = 266;
   abc=123;
   for(int i = 0; i < 10; i++){
    cache_helper_spec2(abc,xP);
    }

     abc=0; //if this is commented, onlt 1 mispredict

    flush_cache_not_bp();


    cache_state cache_state;
    cache_func_prime();

    cache_helper_spec3(abc,xP);

   cache_func_probe(&cache_state);
   print_cache_state(&cache_state);
}

// Initial tests to examine speculative execution

void inputfunction(int x) {
 asm volatile(
   "la t0, _experiment_memory;\n"
   "li t1, 4;\n"
   "sd t1, 48(t0);\n"
   "sd %0, 80(t0);\n"
    :
    : "r"(x)
    :
  );
}

void victim_function_noload_nofences() {
  uint64_t dcache_misses0 = 0;
  uint64_t mispredicts = 0;
  uint64_t cycles0 = 0;

 asm volatile(
   "la t0, _experiment_memory;\n"
   "fence iorw, iorw;\n"
   "csrr t5, 0xb0e;\n"
   "csrr a6, 0xb04;\n"
   "csrr a5, 0xb00;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "ld t4, 48(t0);\n"
   "ld t1, 80(t0);\n"

   "blt t4, t1, label_noloadf;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "label_noloadf:\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "csrr t3, 0xb0e;\n"
   "csrr a3, 0xb04;\n"
   "csrr a2, 0xb00;\n"

   "sub %0, a3, a6;\n"
   "sub %1, a2, a5;\n"
   "sub %2, t3, t5;\n"

   "fence iorw, iorw;\n"
    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    :
    :
  );
  printf("[Exp time from asm: l1dc miss: %d, cycles: %d. mispredicts: %d] \n", dcache_misses0, cycles0, mispredicts);
}

void victim_function_noload_uncond() {
  uint64_t dcache_misses0 = 0;
  uint64_t mispredicts = 0;
  uint64_t cycles0 = 0;

 asm volatile(
   "la t0, _experiment_memory;\n"

   "fence iorw, iorw;\n"
   "csrr t5, 0xb0e;\n"
   "csrr a6, 0xb04;\n"
   "csrr a5, 0xb00;\n"
   "fence iorw, iorw;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "ld t4, 48(t0);\n"
   "ld t1, 80(t0);\n"

   "blt t4, t1, label_consuming;\n"
   "j label_end;\n"

   "label_consuming:\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "label_end:\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "fence iorw, iorw;\n"
   "csrr t3, 0xb0e;\n"
   "csrr a3, 0xb04;\n"
   "csrr a2, 0xb00;\n"
   "fence iorw, iorw;\n"

   "sub %0, a3, a6;\n"
   "sub %1, a2, a5;\n"
   "sub %2, t3, t5;\n"

   "fence iorw, iorw;\n"
    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    :
    :
  );
  printf("[Exp time from asm: l1dc miss: %d, cycles: %d. mispredicts: %d] \n", dcache_misses0, cycles0, mispredicts);
}

void victim_function_uncond() {
  uint64_t dcache_misses0 = 0;
  uint64_t mispredicts = 0;
  uint64_t cycles0 = 0;

 asm volatile(
   "la t0, _experiment_memory;\n"

   "fence iorw, iorw;\n"
   "csrr t5, 0xb0e;\n"
   "csrr a6, 0xb04;\n"
   "csrr a5, 0xb00;\n"
   "fence iorw, iorw;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "ld t4, 48(t0);\n"
   "ld t1, 80(t0);\n"

   "blt t4, t1, label_consumingl;\n"
   "j label_endl;\n"

   "label_consumingl:\n"
   "ld t6, 0(t0);\n"

   "label_endl:\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "fence iorw, iorw;\n"
   "csrr t3, 0xb0e;\n"
   "csrr a3, 0xb04;\n"
   "csrr a2, 0xb00;\n"
   "fence iorw, iorw;\n"

   "sub %0, a3, a6;\n"
   "sub %1, a2, a5;\n"
   "sub %2, t3, t5;\n"

   "fence iorw, iorw;\n"
    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    :
    :
  );
  printf("[Exp time from asm: l1dc miss: %d, cycles: %d. mispredicts: %d] \n", dcache_misses0, cycles0, mispredicts);
}

void victim_function_noload() {
  uint64_t dcache_misses0 = 0;
  uint64_t mispredicts = 0;
  uint64_t cycles0 = 0;

 asm volatile(
   "la t0, _experiment_memory;\n"

   "fence iorw, iorw;\n"
   "csrr t5, 0xb0e;\n"
   "csrr a6, 0xb04;\n"
   "csrr a5, 0xb00;\n"
   "fence iorw, iorw;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "ld t4, 48(t0);\n"
   "ld t1, 80(t0);\n"

   "blt t4, t1, label_noload;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "label_noload:\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "fence iorw, iorw;\n"
   "csrr t3, 0xb0e;\n"
   "csrr a3, 0xb04;\n"
   "csrr a2, 0xb00;\n"
   "fence iorw, iorw;\n"

   "sub %0, a3, a6;\n"
   "sub %1, a2, a5;\n"
   "sub %2, t3, t5;\n"

   "fence iorw, iorw;\n"
    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    :
    :
  );
  printf("[Exp time from asm: l1dc miss: %d, cycles: %d. mispredicts: %d] \n", dcache_misses0, cycles0, mispredicts);
}

void victim_function_add() {
  uint64_t dcache_misses0 = 0;
  uint64_t mispredicts = 0;
  uint64_t cycles0 = 0;

 asm volatile(
   "la t0, _experiment_memory;\n"

   "addi a4, x0, 1;\n"
   "fence iorw, iorw;\n"
   "csrr t5, 0xb0e;\n"
   "csrr a6, 0xb04;\n"
   "csrr a5, 0xb00;\n"
   "fence iorw, iorw;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"

   "ld t4, 48(t0);\n"
   "ld t1, 80(t0);\n"

   "blt t4, t1, label_add;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"

   "label_add:\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"
   "add a4, a4, a4;\n"

   "fence iorw, iorw;\n"
   "csrr t3, 0xb0e;\n"
   "csrr a3, 0xb04;\n"
   "csrr a2, 0xb00;\n"
   "fence iorw, iorw;\n"

   "sub %0, a3, a6;\n"
   "sub %1, a2, a5;\n"
   "sub %2, t3, t5;\n"

   "fence iorw, iorw;\n"
    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    :
    :
  );
  printf("[Exp time from asm: l1dc miss: %d, cycles: %d. mispredicts: %d] \n", dcache_misses0, cycles0, mispredicts);
}

void victim_function() {
  uint64_t dcache_misses0 = 0;
  uint64_t mispredicts = 0;
  uint64_t cycles0 = 0;

 asm volatile(
   "la t0, _experiment_memory;\n"

   "fence iorw, iorw;\n"
   "csrr t5, 0xb0e;\n"
   "csrr a6, 0xb04;\n"
   "csrr a5, 0xb00;\n"
   "fence iorw, iorw;\n"

   "ld t4, 48(t0);\n"
   "ld t1, 80(t0);\n"

   "blt t4, t1, label;\n"
   "lb t6, 0(t0);\n"

   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "label:\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "fence iorw, iorw;\n"
   "csrr t3, 0xb0e;\n"
   "csrr a3, 0xb04;\n"
   "csrr a2, 0xb00;\n"
   "fence iorw, iorw;\n"

   "sub %0, a3, a6;\n"
   "sub %1, a2, a5;\n"
   "sub %2, t3, t5;\n"

   "fence iorw, iorw;\n"
    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    :
    :
  );
  printf("[Exp time from asm: l1dc miss: %d, cycles: %d. mispredicts: %d] \n", dcache_misses0, cycles0, mispredicts);
}

void inputfunction_moreloads(int x) {
 asm(
   "la t0, _experiment_memory;\n"
   "li t1, 16;\n"
   "sd t1, 48(t0);\n"
   "add t1, t1, t0;\n"
   "sd %0, 32(t1);\n"
    :
    : "r"(x)
    :
  );
}

void victim_function_moreloads() {
  uint64_t dcache_misses0 = 0;
  uint64_t mispredicts = 0;
  uint64_t cycles0 = 0;

 asm(
   "la t0, _experiment_memory;\n"

   "fence iorw, iorw;\n"
   "csrr t5, 0xb0e;\n"
   "csrr a6, 0xb04;\n"
   "csrr a5, 0xb00;\n"
   "fence iorw, iorw;\n"

   "ld t4, 48(t0);\n"
   "ld t1, 80(t0);\n"



   "blt t4, t1, labelml;\n"
   "lb t6, 0(t0);\n"

   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "labelml:\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"
   "nop;\n"

   "fence iorw, iorw;\n"
   "csrr t3, 0xb0e;\n"
   "csrr a3, 0xb04;\n"
   "csrr a2, 0xb00;\n"
   "fence iorw, iorw;\n"

   "sub %0, a3, a6;\n"
   "sub %1, a2, a5;\n"
   "sub %2, t3, t5;\n"

   "fence iorw, iorw;\n"
    : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
    :
    :
  );
  printf("[Exp time from asm: l1dc miss: %d, cycles: %d. mispredicts: %d] \n", dcache_misses0, cycles0, mispredicts);
}

void cache_exp_spec_load_adds(){

  printf("experiment: cache_exp_spec_load_adds\n");

  flush_cache();

  for(int i = 0; i < 15; i++){
    inputfunction(1);
   victim_function_add();
  }

  inputfunction(17); // same for input value 1 above for the training

  flush_cache_not_bp();


  cache_state cache_state;
  cache_func_prime();

  victim_function_add();

  cache_func_probe(&cache_state);
  print_cache_state(&cache_state);

   printf("end experiment: cache_exp_spec_load_adds\n");
}

void cache_exp_spec_load_more_loads(){

  printf("experiment: cache_exp_spec_load_more_loads\n");

  flush_cache();

  for(int i = 0; i < 15; i++){
    inputfunction(1);
   victim_function();
  }

  inputfunction(17); // same for input value 1 above for the training

  flush_cache_not_bp();


  cache_state cache_state;
  cache_func_prime();

  victim_function();

  cache_func_probe(&cache_state);
  print_cache_state(&cache_state);

   printf("end experiment: cache_exp_spec_load_more_loads\n");
}

void cache_exp_spec_load(){

  printf("experiment: cache_exp_spec_load\n");

  flush_cache();

  for(int i = 0; i < 15; i++){
    inputfunction(1);
   victim_function();
  }

  inputfunction(17); // same for input value 1 above for the training

  flush_cache_not_bp();


  cache_state cache_state;
  cache_func_prime();

  victim_function();

  cache_func_probe(&cache_state);
  print_cache_state(&cache_state);

   printf("end experiment: cache_exp_spec_load\n");
}

void cache_exp_spec_load_but_no_mispredict(){

  printf("experiment: cache_exp_spec_load_but_no_mispredict\n");

  flush_cache();



  for(int i = 0; i < 15; i++){
    inputfunction(1);
   victim_function();
  }

  inputfunction(1);

  flush_cache_not_bp();

  cache_state cache_state;
  cache_func_prime();

  victim_function();

  cache_func_probe(&cache_state);
  print_cache_state(&cache_state);

  printf("end experiment: cache_exp_spec_load_but_no_mispredict\n");
}

void cache_exp_spec_load_but_no_mispredict_noload_nop(){



    printf("experiment: cache_exp_spec_load_but_no_mispredict_noload_nop\n");

    flush_cache();



    for(int i = 0; i < 15; i++){
      inputfunction(17);
     victim_function_noload();
    }

    inputfunction(17);

    flush_cache_not_bp();

    cache_state cache_state;
    cache_func_prime();

    victim_function_noload();

    cache_func_probe(&cache_state);
    print_cache_state(&cache_state);


    printf("end experiment: cache_exp_spec_load_but_no_mispredict_noload_nop\n");
}

void cache_exp_spec_load_noload_nop(){

    printf("experiment: cache_exp_spec_load_noload_nop_trainTAKE\n");

    flush_cache();

    for(int i = 0; i < 15; i++){
      inputfunction(1);
     victim_function_noload();
    }

    inputfunction(17);

    flush_cache_not_bp();

    cache_state cache_state;
    cache_func_prime();

    victim_function_noload();

    cache_func_probe(&cache_state);
    print_cache_state(&cache_state);


    printf("end experiment: cache_exp_spec_load_noload_nop\n");
}

void cache_exp_spec_load_but_no_mispredict_noload_nop_uncond(){

    uint64_t first_input = 1;
    uint64_t second_input = 17;


    printf("experiment: cache_exp_spec_load_but_no_mispredict_noload_nop_uncond\n first_input: %d, second_input %d.\n", first_input, second_input);

    flush_cache();



    for(int i = 0; i < 15; i++){
      inputfunction(first_input);
     victim_function_noload_uncond();
    }

    inputfunction(second_input);

    flush_cache_not_bp();

    cache_state cache_state;
    cache_func_prime();

    victim_function_noload_uncond();

    cache_func_probe(&cache_state);
    print_cache_state(&cache_state);


    printf("end experiment: cache_exp_spec_load_but_no_mispredict_noload_nop_uncond\n");
}

void cache_exp_spec_load_noload_nop_uncond(){

  uint64_t first_input = 17;
  uint64_t second_input = 17;

    printf("experiment: cache_exp_spec_load_noload_nop_train_uncond\n first_input: %d, second_input %d.\n", first_input, second_input);

    flush_cache();

    for(int i = 0; i < 15; i++){
      inputfunction(first_input);
     victim_function_noload_uncond();
    }

    inputfunction(second_input);

    flush_cache_not_bp();

    cache_state cache_state;
    cache_func_prime();

    victim_function_noload_uncond();

    cache_func_probe(&cache_state);
    print_cache_state(&cache_state);


    printf("end experiment: cache_exp_spec_load_noload_nop_uncond\n");
}

void cache_exp_spec_load_but_no_mispredict_uncond(){

    uint64_t first_input = 1;
    uint64_t second_input = 17;


    printf("experiment: cache_exp_spec_load_but_no_mispredict_uncond\n first_input: %d, second_input %d.\n", first_input, second_input);

    flush_cache();



    for(int i = 0; i < 15; i++){
      inputfunction(first_input);
     victim_function_uncond();
    }

    inputfunction(second_input);

    flush_cache_not_bp();

    cache_state cache_state;
    cache_func_prime();

    victim_function_uncond();

    cache_func_probe(&cache_state);
    print_cache_state(&cache_state);


    printf("end experiment: cache_exp_spec_load_but_no_mispredict_uncond\n");
}

void cache_exp_spec_load_uncond(){

  uint64_t first_input = 17;
  uint64_t second_input = 17;

    printf("experiment: cache_exp_spec_load_train_uncond\n first_input: %d, second_input %d.\n", first_input, second_input);

    flush_cache();

    for(int i = 0; i < 15; i++){
      inputfunction(first_input);
     victim_function_uncond();
    }

    inputfunction(second_input);

    flush_cache_not_bp();

    cache_state cache_state;
    cache_func_prime();

    victim_function_uncond();

    cache_func_probe(&cache_state);
    print_cache_state(&cache_state);


    printf("end experiment: cache_exp_spec_load_uncond\n");
}

void cache_exp_spec_diff_correct_false_predict(){
  printf("start experiment: cache_exp_spec_diff_correct_false_predict\n");
  cache_exp_spec_load();
  cache_exp_spec_load_but_no_mispredict();
  cache_exp_spec_load_noload_nop();
  cache_exp_spec_load_but_no_mispredict_noload_nop();
  cache_exp_spec_load_more_loads();
  cache_exp_spec_load_noload_nop_uncond();
  cache_exp_spec_load_but_no_mispredict_noload_nop_uncond();
  cache_exp_spec_load_uncond();
  cache_exp_spec_load_but_no_mispredict_uncond();
  cache_exp_spec_load_adds();
  printf("end experiment: cache_exp_spec_diff_correct_false_predict\n");
}

uint64_t cache_helper_train_helper(int value){
//   experiment: cache_exp_predict_trainer
// if "<" operator
// == Second experiment Done  ==
// experiment: cache_exp_predict_trainer
//
// experiment: train + no flush
// [Exp time: l1dc miss: 0, cycles: 822, mispredicts: 1.]
//
// experiment: train + flush
// [Exp time: l1dc miss: 0, cycles: 830, mispredicts: 1.]
//
// experiment: train + flush_without bp
// [Exp time: l1dc miss: 0, cycles: 827, mispredicts: 1.]
//
// experiment: train + other value
// [Exp time: l1dc miss: 0, cycles: 789, mispredicts: 2.]


// if ">"
// == Second experiment Done  ==
// experiment: cache_exp_predict_trainer
//
// experiment: train + no flush
// [Exp time: l1dc miss: 0, cycles: 762, mispredicts: 1.]
//
// experiment: train + flush
// [Exp time: l1dc miss: 0, cycles: 779, mispredicts: 2.]
//
// experiment: train + flush_without bp
// [Exp time: l1dc miss: 0, cycles: 752, mispredicts: 1.]
//
// experiment: train + other value
// [Exp time: l1dc miss: 0, cycles: 904, mispredicts: 2.]

  //uint64_t tmp = 0;
  //printf("%x\n", (x+value));
  if(value > 256){
    value = value + 15;
  }
  //printf("%d\n", tmp);
  return value;
}

void cache_exp_predict_trainer(){

  printf("experiment: cache_exp_predict_trainer\n");
  printf("\nexperiment: train + no flush\n");
  flush_cache();

  uint64_t dcache_misses0 = 0;
  uint64_t cycles0 = 0;
  uint64_t mispredicts = 0;
  uint64_t dcache_misses1 = 0;
  uint64_t cycles1 = 0;
  uint64_t mispredict1 = 0;

  uint64_t abc = 100;
   abc=123;
   for(int i = 0; i < 10; i++){
    cache_helper_train_helper(abc);
    }
  //abc=260;

  //flush_cache_not_bp();
    asm volatile(
      "csrr %2, 0xb0e;\n"
      "csrr %0, 0xb04;\n"
      "csrr %1, 0xb00;\n"
       : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
       :
       :
     );

     cache_helper_train_helper(abc);

    asm volatile(
      "csrr %2, 0xb0e;\n"
      "csrr %0, 0xb04;\n"
      "csrr %1, 0xb00;\n"
       : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
       :
       :
     );

   printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);

   printf("\nexperiment: train + flush\n");

   flush_cache();

   dcache_misses0 = 0;
   cycles0 = 0;
   mispredicts = 0;
   dcache_misses1 = 0;
   cycles1 = 0;
   mispredict1 = 0;

   abc = 100;
    abc=123;
    for(int i = 0; i < 10; i++){
     cache_helper_train_helper(abc);
     }
   //abc=260;

   flush_cache();

     asm volatile(
       "csrr %2, 0xb0e;\n"
       "csrr %0, 0xb04;\n"
       "csrr %1, 0xb00;\n"
        : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
        :
        :
      );

      cache_helper_train_helper(abc);

     asm volatile(
       "csrr %2, 0xb0e;\n"
       "csrr %0, 0xb04;\n"
       "csrr %1, 0xb00;\n"
        : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
        :
        :
      );

    printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);

    printf("\nexperiment: train + flush_without bp\n");

    flush_cache();

    dcache_misses0 = 0;
    cycles0 = 0;
    mispredicts = 0;
    dcache_misses1 = 0;
    cycles1 = 0;
    mispredict1 = 0;

    abc = 100;
     abc=123;
     for(int i = 0; i < 10; i++){
      cache_helper_train_helper(abc);
      }
    //abc=260;

    //flush_cache_not_bp(); did not work?
      asm volatile(
        ".word 0xfff7f00b;\n"
        "csrr %2, 0xb0e;\n"
        "csrr %0, 0xb04;\n"
        "csrr %1, 0xb00;\n"
         : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
         :
         :
       );

       cache_helper_train_helper(abc);

      asm volatile(
        "csrr %2, 0xb0e;\n"
        "csrr %0, 0xb04;\n"
        "csrr %1, 0xb00;\n"
         : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
         :
         :
       );

     printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);

     printf("\nexperiment: train + other value\n");

     flush_cache();

     dcache_misses0 = 0;
     cycles0 = 0;
     mispredicts = 0;
     dcache_misses1 = 0;
     cycles1 = 0;
     mispredict1 = 0;

     abc = 100;
      abc=123;
      for(int i = 0; i < 10; i++){
       cache_helper_train_helper(abc);
       }
     abc=260;

     //flush_cache_not_bp();
       asm volatile(
         "csrr %2, 0xb0e;\n"
         "csrr %0, 0xb04;\n"
         "csrr %1, 0xb00;\n"
          : "=r"(dcache_misses0), "=r"(cycles0), "=r"(mispredicts)
          :
          :
        );

        cache_helper_train_helper(abc);

       asm volatile(
         "csrr %2, 0xb0e;\n"
         "csrr %0, 0xb04;\n"
         "csrr %1, 0xb00;\n"
          : "=r"(dcache_misses1), "=r"(cycles1), "=r"(mispredict1)
          :
          :
        );

      printf("[Exp time: l1dc miss: %d, cycles: %d, mispredicts: %d.] \n", dcache_misses1 - dcache_misses0, cycles1 - cycles0, mispredict1 - mispredicts);

}

void cache_exp_all(){

  // printf("== First experiment Start == \n");
  // cache_exp_flushinbetween(); // cache_exp_flushinbetween
  // printf("== First experiment Done  == \n");
  //
  // printf("== Second experiment Start == \n");
  // cache_exp_mispredict_counters();
  // cache_exp_mispredict_counters_speculative_load();
  // cache_exp_mispredict_counters_speculative_noload();
  //cache_exp_spec_diff_correct_false_predict();
  //cache_exp_predict_trainer();();
  // printf("== Second experiment Done  == \n");
  //
  //
  // printf("== Third experiment Start == \n");
  // cache_exp_mispredict_counters();
  // cache_exp_mispredict_counters_0();
  // cache_exp_mispredict_counters_if_1();
  // cache_exp_mispredict_counters_if_2();
  // cache_exp_mispredict_counters_load();
  // cache_exp_mispredict_counters_loop();
  // cache_exp_mispredict_counters_train();
  // printf("== Third experiment Done  == \n");
  //
  // // printf("== Forth experiment Start == \n");
  // // //cache_exp_straight_spec(); // Not done. Not sure how to correctly do it. Will try constant jump.
  // // printf("== Forth experiment Done  == \n");
  // //
  // printf("== Fifth experiment Start == \n");
  // test_value_in_cache(); // Basically shows that two accesses to the same memory address within the cacheable area will cause a miss and then a hit.
  // test_value_in_cache2();
  // test_value_in_cache3();
  // printf("== Fifth experiment Done  == \n");
  //
  // printf("== Sixth experiment Start == \n");
  // cache_exp_miss_and_hit_from_base(); // Shows that the 8 accesses to the same set are in the cache.
  // printf("== Sixth experiment Done  == \n");
  //
  // printf("== Seventh experiment Start == \n");
  // cache_exp_miss_and_hit_from_cacheable(); // Shows that the 9 accesses to the same set are NOT all in the cache.
  // printf("== Seventh experiment Done  == \n");
  //
  //
  // printf("== Eight experiment Start == \n");
  // cache_exp_timings_instructions(); // Timings
  // printf("== Eight experiment Done  == \n");
  //
  // printf("== Ninth experiment Start == \n");
  // test_two_ways(); // Shows that sets are being filled in 2ways
  // printf("== Ninth experiment Done == \n");
  //
  // printf("== Tenth experiment Start == \n");
  // test_eight_ways(); // Shows that sets are being filled in all there ways.
  // printf("== Tenth experiment Done == \n");
  //
  // printf("== Eleventh experiment Start == \n");
  // test_nine_ways(); // Shows that sets are being filled in all there ways.
  // printf("== Eleventh experiment Done == \n");
  //
  // printf("== Twelfth experiment Start == \n");
  // cache_exp_primeandprobe_two_executions(); // prime and probe 2 times, to compare caches.
  // printf("== Twelfth experiment Done == \n");
  //
  // printf("== 13 experiment Start == \n");
  // cache_exp_primeandprobe_no_access(); // prime and probe
  // printf("== 13 experiment Done == \n");
}

// experiments and test cases END
