#pragma once

#include <assert.h>
#include <inttypes.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sched.h>

#ifndef PAGE_SIZE
	#define PAGE_SIZE (4096)
#endif
#ifndef CACHE_LINE_WIDTH
	#define CACHE_LINE_WIDTH (64)
#endif

typedef struct {
	uint8_t* base_addr;
	size_t size;
} Mapping;

typedef struct Result {
	size_t index;
	uint64_t time;
} Result;

// Initialize timing cycle count register on the current CPU core
void timing_init() {
	uint32_t value = 0;

	/* Enable Performance Counter */
	asm volatile("MRS %0, PMCR_EL0" : "=r" (value));
	value |= (1 << 0); /* Enable */
	value |= (1 << 1); /* Cycle counter reset */
	value |= (1 << 2); /* Reset all counters */
	asm volatile("MSR PMCR_EL0, %0" : : "r" (value));

	/* Enable cycle counter register */
	asm volatile("MRS %0, PMCNTENSET_EL0" : "=r" (value));
	value |= (1 << 31);
	asm volatile("MSR PMCNTENSET_EL0, %0" : : "r" (value));
}

// The following inline functions are based on
// https://github.com/IAIK/ZombieLoad/blob/master/attacker/variant1_linux/cacheutils.h
//   and
// https://github.com/IAIK/armageddon/blob/master/libflush/libflush/armv8/
static inline __attribute__((always_inline)) void maccess(void *p) {
	volatile uint32_t value;
	asm volatile ("LDR %w0, [%1]\n\t"
		: "=r" (value)
		: "r" (p)
	);
}
static inline __attribute__((always_inline)) void flush(void* ptr) {
	asm volatile ("DC CIVAC, %0" :: "r"(ptr));
	asm volatile ("DSB ISH");
	asm volatile ("ISB");
}
static inline __attribute__((always_inline)) void mfence() {
	asm volatile ("DSB SY");
	asm volatile ("ISB");
}
static inline __attribute__((always_inline)) uint64_t rdtsc() {
	uint64_t result = 0;
	asm volatile("MRS %0, PMCCNTR_EL0" : "=r" (result));
	return result;
}

static inline __attribute__((always_inline)) int reload_t(void *ptr) {
	uint64_t start = 0, end = 0;

	mfence();
	start = rdtsc();
	mfence();
	maccess(ptr);
	mfence();
	end = rdtsc();
	mfence();

	return (int)(end - start);
}

static inline __attribute__((always_inline)) int reload_flush_t(void *ptr) {
	uint64_t start = 0, end = 0;

	mfence();
	start = rdtsc();
	mfence();
	maccess(ptr);
	mfence();
	end = rdtsc();
	mfence();
	flush(ptr);
	mfence();

	return (int)(end - start);
}

static inline __attribute__((always_inline)) int flush_t(void *ptr) {
	uint64_t start = 0, end = 0;

	mfence();
	start = rdtsc();
	mfence();
	flush(ptr);
	mfence();
	end = rdtsc();
	mfence();

	return (int)(end - start);
}

// Helper function that returns a cpu_set_t with a cpu affinity mask
// that limits execution to the single (logical) CPU core cpu.
cpu_set_t build_cpuset(int cpu) {
	cpu_set_t cpuset;
	CPU_ZERO(&cpuset);
	CPU_SET(cpu, &cpuset);
	return cpuset;
}

// Set affinity mask of the given process so that the process is executed
// on a specific (logical) core.
int move_process_to_cpu(pid_t pid, int cpu) {
	cpu_set_t cpuset = build_cpuset(cpu);
	return sched_setaffinity(pid, sizeof(cpu_set_t), &cpuset);
}

int get_current_cpu_core() {
	unsigned int cpu;
	int ret = getcpu(&cpu, NULL);
	if (ret != 0) {
		return -1;
	}
	return cpu;
}
