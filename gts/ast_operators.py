from __future__ import annotations

import abc
import random
import itertools

import copy

from enum import Enum
from typing import Union, Optional, Tuple, Dict, List, TYPE_CHECKING
if TYPE_CHECKING:
	from .codegen import CodeGenerator
	from .ast_directives import Directive
	from .ast_containers import Expression

from .ast_state import ExpansionState
from .ast_node import ASTNodeExpandable
from .ast_utils import ind, swap_pivots, ast_list_unique
from .ast_directives import DirectiveMemory, DirectiveNop, DirectiveBranch, DirectiveArithmetic
	
class Operator(ASTNodeExpandable, metaclass=abc.ABCMeta):
	pass

class OperatorLoop(Operator):
	def __init__(self, expression: Expression, end: int, step: int = 1, loopvar: Optional[str] = None) -> None:
		self.end = end
		self.step = step
		self.loopvar = loopvar
		self.expression = expression
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "\n"
		result += ind(indent) + f"\tend: {self.end}, step: {self.step}, loopvar: {self.loopvar},\n"
		result += ind(indent) +  "\texpression: " + self.expression.to_str(indent+1) + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		if self.step == 1 and self.loopvar is None:
			resultA: List[List[Directive]] = []
			experimentsA: List[List[Directive]] = self.expression.expand(state)
			for experimentA in experimentsA:
				new_experimentA: List[Directive] = []
				for i in range(self.end):
					new_experimentA = new_experimentA + experimentA
				resultA.append(new_experimentA)
			return resultA
		else:
			resultB: List[Directive] = []
			scope = ExpansionState.Scope()
			state.push_scope(scope)
			for i in range(0, self.end, self.step):
				assert self.loopvar is not None
				scope.put_var(self.loopvar, i)
				experimentsB: List[List[Directive]] = self.expression.expand(state)
				assert len(experimentsB) == 1
				resultB.extend(experimentsB[0])
			state.pop_scope()
			return [resultB]

class OperatorWildcard(Operator):
	def __init__(self, no_wildcards: int) -> None:
		self.no_wildcards = no_wildcards
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += str(self.no_wildcards)
		result += ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		result: List[List[Directive]] = [[]]
		for i in range(self.no_wildcards):
			directive_choice = random.randrange(0, 2)
			if directive_choice == 0:
				result[0].append(DirectiveArithmetic({}).expand(state)[0][0])
			elif directive_choice == 1:
				result[0].append(DirectiveNop().expand(state)[0][0])
			# elif directive_choice == 2:
			# 	result[0].append(DirectiveBranch({}).expand(state)[0][0])
			else:
				assert False
		return result

class OperatorShuffle(Operator):
	def __init__(self, expression: Expression) -> None:
		self.expression = expression
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "\n"
		result += ind(indent) + "\texpression: " + self.expression.to_str(indent+1) + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		result: List[List[Directive]] = []
		experiments: List[List[Directive]] = self.expression.expand(state)
		for experiment in experiments:
			shuffled_experiment: List[List[Directive]] = [
				list(x) for x in itertools.permutations(experiment)
			]
			shuffled_experiment = ast_list_unique(shuffled_experiment)
			result.extend(shuffled_experiment)
		return result

class OperatorSubset(Operator):
	def __init__(self, expression: Expression) -> None:
		self.expression = expression
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "\n"
		result += ind(indent) + "\texpression: " + self.expression.to_str(indent+1) + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		result: List[List[Directive]] = []
		experiments: List[List[Directive]] = self.expression.expand(state)
		for experiment in experiments:
			powerset: List[List[Directive]] = [
				list(x) for x in itertools.chain.from_iterable(
					itertools.combinations(experiment, r) for r in range(1, len(experiment))
				)
			]
			powerset = ast_list_unique(powerset)
			result.extend(powerset)
		return result

class OperatorSlide(Operator):
	def __init__(self, expression: Expression, n: int) -> None:
		self.expression = expression
		self.n = n
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "\n"
		result += ind(indent) + "\texpression: " + self.expression.to_str(indent+1) + ",\n"
		result += ind(indent) + f"\tn: {self.n}" + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		result: List[List[Directive]] = []
		experiments: List[List[Directive]] = self.expression.expand(state)
		for experiment in experiments:
			directives_M: List[int] = []
			for i, directive in enumerate(experiment):
				if isinstance(directive, DirectiveMemory):
					directives_M.append(i)
			if len(directives_M) == 0:
				# if there are none, just keep the experiment as it is.
				result.append(experiment)
			else:
				# Otherwise, copy the experiment self.n times. For each copy,
				# add an increasing counter to the set attribute of all M
				# directives.
				for i in range(self.n):
					experiment_copy = experiment[:]
					for location in directives_M:
						experiment_copy[location] = copy.deepcopy(experiment[location])
						assert isinstance(experiment_copy[location], DirectiveMemory)
						experiment_copy[location].address.set.fixed_offset += i
					result.append(experiment_copy)
		return result

class OperatorMerge(Operator):
	def __init__(self, expression1: Expression, expression2: Expression) -> None:
		self.expression1 = expression1
		self.expression2 = expression2
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "\n"
		result += ind(indent) + "\texpression1: " + self.expression1.to_str(indent+1) + ",\n"
		result += ind(indent) + "\texpression2: " + self.expression2.to_str(indent+1) + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		result: List[List[Directive]] = []
		expanded1: List[List[Directive]] = self.expression1.expand(state)
		expanded2: List[List[Directive]] = self.expression2.expand(state)
		
		if len(expanded1) != 1 or len(expanded2) != 1:
			raise SyntaxError("Merge on sets of experiments not supported (yet).")

		combined: List[Directive] = expanded1[0] + expanded2[0]
		result.append(combined)

		# Build list of pivot positions. The pivot always points to the
		# first of the two elements to be swapped.
		pivots = set()

		# add initial pivot position
		pivots.add(len(expanded1[0]) - 1)

		# perform first swap at initial pivot position
		updated: List[Directive] = swap_pivots(combined, pivots)
		result.append(updated)

		# first, generate the mutated lists while the number of pivot positions is
		# growing
		pivots_growing = True
		while pivots_growing:	
			# update pivot positions
			for pivot in list(pivots):
				# remove current pivot position
				pivots.remove(pivot)

				# add new pivot positions
				pivot_low = pivot - 1
				pivot_high = pivot + 1
				if pivot_low <= 0:
					pivots_growing = False
				if pivot_low >= 0:
					pivots.add(pivot_low)
				if pivot_high + 1 < len(combined):
					pivots.add(pivot_high)
			
			# swap elements at pivot positions
			if len(pivots) >= 1:
				updated = swap_pivots(updated, pivots)
				result.append(updated)

		# second, generate the mutated lists while the number of pivot positions is
		# shrinking
		pivots_shrinking = True
		while pivots_shrinking:
			# update pivot positions
			old_pivots = sorted(list(pivots))
			for i in range(0, len(old_pivots)):
				pivot = old_pivots[i]
				# remove current pivot position
				pivots.remove(pivot)

				# add new pivot positions
				pivot_low = pivot - 1
				pivot_high = pivot + 1
				if pivot_low >= 0 and i > 0:
					pivots.add(pivot_low)
				if pivot_high + 1 < len(combined) and i < len(old_pivots) - 1:
					pivots.add(pivot_high)

			if len(pivots) <= 1:
				pivots_shrinking = False

			# swap elements at pivot positions
			if len(pivots) >= 1:
				updated = swap_pivots(updated, pivots)
				result.append(updated)

		return result

class OperatorFuzz(Operator):
	def __init__(self, expression: Expression, fuzz_type: str) -> None:
		self.expression: Expression = expression
		self.fuzz_type: str = fuzz_type
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "\n"
		result += ind(indent) + "\texpression: " + self.expression.to_str(indent+1) + ",\n"
		result += ind(indent) + f"\tfuzz_type: {self.fuzz_type}" + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		result: List[List[Directive]] = []
		experiments: List[List[Directive]] = self.expression.expand(state)
		
		for experiment in experiments:
			directives_M: List[int] = []
			# collect all M directives in the current experiment
			for i, directive in enumerate(experiment):
				if isinstance(directive, DirectiveMemory):
					directives_M.append(i)
			if len(directives_M) == 0:
				# if there are none, just keep the experiment as it is.
				result.append(experiment)
			else:
				# Otherwise, copy the experiment many times to fuzz the
				# requested bits.
				
				# determine which bits to fuzz
				num_fuzzed_bits: int = 0
				if self.fuzz_type == "FUZZ_OFFSET_AT": # offset fuzzing
					offset_bit_lower, offset_bit_upper = state.generator.address_bits_offset()
					num_fuzzed_bits = offset_bit_upper - offset_bit_lower
				elif self.fuzz_type == "FUZZ_CL_DOLLAR": # cache line fuzzing
					set_bit_lower, set_bit_upper = state.generator.address_bits_set()
					num_fuzzed_bits = set_bit_upper - set_bit_lower
				else:
					raise SyntaxError("Unknown fuzz type")
				
				# iterate over these bits; multiply the experiment such that
				# every possible combination of the fuzzed bits is covered.
				fuzzed_bits_mask = (1 << (num_fuzzed_bits)) - 1
				for offsets in range(0, 1 << (num_fuzzed_bits * len(directives_M))):
					experiment_copy = experiment[:]
					for i, location in enumerate(directives_M):
						offset = (offsets & (fuzzed_bits_mask << (num_fuzzed_bits * i))) >> (num_fuzzed_bits * i)
						experiment_copy[location] = copy.deepcopy(experiment[location])
						assert isinstance(experiment_copy[location], DirectiveMemory)
						if self.fuzz_type == "FUZZ_OFFSET_AT": # offset fuzzing
							experiment_copy[location].address.offset.offset = offset
							experiment_copy[location].address.set.override = 0
							experiment_copy[location].address.tag.override = 0
						elif self.fuzz_type == "FUZZ_CL_DOLLAR": # cache line fuzzing
							experiment_copy[location].address.offset.offset = 0
							experiment_copy[location].address.set.override = offset
							experiment_copy[location].address.tag.override = 0
						else:
							raise SyntaxError("Unknown fuzz type")
						
					result.append(experiment_copy)

		return result

class OperatorRepetition(Operator):
	def __init__(self, expression: Expression, n: int) -> None:
		self.expression = expression
		self.n = n
	
	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "\n"
		result += ind(indent) + "\texpression: " + self.expression.to_str(indent+1) + ",\n"
		result += ind(indent) + f"\tn: {self.n}" + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		result: List[List[Directive]] = []
		experiments: List[List[Directive]] = self.expression.expand(state)
		for _ in range(self.n):
			for experiment in experiments:
				result.append(experiment)
		return result