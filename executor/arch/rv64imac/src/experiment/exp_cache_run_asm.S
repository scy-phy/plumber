#include "config.h"

// https://github.com/riscv/riscv-asm-manual/blob/master/riscv-asm.md
// https://www.cs.cornell.edu/courses/cs3410/2019sp/riscv/interpreter/
// https://riscv.org/wp-content/uploads/2017/05/riscv-spec-v2.2.pdf

#define TRAINING_ROUNDS 15

#ifdef RUN_CACHE

#if !defined(__has_include)
#  error "need __has_include"
#endif

#if (!__has_include("experiment/asm.h")) || (!__has_include("experiment/asm_setup_1.h"))
#  error "need at least asm code to run and asm code to setup state 1"
#endif

#if __has_include("experiment/asm_setup_train.h")
#  define EXP_HAS_INPUT_TRAIN
#endif

#if __has_include("experiment/asm_setup_2.h")
#  define EXP_HAS_INPUT_2
#endif

.globl _cache_run

#ifdef EXP_HAS_INPUT_TRAIN
.globl _scamv_train
#endif
.globl _scamv_run1
#ifdef EXP_HAS_INPUT_2
.globl _scamv_run2
#endif

.section .text //.experiment_code
scamv_entry:
.include "experiment/asm.h"
	j scamv_exit


.section .data
.align 3
_sp_store:
	.quad 0
.align 3
_scamv_ret_store:
	.quad 0
.align 3
_scamv_train_loop_cnt:
	.quad 0


.section .text

#ifdef EXP_HAS_INPUT_TRAIN
_scamv_train:
	la t0, _scamv_ret_store
	sd ra, 0(t0)
	mv t0, zero
	mv ra, zero
.include "experiment/asm_setup_train.h"
	j scamv_entry
#endif // EXP_HAS_INPUT_TRAIN

_scamv_run1:
	la t0, _scamv_ret_store
	sd ra, 0(t0)
	mv t0, zero
	mv ra, zero
.include "experiment/asm_setup_1.h"
	fence iorw, iorw
	j scamv_entry

#ifdef EXP_HAS_INPUT_2
_scamv_run2:
	la t0, _scamv_ret_store
	sd ra, 0(t0)
	mv t0, zero
	mv ra, zero
.include "experiment/asm_setup_2.h"
	fence iorw, iorw
	j scamv_entry
#endif // EXP_HAS_INPUT_2

scamv_exit:
	fence iorw, iorw
	la t0, _scamv_ret_store
	ld ra, 0(t0)
	ret


_cache_run:
// save registers on stack
	addi	sp, sp, (8 * -40)
	sd	 x1, (8 *  1)(sp) // RA
	sd	 x2, (8 *  2)(sp) // SP
	sd	 x3, (8 *  3)(sp)
	sd	 x4, (8 *  4)(sp)
	sd	 x5, (8 *  5)(sp)
	sd	 x6, (8 *  6)(sp)
	sd	 x7, (8 *  7)(sp)
	sd	 x8, (8 *  8)(sp)
	sd	 x9, (8 *  9)(sp)
	sd	x10, (8 * 10)(sp) // cache
	sd	x11, (8 * 11)(sp) // _clean_mem_run
	sd	x12, (8 * 12)(sp) // _scamv_run
	sd	x13, (8 * 13)(sp) // _clean_mem_train
	sd	x14, (8 * 14)(sp) // _scamv_train
	sd	x15, (8 * 15)(sp)
	sd	x16, (8 * 16)(sp)
	sd	x17, (8 * 17)(sp)
	sd	x18, (8 * 18)(sp)
	sd	x19, (8 * 19)(sp)
	sd	x20, (8 * 20)(sp)
	sd	x21, (8 * 21)(sp)
	sd	x22, (8 * 22)(sp)
	sd	x23, (8 * 23)(sp)
	sd	x24, (8 * 24)(sp)
	sd	x25, (8 * 25)(sp)
	sd	x26, (8 * 26)(sp)
	sd	x27, (8 * 27)(sp)
	sd	x28, (8 * 28)(sp)
	sd	x29, (8 * 29)(sp)
	sd	x30, (8 * 30)(sp)
	sd	x31, (8 * 31)(sp)

// store SP register
	la	t0, _sp_store
	sd	sp, 0(t0)


#ifdef EXP_HAS_INPUT_TRAIN
// ========================================================

	la	t0, _scamv_train_loop_cnt
	mv	t1, zero
	sd	t1, 0(t0)

__enter_scamv_train_loop:
	la	t0, _scamv_train_loop_cnt
	ld	t1, 0(t0)
	li	t2, TRAINING_ROUNDS
	bge	t1, t2, __exit_scamv_train_loop
	addi	t1, t1, 1
	sd	t1, 0(t0)

// restore SP register
	la	t0, _sp_store
	ld	sp, 0(t0)
// clean experiment memory: _clean_mem_train
	// TODO: need to set input memory here as well!!!
	ld	x1, (8 * 13)(sp)
	jalr	x1
// load _scamv_train in x1 (RA)
	ld	x1, (8 * 14)(sp)
// create defined processor state
	mv	 x2, zero
	mv	 x3, zero
	mv	 x4, zero
	mv	 x5, zero
	mv	 x6, zero
	mv	 x7, zero
	mv	 x8, zero
	mv	 x9, zero
	mv	x10, zero
	mv	x11, zero
	mv	x12, zero
	mv	x13, zero
	mv	x14, zero
	mv	x15, zero
	mv	x16, zero
	mv	x17, zero
	mv	x18, zero
	mv	x19, zero
	mv	x20, zero
	mv	x21, zero
	mv	x22, zero
	mv	x23, zero
	mv	x24, zero
	mv	x25, zero
	mv	x26, zero
	mv	x27, zero
	mv	x28, zero
	mv	x29, zero
	mv	x30, zero
	mv	x31, zero
	// TODO: are there ALU flags that should be set to a defined state?
	// like ARM "adds x0, x1, x2"

// run the experiment code (with training inputs)
	jalr	x1

// go back into to the loop entry
	j __enter_scamv_train_loop

__exit_scamv_train_loop:

// ========================================================
#endif // EXP_HAS_INPUT_TRAIN


// restore SP register
	la	t0, _sp_store
	ld	sp, 0(t0)
// clean experiment memory: _clean_mem_run
	// TODO: need to set input memory here as well!!!
	ld	x1, (8 * 11)(sp)
	jalr	x1
// flush the cache now
	fence iorw, iorw
	// flush here! tried with 7 now. With full fffff, we get also result.
	.word 0xfff7f00b
// prime for measurement
	la	x1, cache_func_prime
	jalr	x1
// load _scamv_run in x1 (RA)
	ld	x1, (8 * 12)(sp)
// create defined processor state
	mv	 x2, zero
	mv	 x3, zero
	mv	 x4, zero
	mv	 x5, zero
	mv	 x6, zero
	mv	 x7, zero
	mv	 x8, zero
	mv	 x9, zero
	mv	x10, zero
	mv	x11, zero
	mv	x12, zero
	mv	x13, zero
	mv	x14, zero
	mv	x15, zero
	mv	x16, zero
	mv	x17, zero
	mv	x18, zero
	mv	x19, zero
	mv	x20, zero
	mv	x21, zero
	mv	x22, zero
	mv	x23, zero
	mv	x24, zero
	mv	x25, zero
	mv	x26, zero
	mv	x27, zero
	mv	x28, zero
	mv	x29, zero
	mv	x30, zero
	mv	x31, zero
	// TODO: are there ALU flags that should be set to a defined state?
	// like ARM "adds x0, x1, x2"

// run the experiment code
	jalr	x1
// restore SP register
	la	t0, _sp_store
	ld	sp, 0(t0)
// probe for measurement, and save the cache state for this run
	la	x1, cache_func_probe
	ld	a0, (8 * 10)(sp)
	jalr	x1

/*
// debug the first cache set
	//debug_set(cache1[0]);
	ldr x0,  [sp, #(8 *  0)]
	mov x1, #0
	bl debug_set
*/

// restore registers from stack
	ld	 x1, (8 *  1)(sp)
	ld	 x2, (8 *  2)(sp)
	ld	 x3, (8 *  3)(sp)
	ld	 x4, (8 *  4)(sp)
	ld	 x5, (8 *  5)(sp)
	ld	 x6, (8 *  6)(sp)
	ld	 x7, (8 *  7)(sp)
	ld	 x8, (8 *  8)(sp)
	ld	 x9, (8 *  9)(sp)
	ld	x10, (8 * 10)(sp)
	ld	x11, (8 * 11)(sp)
	ld	x12, (8 * 12)(sp)
	ld	x13, (8 * 13)(sp)
	ld	x14, (8 * 14)(sp)
	ld	x15, (8 * 15)(sp)
	ld	x16, (8 * 16)(sp)
	ld	x17, (8 * 17)(sp)
	ld	x18, (8 * 18)(sp)
	ld	x19, (8 * 19)(sp)
	ld	x20, (8 * 20)(sp)
	ld	x21, (8 * 21)(sp)
	ld	x22, (8 * 22)(sp)
	ld	x23, (8 * 23)(sp)
	ld	x24, (8 * 24)(sp)
	ld	x25, (8 * 25)(sp)
	ld	x26, (8 * 26)(sp)
	ld	x27, (8 * 27)(sp)
	ld	x28, (8 * 28)(sp)
	ld	x29, (8 * 29)(sp)
	ld	x30, (8 * 30)(sp)
	ld	x31, (8 * 31)(sp)
	addi	sp, sp, (8 * 40)

// return to the caller
	ret


#endif // RUN_CACHE
