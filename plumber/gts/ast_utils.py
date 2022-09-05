from __future__ import annotations

from typing import List, Set, Iterable, Optional, Sequence, TYPE_CHECKING
if TYPE_CHECKING:
	from .ast_node import ASTNode
	from .ast_directives import Directive, DirectiveAttributeValueParts, DirectiveAttributeValuePart
	from .ast_state import ExpansionState

def ind(indent: int) -> str:
	"""
	Helper function to indent to_str output properly.
	
	:param      indent:  The current indentation level
	:type       indent:  int
	
	:returns:   String containing n tabs
	:rtype:     str
	"""
	return "\t" * indent

def ast_list_unique(l: List[List[Directive]]) -> List[List[Directive]]:
	"""
	Removes duplicate `List[Directive]`s from a `List[List[Directive]]`.
	Duplicates are identified based on the XOR-sum of the `.hash()`es of
	their `Directive`s.
	
	:param      l:    Input list
	:type       l:    List[List[Directive]]
	
	:returns:   Output list (= input list w/o duplicates)
	:rtype:     List[List[Directive]]
	"""
	seen: Set[int] = set()
	result: List[List[Directive]] = []
	for elem in l:
		elem_hash = ast_list_hash(elem)
		if elem_hash not in seen:
			seen.add(elem_hash)
			result.append(elem)
	return result

def ast_list_hash(l: Sequence[ASTNode]) -> int:
	"""
	Computes the hash of a list of ASTNodes.

	:param      l:    List
	:type       l:    Sequence[ASTNode]

	:returns:   Hash
	:rtype:     int
	"""
	result: int = 0
	for i, elem in enumerate(l):
		result ^= hash(str(i) + str(elem.hash()))
	return result

def ast_product_list_of_sets(expanded: List[List[List[Directive]]]) -> List[List[Directive]]:
	"""
	Given a `List[List[List[Directive]]]`, flatten it by one level of
	`List[]` by computing the product of the inner `List[List[Directive]]`s
	(left-to-right).

	Example:
	Input: [
		[[A B], [M]],
		[[A A], [M]],
		[[N]]
	]
	1st product: [
		[[A B A A], [A B M], [M A A], [M M]],
		[[N]]
	]
	2nd product, ouput: [
		[A B A A N], [A B M N], [M A A N], [M M N]
	]
	
	:param      expanded:  Input list
	:type       expanded:  List[List[List[Directive]]]
	
	:returns:   Output list
	:rtype:     List[List[Directive]]
	"""
	result: List[List[List[Directive]]] = expanded.copy()
	while len(result) > 1:
		result[0] = ast_product_of_sets(result[0], result[1])
		result.pop(1)
	return result[0]

def ast_product_of_sets(l1: List[List[Directive]], l2: List[List[Directive]]) -> List[List[Directive]]:
	"""
	Compute the product of two `List[List[Directive]]`.
	
	:param      l1:   First list
	:type       l1:   List[List[Directive]]
	:param      l2:   Second list
	:type       l2:   List[List[Directive]]
	
	:returns:   Output list: l1 x l2
	:rtype:     List[List[Directive]]
	"""
	result: List[List[Directive]] = []
	for l1elem in l1:
		for l2elem in l2:
			result.append(l1elem + l2elem)
	return result

def swap_pivots(l: List, pivots: Iterable[int]) -> List:
	"""
	Helper function for OperatorMerge: for each list index p in pivots,
	swap elements at index p and p+1 in l. If p or p+1 are out of bounds,
	the pivot position p is silently ignored (i.e. no swap will be peformed
	and no error will be raised).
	
	This function retains the original list as-is and works on a copy that
	is then returned.
	
	:param      l:       The list to swap elements in
	:type       l:       List
	:param      pivots:  The pivot positions
	:type       pivots:  Iterable[int]
	
	:returns:   The altered list
	:rtype:     List
	"""
	result = l[:]
	for pivot in pivots:
		i1 = pivot
		i2 = pivot + 1
		if i1 < 0 or i2 >= len(l):
			continue
		swap_elements(result, i1, i2)
	return result

def swap_elements(l: List, i1: int, i2: int) -> None:
	"""
	Helper function to swap two elements of a list (in-place).

	:param      l:    The list to alter
	:type       l:    List
	:param      i1:   First element index
	:type       i1:   int
	:param      i2:   Second element index
	:type       i2:   int

	:returns:   -
	:rtype:     None
	"""
	l[i1], l[i2] = l[i2], l[i1]


def compute_effective_attribute_value(value_parts: DirectiveAttributeValueParts, state: ExpansionState) -> int:
	"""
	Calculates the effective value of an attribute value with all variable
	identifiers resolved (based on the given expansion state).
	
	assumptions on value_parts:
	- value_parts[0] is placeholder -> ignored
	- all other value_parts are sequence of (ArithmeticOperator, digits or
	  identifier)
	
	:param      value_parts:     The value_parts
	:type       value_parts:     DirectiveAttributeValueParts
	:param      state:           The state
	:type       state:           ExpansionState
	
	:returns:   The effective attribute value.
	:rtype:     int
	
	:raises     SyntaxError:     In case of unexpected/malformed
	                             value_parts
	"""
	
	if len(value_parts) == 1:
		# only placeholder, no offset
		return 0
	elif len(value_parts) >= 3:
		# there is more. the rest of the arithmetic expression may or
		# may not contain variables.

		# copy value_parts and resolve all variable identifiers.
		value_parts_copy = value_parts[:]
		for i in range(1, len(value_parts_copy)):
			value_part: DirectiveAttributeValuePart = value_parts_copy[i]
			if value_part[0] == "IDENTIFIER":
				var_name = value_part[1]
				assert isinstance(var_name, str)
				var_value: Optional[int] = state.get_var_value(var_name)
				if var_value is not None:
					value_parts_copy[i] = ("DIGITS", var_value)
				else:
					raise SyntaxError(f"Could not resolve variable {var_name}.")
	
		# reduce the arithmetic expression to a single digit.
		# 1. assert that the value_parts are alternating sequence of
		#    (arithmetic operator, digits)
		for i in range(1, len(value_parts_copy)):
			if i % 2 == 1:
				if not value_parts_copy[i][0] in ["PLUS", "MINUS"]:
					raise SyntaxError("Invalid attribute value (arithmetic expression)")
			elif i % 2 == 0:
				if not value_parts_copy[i][0] == "DIGITS":
					raise SyntaxError("Invalid attribute value (arithmetic expression)")

		# 2. compute effective sum of all parts
		parts_sum: int = 0
		sign: int = 1
		for i in range(1, len(value_parts_copy)):
			kind, value = value_parts_copy[i]
			if kind == "PLUS":
				sign = 1
			elif kind == "MINUS":
				sign = -1
			elif kind == "DIGITS":
				assert isinstance(value, int)
				parts_sum += sign * value
		return parts_sum
	else:
		# value_parts != 0: should at least contain the placeholder
		# value_parts of 2 indicates missing operand (x+)
		raise SyntaxError("Invalid number of value_parts.")
