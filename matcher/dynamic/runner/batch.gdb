# connect to valgrind's gdb interface
target remote | vgdb

# set a breakpoint at the entry point and let the program continue until there.
# this ensures that openssl's libcrypto (and its symbols) are loaded
b *main
c

# now continue until the relevant function call
b *BN_GF2m_mod_sqr_arr
c

# print base address and end address of the lookup table (LUT)
printf "&SQR_tb[0] = %p\n", &SQR_tb[0]
printf "&SQR_tb[16] = %p\n", &SQR_tb[16]

# set up read watchpoints for all elements of the LUT
rwatch *SQR_tb[0]
rwatch *SQR_tb[1]
rwatch *SQR_tb[2]
rwatch *SQR_tb[3]
rwatch *SQR_tb[4]
rwatch *SQR_tb[5]
rwatch *SQR_tb[6]
rwatch *SQR_tb[7]
rwatch *SQR_tb[8]
rwatch *SQR_tb[9]
rwatch *SQR_tb[10]
rwatch *SQR_tb[11]
rwatch *SQR_tb[12]
rwatch *SQR_tb[13]
rwatch *SQR_tb[14]
rwatch *SQR_tb[15]
printf "--- experiment start ---\n"

# dummy count output to make parsing easier
printf "count: %d\n", 0
# continue until the first watchpoint triggers
c

# starting from the first watchpoint, use stepi to go to the next instruction
# and count the number of instructions that are executed. the counter allows to
# compute the effective distance between two relevant load instructions later.
set $count = 0
while($count < 250)
	set $count = $count + 1
	printf "count: %d\n", $count
	stepi
end

#printf "Stopped at instruction %p", $pc-4

# kill process
k