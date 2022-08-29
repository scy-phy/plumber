from __future__ import annotations

import abc
import copy
import re

from enum import Enum
from typing import Union, Optional, Tuple, Dict, List
from typing_extensions import TypeAlias

from .codegen import CodeGenerator
from .ast_utils import ind
from .ast_node import ASTNodeExpandable
from .ast_attributes import AttributeConditionOperand, AttributeOperand, AttributeAddress
from .ast_state import ExpansionState

class ArithmeticOperator(Enum):
	PLUS = 0
	MINUS = 1

	@staticmethod
	def from_str(s: str) -> Optional[ArithmeticOperator]:
		if s == "+":
			return ArithmeticOperator.PLUS
		elif s == "-":
			return ArithmeticOperator.MINUS
		return None

class Directive(ASTNodeExpandable, metaclass=abc.ABCMeta):
	@abc.abstractmethod
	def codegen(self, generator: CodeGenerator) -> None:
		pass

# List[ (token.type, value) ]
DirectiveAttributeValuePart: TypeAlias = Tuple[str, Union[str, int, ArithmeticOperator]]
DirectiveAttributeValueParts: TypeAlias = List[DirectiveAttributeValuePart]

class DirectiveArithmetic(Directive):
	def __init__(self, attributes: Dict[str, DirectiveAttributeValueParts]) -> None:
		# if one of the operands was not specified, fall back to default values
		for name in ["u", "v"]:
			if name not in attributes:
				attributes[name] = [("IDENTIFIER", "oDEFAULT")]
		# attribute sanity check
		for name, value_parts in attributes.items():
			if name not in ["u", "v"]:
				raise SyntaxError("Invalid attribute name.")
			else:
				if not value_parts[0][0] == "IDENTIFIER":
					raise SyntaxError("Invalid attribute: must start with IDENTIFIER token.")
				if not (isinstance(value_parts[0][1], str) and re.match(r"^o(\d+|DEFAULT)$", value_parts[0][1])):
					raise SyntaxError("Invalid attribute: first value token does not match expected pattern for this kind of placeholder.")

		self.operand_u: AttributeOperand = AttributeOperand(attributes["u"])
		self.operand_v: AttributeOperand = AttributeOperand(attributes["v"])

	def codegen(self, generator: CodeGenerator) -> None:
		generator.arithmetic(self.operand_u, self.operand_v)

	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "u: " + self.operand_u.to_str(0) + ", "
		result += "v: " + self.operand_v.to_str(0)
		result += ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		return [[self]]

class DirectiveBranch(Directive):
	def __init__(self, attributes: Dict[str, DirectiveAttributeValueParts]) -> None:
		# defaults
		if "c" not in attributes:
			attributes["c"] = [("IDENTIFIER", "cDEFAULT")]
		if "b" not in attributes:
			attributes["b"] = [("IDENTIFIER", "T")]
		if "d" not in attributes:
			attributes["d"] = [("DIGITS", 12)]

		# attribute sanity check
		for name, value_parts in attributes.items():
			if name not in ["c", "b", "d"]:
				raise SyntaxError("Invalid attribute name.")
			else:
				if name in ["c", "b"] and not value_parts[0][0] == "IDENTIFIER":
					raise SyntaxError("Invalid attribute: must start with IDENTIFIER token.")
				if name == ["d"] and not value_parts[0][0] == "DIGITS":
					raise SyntaxError("Invalid attribute: must start with DIGITS token.")
				if name == "c" and not (isinstance(value_parts[0][1], str) and re.match(r"^c(\d+|DEFAULT)$", value_parts[0][1])):
					raise SyntaxError("Invalid attribute: first value token does not match expected pattern for this kind of placeholder.")
				if name == "b" and not (isinstance(value_parts[0][1], str) and re.match(r"^[TF]$", value_parts[0][1])):
					raise SyntaxError("Invalid attribute: first value token does not match expected pattern for this kind of placeholder.")
				if name == "d" and not isinstance(value_parts[0][1], int):
					raise SyntaxError("Invalid attribute: first value token is not a number")
		
		self.condition_operand_imm: AttributeConditionOperand = AttributeConditionOperand(attributes["c"], attributes["b"])
		assert isinstance(attributes["d"][0][1], int)
		self.distance: int = attributes["d"][0][1]

	def codegen(self, generator: CodeGenerator) -> None:
		generator.branch(self.condition_operand_imm, self.distance)

	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "condition_operand_imm: " + self.condition_operand_imm.to_str(indent)
		result += ", distance: " + str(self.distance)
		result += ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		return [[self]]

class DirectiveStoreConditionOperand(Directive):
	def __init__(self, attributes: Dict[str, DirectiveAttributeValueParts]) -> None:
		# defaults
		if "c" not in attributes:
			attributes["c"] = [("IDENTIFIER", "cDEFAULT")]
		if "b" not in attributes:
			attributes["b"] = [("IDENTIFIER", "T")]

		# attribute sanity check
		for name, value_parts in attributes.items():
			if name not in ["c", "b"]:
				raise SyntaxError("Invalid attribute name.")
			else:
				if name in ["c", "b"] and not value_parts[0][0] == "IDENTIFIER":
					raise SyntaxError("Invalid attribute: must start with IDENTIFIER token.")
				if name == "c" and not (isinstance(value_parts[0][1], str) and re.match(r"^c(\d+|DEFAULT)$", value_parts[0][1])):
					raise SyntaxError("Invalid attribute: first value token does not match expected pattern for this kind of placeholder.")
				if name == "b" and not (isinstance(value_parts[0][1], str) and re.match(r"^[TF]$", value_parts[0][1])):
					raise SyntaxError("Invalid attribute: first value token does not match expected pattern for this kind of placeholder.")
		
		self.condition_operand_stored: AttributeConditionOperand = AttributeConditionOperand(attributes["c"], attributes["b"])

	def codegen(self, generator: CodeGenerator) -> None:
		generator.store_condition_operand(self.condition_operand_stored)

	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "condition_operand_stored: " + self.condition_operand_stored.to_str(indent)
		result += ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		return [[self]]


class DirectiveMemory(Directive):
	def __init__(self, attributes: Dict[str, DirectiveAttributeValueParts]) -> None:
		# if tag and/or set was not specified, fall back to default values
		for name in ["s", "t"]:
			if name not in attributes:
				attributes[name] = [("IDENTIFIER", f"{name}DEFAULT")]

		# attribute sanity check
		for name, value_parts in attributes.items():
			if name not in ["s", "t"]:
				raise SyntaxError("Invalid attribute name.")
			else:
				if not value_parts[0][0] == "IDENTIFIER":
					raise SyntaxError("Invalid attribute: must start with IDENTIFIER token.")
				if not (isinstance(value_parts[0][1], str) and re.match(r"^" + name + r"(\d+|DEFAULT)$", value_parts[0][1])):
					raise SyntaxError("Invalid attribute: first value token does not match expected pattern for this kind of placeholder.")

		self.address: AttributeAddress = AttributeAddress(attributes["s"], attributes["t"])

	def codegen(self, generator: CodeGenerator) -> None:
		generator.memory_load(self.address)

	def to_str(self, indent: int) -> str:
		result = ind(indent) + self.__class__.__name__ + "("
		result += "address: " + self.address.to_str(indent)
		result += ")"
		return result

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		# we only need to copy M if at least one of its set/tag attributes
		# contains variables (such as loop variables). if both attributes
		# only consist of a placeholder, we can safely represent them with
		# the same object.
		if len(self.address.set.value_parts) > 1 or len(self.address.tag.value_parts) > 1:
			cp = copy.deepcopy(self)
			cp.address.set.expand(state)
			cp.address.tag.expand(state)
			return [[cp]]
		else:
			self.address.set.expand(state)
			self.address.tag.expand(state)
			return [[self]]

class DirectiveNop(Directive):
	def codegen(self, generator: CodeGenerator) -> None:
		generator.nop()

	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		return [[self]]

	def to_str(self, indent: int) -> str:
		return ind(indent) + self.__class__.__name__ + "()"