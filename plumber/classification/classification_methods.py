from __future__ import annotations

from typing import Dict, List, Callable, Final, TYPE_CHECKING
if TYPE_CHECKING:
	from .measurement import Measurement

from .measurement import MeasurementCache, MeasurementInt

from gts.codegen import CodeGeneratorARMA64
from utils.config import Config

def classificationmethod_cache_count(measurement: Measurement, config: Config) -> int:
	assert isinstance(measurement, MeasurementCache)

	# read additional parameters from config
	cache_level: int = config.get_int_or_error("method_cache_count", "cache_level")

	if cache_level in measurement.cache_contents:
		return len(measurement.cache_contents[cache_level])
	else:
		return 0

def classificationmethod_cache_exact_address(measurement: Measurement, config: Config) -> int:
	assert isinstance(measurement, MeasurementCache)
	
	# read the CPU architecture from config to determine tag/set offsets
	cpu_architecture: str = config.get_str_or_error("general", "cpu_architecture")
	if cpu_architecture == "ARMA64":
		mask_set: int = CodeGeneratorARMA64.mask_set()
		mask_tag: int = CodeGeneratorARMA64.mask_tag()
		shift_set: int = CodeGeneratorARMA64.shift_set()
		shift_tag: int = CodeGeneratorARMA64.shift_tag()
	else:
		raise Exception("Unknown CPU architecture")
	
	# read additional parameters from config
	cache_level: int = config.get_int_or_error("method_cache_exact_address", "cache_level")
	expected_address_index: int = config.get_int_or_error("method_cache_exact_address", "expected_address_index")

	# get dict of registers; sort addresses stored in registers by the register name
	register_contents: Dict[str, int] = measurement.register_contents()
	register_contents_sorted: List[int] = [
		address for reg_name, address in sorted(
			register_contents.items(), key=lambda x: int(x[0][1:])
		)
	]
	
	# try to find the selected address in the cache dump
	if expected_address_index < len(register_contents_sorted):
		expected_address: int = register_contents_sorted[expected_address_index]

		expected_set_no: int = (expected_address & mask_set) >> shift_set
		expected_tag_no: int = (expected_address & mask_tag) >> shift_tag
		
		if cache_level in measurement.cache_contents:
			for set_no, tag_no in measurement.cache_contents[cache_level]:
				if set_no == expected_set_no and tag_no == expected_tag_no:
					return 1
	return 0

def classificationmethod_int_threshold(measurement: Measurement, config: Config) -> int:
	assert isinstance(measurement, MeasurementInt)
	
	# read additional parameters from config
	threshold: int = config.get_int_or_error("method_int_threshold", "threshold")
	relation: str = config.get_str_or_error("method_int_threshold", "relation")

	if relation == "lt":
		return 1 if measurement.value <  threshold else 0
	elif relation == "le":
		return 1 if measurement.value <= threshold else 0
	elif relation == "eq":
		return 1 if measurement.value == threshold else 0
	elif relation == "ge":
		return 1 if measurement.value >= threshold else 0
	elif relation == "gt":
		return 1 if measurement.value >  threshold else 0
	elif relation == "ne":
		return 1 if measurement.value != threshold else 0
	else:
		raise Exception(r"Threshold classification: Invalid relation {relation}.")

def classificationmethod_int_pct_error(measurement: Measurement, config: Config) -> int:
	assert isinstance(measurement, MeasurementInt)
	assert measurement.value >= 0 and measurement.value <= 100

	bucket_size: int = config.get_int_or_error("method_int_pct_error", "bucket_size")

	# put measurements into buckets of width `bucket_size`. The name of the
	# bucket is its middle element.
	# TODO: For bucket_size = 10, 100 maps to 105. OK?
	return (measurement.value // bucket_size) * bucket_size + (bucket_size // 2)

CLASSIFICATION_METHODS: Final[Dict[str, Callable[[Measurement, Config], int]]] = {
	"cache_count":         classificationmethod_cache_count,
	"cache_exact_address": classificationmethod_cache_exact_address,
	"int_threshold":       classificationmethod_int_threshold,
	"int_pct_error":       classificationmethod_int_pct_error
}