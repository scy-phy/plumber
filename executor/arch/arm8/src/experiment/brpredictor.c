#include <stdio.h>
#include "cache.h" 

/* ******************************************************************** */
/* Test code.                                                         */
/* ******************************************************************** */

uint8_t branch_rev()
{
  uint64_t cnt1 = 0, cnt2 = 0, c;
  int long unsigned L, liter = 10000, off = liter;
  int a = 0;

  enable_pmu(1,0xCC);
  do{
      L = (liter % 32) >> 4; // pattern 16*T, 16*nT
      /* printf("L is %d \n", L); */
//-----------------------------------
__asm__ __volatile__(".include \"all/inc/experiment/asm.h\"" : :);
//-----------------------------------	
      if (L == 1){ // execute one path per iteration
      
	if(a == 0) a = 1; // Repeat the statement 8 times
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");	
		
	if(a == 0) a = 1; // Setup1*/
	//asm volatile("nop");
     }
     else{ // dummy non-branch instructions
//-----------------------------------	
	if(a == 0) a = 1; // Repeat the statement 8 times
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");
	if(a == 0) a = 1;
	asm volatile("nop");	
		
	if(a == 0) a = 1; // Setup2*/
	//asm volatile("nop");

    }
//-----------------------------------
__asm__ __volatile__(".include \"all/inc/experiment/nop.h\"" : :);
//-----------------------------------
      asm volatile("nop");
      if(L == 0) a = 1; // Spy branch
      liter--;  
         
   } while (liter > 0);
  disable_pmu(1);
  cnt1 = read_pmu(1); 
  printf("Number of mispredicted branches is %d \n", cnt1);
  
}
 
