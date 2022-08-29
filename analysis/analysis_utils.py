from __future__ import annotations

import sympy
from typing import List, Optional, Tuple, Dict, Iterator, TYPE_CHECKING
if TYPE_CHECKING:
	from classification.measurement import Measurement

def selectN(
	bittable: List[Measurement],
	reg_names: List[str], bits_idxs: List[Tuple[int, int]], bits_values: List[int]
) -> Iterator[Measurement]:
	"""
	Similar to SQL select: filter bittable such that only contains
	testcases where the bits indicated by bit_idxs in register[reg_name]
	are equal to bits_value. Implemented as a generator function.
	
	This variant of the function allows to specify multiple conditions.
	Condition i is specified by reg_names[i], bit_idxs[i] and
	bits_values[i]. (Thus, all three lists must have equal length.)
	
	:param      bittable:        The bittable
	:type       bittable:        List[Measurement]
	:param      reg_names:       Conditions: The register names
	:type       reg_names:       List[str]
	:param      bits_idxs:       Conditions: The range of fuzzed bits
	                             (lower bound incl., upper bound excl.)
	:type       bits_idxs:       List[Tuple[int, int]]
	:param      bits_values:     Conditions: The expected bit values to
	                             filter for
	:type       bits_values:     List[int]
	
	:returns:   Iterator; corresponds to filtered bittable
	:rtype:     Iterator[Measurement]
	"""
	assert len(reg_names) == len(bits_idxs) == len(bits_values)
	len_inputs: int = len(reg_names)

	masks: List[int] = [(1 << (bits_idx[1] - bits_idx[0])) - 1 for bits_idx in bits_idxs]
	shifts: List[int] = [bits_idx[0] for bits_idx in bits_idxs]

	for measurement in bittable:
		match = True
		for i in range(len_inputs):
			registers: Dict[str, int] = measurement.register_contents()
			if reg_names[i] not in registers:
				raise Exception("Error during select: selected register was not used.")
			if not ((registers[reg_names[i]] >> shifts[i]) & masks[i]) == (bits_values[i] & masks[i]):
				match = False
				break
		if match:
			yield measurement

def select1(
	bittable: List[Measurement],
	reg_name: str, bits_idx: Tuple[int, int], bits_value: int
) -> Iterator[Measurement]:
	"""
	Similar to SQL select: filter bittable such that only contains
	testcases where the bits indicated by bit_idxs in register[reg_name]
	are equal to bits_value. Implemented as a generator function.
	
	This variant of the function allows to specify only one condition.
	
	:param      bittable:    The bittable
	:type       bittable:    List[Measurement]
	:param      reg_name:    Condition: The register names
	:type       reg_name:    str
	:param      bits_idx:    Condition: The range of fuzzed bits  (lower
	                         bound incl., upper bound excl.)
	:type       bits_idx:    Tuple[int, int]
	:param      bits_value:  Condition: The expected bit values to filter
	                         for
	:type       bits_value:  int
	
	:returns:   Iterator; corresponds to filtered bittable
	:rtype:     Iterator[Measurement]
	"""
	return selectN(bittable, [reg_name], [bits_idx], [bits_value])

def occN(
	bittable: List[Measurement],
	reg_names: List[str], bits_idxs: List[Tuple[int, int]], bits_values: List[int]
) -> int:
	"""
	Performs a select, but returns the number of results instead of the
	actual list of results.According to the paper, occ = count o select;
	count corresponds to len() in python.
	
	This variant of the function allows to specify multiple conditions.
	Condition i is specified by reg_names[i], bit_idxs[i] and
	bits_values[i]. (Thus, all three lists must have equal length.)
	
	:param      bittable:     The bittable
	:type       bittable:     List[Measurement]
	:param      reg_names:    Conditions: The register names
	:type       reg_names:    List[str]
	:param      bits_idxs:    Conditions: The range of fuzzed bits  (lower
	                          bound incl., upper bound excl.)
	:type       bits_idxs:    List[Tuple[int, int]]
	:param      bits_values:  Conditions: The expected bit values to filter
	                          for
	:type       bits_values:  List[int]
	
	:returns:   Number of matches for the select query
	:rtype:     int
	"""
	return len(list(selectN(bittable, reg_names, bits_idxs, bits_values)))

def occ1(
	bittable: List[Measurement],
	reg_name: str, bits_idx: Tuple[int, int], bits_value: int
) -> int:
	"""
	Performs a select, but returns the number of results instead of the
	actual list of results.According to the paper, occ = count o select;
	count corresponds to len() in python.
	
	This variant of the function allows to specify only one condition.
	
	:param      bittable:    The bittable
	:type       bittable:    List[Measurement]
	:param      reg_name:    Condition: The register names
	:type       reg_name:    str
	:param      bits_idx:    Condition: The range of fuzzed bits  (lower
	                         bound incl., upper bound excl.)
	:type       bits_idx:    Tuple[int, int]
	:param      bits_value:  Condition: The expected bi values to filter
	                         for
	:type       bits_value:  int
	
	:returns:   Number of matches for the select query
	:rtype:     int
	"""
	return len(list(select1(bittable, reg_name, bits_idx, bits_value)))

def expectedN(
	n: int, no_registers: int, bits_idx: Tuple[int, int]
) -> int:
	"""
	Returns the exepcted number of occurrences of each value if no
	undocumented behavior occurred.
	
	:param      n:             1 for single addresses, 2 for pairs of
	                           addresses (interrelated addresses)
	:type       n:             int
	:param      no_registers:  Number of registers in the bittable
	:type       no_registers:  int
	:param      bits_idx:      The range of fuzzed bits  (lower bound
	                           incl., upper bound excl.)
	:type       bits_idx:      Tuple[int, int]
	
	:returns:   Expected number of occurrences
	:rtype:     int
	"""
	no_fuzzed_bits: int = bits_idx[1] - bits_idx[0]
	return (1 << no_fuzzed_bits * (no_registers - n))

def expected1(
	no_registers: int, bits_idx: Tuple[int, int]
) -> int:
	"""
	Returns the exepcted number of occurrences if no undocumented behavior
	occurred.
	
	:param      no_registers:  Number of registers in the bittable
	:type       no_registers:  int
	:param      bits_idx:      The range of fuzzed bits  (lower bound
	                           incl., upper bound excl.)
	:type       bits_idx:      Tuple[int, int]
	
	:returns:   Expected number of occurrences
	:rtype:     int
	"""
	return expectedN(1, no_registers, bits_idx)

def relation2(
	addr1_bits: int, addr2_bits: int, bits_idx: Tuple[int, int], symbols: Tuple[sympy.Symbol,sympy.Symbol]
) -> sympy.Poly:
	"""
	Expresses the relation between two addresses in a linear equation.
	
	:param      addr1_bits:  The fuzzed bits from address 1
	:type       addr1_bits:  int
	:param      addr2_bits:  The fuzzed bits from address 2
	:type       addr2_bits:  int
	:param      bits_idx:    The range of fuzzed bits  (lower bound incl.,
	                         upper bound excl.)
	:type       bits_idx:    Tuple
	:param      symbols:     The sympy symbols
	:type       symbols:     Tuple[sympy.Symbol,sympy.Symbol]
	
	:returns:   Sympy Polynomial that represents the linear relation
	:rtype:     sympy.Poly
	"""
	return sympy.Poly(
		symbols[0] * addr1_bits + symbols[1] - addr2_bits,
		modulus=(1 << (bits_idx[1]-bits_idx[0]))
	)
