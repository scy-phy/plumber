#!/usr/bin/env python3

from __future__ import annotations
from typing import Iterator, TYPE_CHECKING
if TYPE_CHECKING:
	from lookuptable import LookupTableWithAccesses

import logging
import random
import jsonpickle
import glob
import argparse
import re
import os

from constants import PATH_RESULTS
from experiment_execution import run_experiment_gdb, run_experiment_cachetrace, parse_gdb_output
from relations import relations_classify
from util import hit_ratios_to_classification

l = logging.getLogger(__name__)

def generate_random_experiment_inputs(n: int) -> Iterator[str]:
	for _ in range(n):
		value = random.randint(0x0000000000000000, 0xffffffffffffffff)
		yield f"{value:016x}"

# main function for 'run' mode
def run_experiments():
	os.makedirs(PATH_RESULTS, exist_ok=True)

	# special_experiment_inputs = [
	# 	"0123456789abcdef",
	# 	"02468ace00000000",
	# 	"048c000000000000",
	# 	"08f0000000000000",
	# 	"0800000f00000000",
	# 	"0000000000000000",
	# 	"0000000000000001",
	# 	"ffffffffffffffff",
	# ]
	
	# run experiments and store the results in text files
	# for idx, experiment_input in enumerate(special_experiment_inputs):
	for idx, experiment_input in enumerate(generate_random_experiment_inputs(100)):
		l.info(f"Starting experiment {idx+1}.")
		SQR_tb: LookupTableWithAccesses = run_experiment_gdb(experiment_input)
		hit_ratio_per_cache_line: List[float] = run_experiment_cachetrace(experiment_input)
		with open(os.path.join(PATH_RESULTS, f"experiment_{experiment_input}.result.txt"), "w") as result_file:
			result_file.write(jsonpickle.encode(SQR_tb))
			result_file.write("\n")
			result_file.write(jsonpickle.encode(hit_ratio_per_cache_line))

def _find_relevant_accesses(lut: LookupTableWithAccesses) -> Tuple[Access, Access, Access]:
	assert(len(lut.accesses) >= 3)
	used_sets: Set[int] = set()
	accesses: List[Access] = [lut.accesses[i] for i in range(3)]
	confirmed = 0
	for i, access in enumerate(lut.accesses):
		acc_set = lut.idx_to_set(access.idx)
		if acc_set not in used_sets:
			used_sets.add(acc_set)
			accesses[confirmed] = access
			confirmed += 1
		if confirmed == 3:
			break
	return tuple(accesses)

# main function for 'evaluate' mode
def evaluate_experiments():
	result_file_paths = glob.glob(os.path.join(PATH_RESULTS, "*.result.txt"))
	statistics = dict()
	for result_file_path in result_file_paths:
		# extract input from filename
		experiment_input = re.match(r".*experiment_([0-9a-f]+)\.result\.txt$", result_file_path).group(1)
		
		# read lookuptable information and recorded accesses from file
		with open(result_file_path) as result_file:
			lines = result_file.read().splitlines()
			SQR_tb: LookupTableWithAccesses = jsonpickle.decode(lines[0])
			hit_ratio_per_cache_line: List[float] = jsonpickle.decode(lines[1])
		
		print(f"Input: {experiment_input}")

		# make sure at least 3 accesses happened for the given input
		if len(SQR_tb.accesses) < 3:
			print("Insufficient number of accesses\n-----")
			continue

		# check relations between the first three loads and print results
		accesses = _find_relevant_accesses(SQR_tb)
		# accesses = (
		# 	SQR_tb.accesses[0],
		# 	SQR_tb.accesses[1],
		# 	SQR_tb.accesses[2]
		# )
		sets = (
			SQR_tb.idx_to_set(accesses[0].idx),
			SQR_tb.idx_to_set(accesses[1].idx),
			SQR_tb.idx_to_set(accesses[2].idx)
		)
		n1 = accesses[1].instruction_counter - accesses[0].instruction_counter
		n2 = accesses[2].instruction_counter - accesses[1].instruction_counter
		relations_classification = relations_classify(SQR_tb, accesses)
		hit_ratios_classification = hit_ratios_to_classification(hit_ratio_per_cache_line)
		print(f" sets: {sets}")
		print(f" n1: {n1}, n2: {n2}")
		print(f" Classification:   {relations_classification}")
		print(f" Real world:      {hit_ratios_classification} (hit ratios per CL: {hit_ratio_per_cache_line})")

		statistics_key = f"{relations_classification}-{hit_ratios_classification}"
		if not statistics_key in statistics:
			statistics[statistics_key] = 1
		else:
			statistics[statistics_key] += 1
		print("-----")
	
	print(statistics)

if __name__ == "__main__":
	# set up logging
	logging.basicConfig(
		format="%(asctime)s %(name)s %(levelname)s: %(message)s",
		level=logging.INFO
	)

	# parse command line arguments
	argparser = argparse.ArgumentParser(description="Experiment Runner.")
	argparser_subs = argparser.add_subparsers(dest="command")
	argparser_sub_run = argparser_subs.add_parser("run")
	argparser_sub_evaluate = argparser_subs.add_parser("evaluate")
	args = argparser.parse_args()
	
	# start main action, depending on command line
	l.info(f"Starting in '{args.command}' mode.")
	if args.command == "run":
		run_experiments()
	elif args.command == "evaluate":
		evaluate_experiments()
