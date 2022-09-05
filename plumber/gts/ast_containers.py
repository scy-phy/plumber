from __future__ import annotations

import os

from typing import Union, Optional, Tuple, List, TYPE_CHECKING
if TYPE_CHECKING:
	from .ast_directives import Directive
	from .ast_operators import Operator

from .ast_utils import ind, ast_product_list_of_sets
from .ast_state import ExpansionState
from .ast_node import ASTNode, ASTNodeExpandable

from .codegen import CodeGenerator, CGDestination

class Expression(ASTNodeExpandable):
	"""
	This class describes an expression, i.e. an AST node that contains any
	number of Directives and/or Operators.
	"""
	def __init__(self) -> None:
		self.children: List[Union[Directive, Operator]] = []
	
	def append_child(self, child: Union[Directive, Operator]) -> None:
		self.children.append(child)

	def to_str(self, indent: int) -> str:
		result = self.__class__.__name__ + "("
		if len(self.children) > 0:
			for child in self.children:
				result += "\n"
				result += child.to_str(indent+1)
				result += ","
			result = result[:-1] + "\n"
		result += ind(indent) + ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		if len(self.children) == 0:
			raise SyntaxError("Empty expression cannot be expanded")

		expanded_children: List[List[List[Directive]]] = []
		for child in self.children:
			expanded_children.append(child.expand(state))
		result = ast_product_list_of_sets(expanded_children)
		return result

class GTS(ASTNode):
	"""
	Root node of an AST describing a GTS (Generative Testcase Specification)
	"""
	def __init__(self, precondition: Optional[Expression] = None, expression: Optional[Expression] = None) -> None:
		self.precondition = precondition
		self.expression = expression

	def to_str(self, indent: int = 0) -> str:
		result = self.__class__.__name__
		result += "(\n"
		result += "\tprecondition: " + ("None" if not self.precondition else self.precondition.to_str(indent+1)) + ",\n"
		result += "\texpression:   " + ("None" if not self.expression else self.expression.to_str(indent+1)) + "\n"
		result += ")"
		return result

	def expand(self, state: ExpansionState) -> Tuple[Optional[List[List[Directive]]], List[List[Directive]]]:
		precondition_expanded: Optional[List[List[Directive]]] = None
		if self.precondition is not None:
			precondition_expanded = self.precondition.expand(state)
			if len(precondition_expanded) == 0:
				raise SyntaxError("Precondition must not be empty (you may omit it, though).")
			elif len(precondition_expanded) > 1:
				raise SyntaxError("Sets in preconditions are not supported.")

		if self.expression is not None:
			expression_expanded = self.expression.expand(state)
			if len(expression_expanded) == 0:
				raise SyntaxError("Expanded main expression of GTS must not be empty.")
		else:
			raise SyntaxError("Main expression of GTS must not be empty.")
		
		assert self.expression is not None
		return (precondition_expanded, expression_expanded)

	def codegen(self, generator: CodeGenerator, deterministic: Union[bool, str]) -> List[Tuple[str, str, str]]:
		result: List[Tuple[str, str, str]] = []

		# if deterministic and state json file exists, recover mappings before starting
		if deterministic is not False:
			assert isinstance(deterministic, str)
			if os.path.isfile(deterministic):
				with open(deterministic) as deterministic_state_file:
					generator.load_mappings(deterministic_state_file.read())

		# expand precondition and expression
		state: ExpansionState = ExpansionState(generator)
		expanded_precondition, expanded_expression = self.expand(state)
		
		# for each experiment, generate setup and main code section
		for experiment in expanded_expression:
			# reset generator state (if not deterministic)
			generator.reset(reset_mappings=(deterministic is False))

			# code generation for precondition
			if expanded_precondition is not None:
				# disallow sets in precondition; this is already handled in expand()
				assert len(expanded_precondition) == 1
		
				generator.destination = CGDestination.PRECONDITION
				for directive in expanded_precondition[0]:
					directive.codegen(generator)

			# code generation for expression
			generator.destination = CGDestination.MAIN
			for directive in experiment:
				directive.codegen(generator)
			
			result.append((generator.generate_setup(), generator.generate_main(), generator.generate_register_contents_json()))

		# if deterministic, store the final state of code generation mappings
		# in the specified json file
		if deterministic is not False:
			assert isinstance(deterministic, str)
			with open(deterministic, "w") as deterministic_state_file:
				deterministic_state_file.write(generator.dump_mappings())

		return result
