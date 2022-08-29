# start sequence of the bootloader
#
#
#include <smp.h>
#define DRAM_BASE 0x80000000

  .section .text.init
  .option norvc
  .globl _embexp_entry
_embexp_entry:
  smp_pause(s1, s2)
  li sp, 0x84000000
  call _main_init
  smp_resume(s1, s2)
  csrr a0, mhartid
  li s1, DRAM_BASE
  jr s1
