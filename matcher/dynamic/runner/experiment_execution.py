import logging
import subprocess
import os
import re

from typing import List

from constants import PATH_OPENSSL, PATH_BINARY, PATH_GDB_BATCHFILE, NUM_CACHE_LINES, NUM_REPETITIONS
from lookuptable import LookupTableWithAccesses
from util import proc_wait_for_output

l = logging.getLogger(__name__)

def parse_gdb_output(gdb_out: str) -> LookupTableWithAccesses:
	pos = 0
	def expect(substr: str) -> None:
		nonlocal pos
		pos = gdb_out.index(substr, pos) + len(substr)
	def extract_until_EOL() -> str:
		nonlocal pos
		return gdb_out[pos:gdb_out.index("\n", pos)]

	# identify SQR_tb base address
	expect("\n&SQR_tb[0] = ")
	SQR_tb_addr_start = int(extract_until_EOL(), 16)
	# for validation purposes, also identify the address of the last element
	expect("\n&SQR_tb[16] = ")
	# validation
	SQR_tb_addr_end = int(extract_until_EOL(), 16)
	assert(SQR_tb_addr_end == SQR_tb_addr_start + (16 * 8))
	
	# create internal data structure to represent the results. represents
	# the lookup table's data structure and the accesses to the lookup
	# table in the course of the execution.
	SQR_tb = LookupTableWithAccesses(
		base_addr=SQR_tb_addr_start,
		element_size=8,
		no_elements=16
	)

	# parse recorded accesses and store the records in SQR_tb
	expect("--- experiment start ---\n")
	regex = (r"count: (\d+)\n\nHardware read watchpoint (\d+): \*SQR_tb\[(\d+)\]\n\n"
		+ r"Value = (.*)\n\nHardware read watchpoint \2: \*SQR_tb\[\3\]\n\nValue = \4")
	for match_idx, match in enumerate(re.finditer(regex, gdb_out[pos:])):
		instruction_counter = int(match.group(1))
		SQR_tb_index = int(match.group(3))
		SQR_tb.record_access(SQR_tb_index, instruction_counter)

	return SQR_tb

def run_experiment_gdb(bignum: str) -> LookupTableWithAccesses:
	# validate bignum format
	assert(re.match(r"[0-9a-zA-Z]+", bignum))

	l.info(f"Running experiment with input {bignum} in Valgrind/GDB.")

	# To make sure that the correct OpenSSL library is used, create a new
	# set of environment variables that specifies the library path. This
	# set of variables is then passed to valgrind and gdb when they are
	# executed.
	env_with_ld = dict(os.environ, LD_LIBRARY_PATH=PATH_OPENSSL)

	# start valgrind
	proc_valgrind = subprocess.Popen(
		args=["valgrind", "--vgdb=full", "--vgdb-error=0", PATH_BINARY, bignum],
		env=env_with_ld, stdout=subprocess.PIPE, stderr=subprocess.PIPE
	)

	# wait for valgrind to get ready
	if proc_valgrind.stderr is not None:
		proc_wait_for_output(proc_valgrind.stderr, "TO DEBUG THIS PROCESS USING GDB")
		l.info("Valgrind ready. Starting GDB.")
	else:
		raise Exception("Error in Valgrind execution")

	# start gdb
	proc_gdb = subprocess.Popen(
		args=["gdb", "--batch", f"--command={PATH_GDB_BATCHFILE}", PATH_BINARY],
		env=env_with_ld, stdout=subprocess.PIPE, stderr=subprocess.PIPE
	)

	# wait for gdb to finish and capture the output
	gdb_stdout, gdb_stderr = proc_gdb.communicate()
	l.info(f"GDB finished, RC: {proc_gdb.returncode}")

	# wait for valgrind to finish
	# proc_wait_for_output(proc_valgrind.stdout, bignum)
	returncode_valgrind = proc_valgrind.wait()
	assert(returncode_valgrind == 0)

	l.info("Experiment execution done.")

	return parse_gdb_output(gdb_stdout.decode())

def run_experiment_cachetrace(bignum: str) -> List[float]:
	# validate bignum format
	assert(re.match(r"[0-9a-zA-Z]+", bignum))

	l.info(f"Running experiment with input {bignum} for cache tracing.")

	# datastructure to store results (for each cache line to probe, store a
	# cache hit ratio.)
	hits_per_cache_line: List[float] = [0.0 for _ in range(NUM_CACHE_LINES)]

	# To make sure that the correct OpenSSL library is used, create a new
	# set of environment variables that specifies the library path. This
	# set of variables is then passed to valgrind and gdb when they are
	# executed.
	env_with_ld = dict(os.environ, LD_LIBRARY_PATH=PATH_OPENSSL)

	# run victim process NUM_REPETITION times per cache line to probe.
	for cache_line_idx in range(NUM_CACHE_LINES):
		for repetition_idx in range(NUM_REPETITIONS):
			# start victim process
			proc_victim = subprocess.Popen(
				args=[PATH_BINARY, bignum, str(cache_line_idx)],
				env=env_with_ld, stdout=subprocess.PIPE, stderr=subprocess.PIPE
			)

			# wait for victim process to finish and capture the output
			victim_stdout, victim_stderr = proc_victim.communicate()
			l.debug(f"Victim (CL: {cache_line_idx}, Repetition: {repetition_idx}) finished, RC: {proc_victim.returncode}")

			# parse output (extract the Flush+Reload timing information)
			for line in victim_stdout.decode().splitlines():
				rx = re.match(r"^time: +(\d+) \((hit|miss)\)$", line)
				if rx:
					l.debug(f"F+R time: {int(rx.group(1))}, cache state: {rx.group(2)}")
					if rx.group(2) == "hit":
						hits_per_cache_line[cache_line_idx] += 1.0

	for i, hits in enumerate(hits_per_cache_line):
		hits_per_cache_line[i] = hits / NUM_REPETITIONS
	l.info(f"Hit ratio per cache line: {hits_per_cache_line}")

	return hits_per_cache_line