from __future__ import annotations

import argparse
import os

from typing import Dict, List, Tuple, Iterator, Optional, Any, TYPE_CHECKING
if TYPE_CHECKING:
	from classification.measurement import Measurement

from classification.measurement import MeasurementCache, MeasurementInt
from classification.classification_methods import CLASSIFICATION_METHODS

from analysis.analysis_functions import analyze_fuzzed_bits

from utils.config import Config

if __name__ == "__main__":
	# parse command line arguments
	argparser = argparse.ArgumentParser(
		description="Classifies and analyzes the results of GTS execution based on user-defined criteria."
	)
	argparser.add_argument(
		"-o", "--outdir", required=True,
		help="Output directory of the executor to load the logs from"
	)
	argparser.add_argument(
		"-c", "--config", type=str, default="classifier.ini",
		help="Configuration file for the classifier. Default: classifier.ini"
	)
	args = argparser.parse_args()

	config: Config = Config(args.config)
	
	# ============ CLASSIFIER ===========

	# classify experiments
	# Possible improvement: find out measurement_method dynamically
	measurement_method: str = config.get_str_or_error("general", "measurement_method")
	classification_method: str = config.get_str_or_error("general", "classification_method")

	# data structure to store the resulting classification
	classification: Dict[int, List[Measurement]] = dict()

	for experiment_dir in sorted(os.listdir(args.outdir)):
		experiment_dir = os.path.join(args.outdir, experiment_dir)
		if not os.path.isdir(experiment_dir):
			continue
		print(f"classifying experiment {experiment_dir}...")

		# parse measurement log into data structure
		if measurement_method == "cache":
			measurement: Measurement = MeasurementCache(experiment_dir)
		elif measurement_method == "time":
			measurement = MeasurementInt(experiment_dir, "time")
		elif measurement_method == "branch_predictor":
			measurement = MeasurementInt(experiment_dir, "mispredictions")
		else:
			raise Exception(f"Unknown measurement method {measurement_method}.")

		# classify measurement according to the selected classification method
		if classification_method not in CLASSIFICATION_METHODS:
			raise Exception(f"Unknown classification method {classification_method}.")

		class_id: int = CLASSIFICATION_METHODS[classification_method](measurement, config)
		classification.setdefault(class_id, []).append(measurement)
		print(f"classified {experiment_dir} into class {class_id}.")

	# ============ ANALYZER ===========
	
	# find out fuzzed bits
	# Possible improvement: Store this with the GTS and read it from there,
	# or at least read it from the config.
	# fuzzed_bits_idx: Tuple[int, int] = (0,  6) # offset fuzzing
	fuzzed_bits_idx: Tuple[int, int] = (6, 13) # cache line fuzzing
	
	# Analysis: find constraints and relations
	analyze_fuzzed_bits(classification, fuzzed_bits_idx)
