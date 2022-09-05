from __future__ import annotations

import itertools
import sympy

from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
if TYPE_CHECKING:
	from classification.measurement import Measurement

from .analysis_utils import occ1, occN, expected1, expectedN, relation2

def analyze_fuzzed_bits(classification: Dict[int, List[Measurement]], fuzzed_bits_idx: Tuple[int, int]) -> None:
	# generate a list of registers in the bit table
	# assumption: all testcases use the same set of registers
	registers: Optional[List[str]] = None
	for class_id, bittable in classification.items():
		if len(bittable) > 0:
			registers = list(bittable[0].register_contents().keys())
			break
	assert registers is not None
	
	no_fuzzed_bits: int = fuzzed_bits_idx[1] - fuzzed_bits_idx[0]

	# Analyze the bit tables one by one
	for class_id, bittable in classification.items():
		# Step 1: Candidate Selection on single addresses. For each
		# possible value of the fuzzed bits in each register, count and
		# compare the number of occurrences in the bittable with the
		# expected number if no hidden behavior occurred.
		candidate_addr_bits: List[Tuple[str, int]] = []
		no_expected_testcases: int = expected1(len(registers), fuzzed_bits_idx)
		for register in registers:
			for bits_value in range(1 << no_fuzzed_bits):
				count: int = occ1(bittable, register, fuzzed_bits_idx, bits_value)
				if count != no_expected_testcases:
					candidate_addr_bits.append((register, bits_value))
					print(f"Candidate address bits {candidate_addr_bits[-1]}")
		
		# Step 1': Candidate Selection on pairs of addresses. For each
		# possible combination of values in all possible pairs of
		# registers, count and compare the number of occurrences in the
		# bittable with the expected number if no hidden behavior occurred.
		candidate_interrelated_addr_bits: List[Tuple[Tuple[str, int],Tuple[str, int]]] = []
		no_expected_testcases = expectedN(2, len(registers), fuzzed_bits_idx)
		for register1, register2 in itertools.combinations(registers, 2):
			for bits_value1, bits_value2 in itertools.product(range(1 << no_fuzzed_bits), range(1 << no_fuzzed_bits)):
				count = occN(bittable, [register1, register2], [fuzzed_bits_idx, fuzzed_bits_idx], [bits_value1, bits_value2])
				if count != no_expected_testcases:
					candidate_interrelated_addr_bits.append(((register1, bits_value1), (register2, bits_value2)))
					print(f"Candidate interrelated address bits {candidate_interrelated_addr_bits[-1]}")

		# Step 2a: Relation Extraction for single candidate addresses: Find
		# constraints on single bits or sequences of bits.
		
		# Find all bits that are constant across all candidate addresses.
		constraints: List[Tuple[str, int, int]] = []
		for i in range(fuzzed_bits_idx[0], fuzzed_bits_idx[1]):
			first: Dict[str, Optional[int]] = dict()
			for register_name, addr_bits in candidate_addr_bits:
				bit: int = 0 if (addr_bits & (1 << i)) == 0 else 1
				if register_name not in first:
					first[register_name] = bit
					continue
				if first[register_name] is None:
					continue
				if first[register_name] != bit:
					first[register_name] = None
			for register_name, opt_bit in first.items():
				if opt_bit is not None:
					constraints.append((register_name, i, opt_bit))

		print(f"Identified Constraints (bit index, bit value): {constraints}")

		# Step 2b: Relation Extraction for candidate interrelated
		# addresses. For each previously collected pair of candidate
		# interrelated addresses, transform the relation into a linear
		# equation y=ax+b mod |S_c|, where x and y are the interrelated
		# address bits. Collect these equations per register pair. Then,
		# for each register pair, try to solve the system of equations.
		polynomials_per_regpair: Dict[str, List[sympy.Poly]] = dict()
		symbols = sympy.symbols('a b')
		for cir1, cir2 in candidate_interrelated_addr_bits:
			register1, bits_value1 = cir1
			register2, bits_value2 = cir2
			polynomial: sympy.Poly = relation2(bits_value1, bits_value2, fuzzed_bits_idx, symbols)
			polynomials_per_regpair.setdefault(f"{register1}_{register2}", []).append(polynomial)

		relations: List[Tuple[str, int, int]] = []
		for register_pair, polynomials in polynomials_per_regpair.items():
			if len(polynomials) >= 2:
				result: Dict[sympy.Symbol, int] = sympy.solve(polynomials, list(symbols))
				if symbols[0] in result and symbols[1] in result:
					relations.append((register_pair, result[symbols[0]], result[symbols[1]]))
					print(f"Class {class_id}: Found relation: {register_pair}: y = {result[symbols[0]]} * x + {result[symbols[1]]}")

		# Step 3: Relation Validation
		# - Validate constraints (find out how may of the values in the
		#   same register have the same bit value at the relevant position)
		for register_name, i, bit in constraints:
			cnt_constraints_sat: int = 0
			cnt_constraints_all: int = 0
			for measurement in bittable:
				register_contents: Dict[str, int] = measurement.register_contents()
				if (
					register_name in register_contents
					and (register_contents[register_name] & (1 << i)) == (bit << i)
				):
					cnt_constraints_sat += 1
				cnt_constraints_all += 1
			
			print(f"Class {class_id}: constraint: {register_name}, bit {i} is {bit}" +
				f" -- match rate: {cnt_constraints_sat}/{cnt_constraints_all} ({cnt_constraints_sat/cnt_constraints_all})")
		
		# - Validate Relations
		for relation in relations:
			cnt_rel_sat: int = 0
			cnt_rel_all: int = 0

			register_pair, value_a, value_b = relation
			reg1, reg2 = register_pair.split("_")

			for measurement in bittable:
				register_contents = measurement.register_contents()
				if (
					reg1 in register_contents
					and reg2 in register_contents
					and register_contents[reg2] == (value_a * register_contents[reg1] + value_b) % (1 << no_fuzzed_bits)
				):
					cnt_rel_sat += 1
				cnt_rel_all += 1
			
			print(f"Class {class_id}: relation {register_pair}: y = {value_a} * x + {value_b}" +
				f" -- match rate: {cnt_rel_sat}/{cnt_rel_all} ({cnt_rel_sat/cnt_rel_all})")