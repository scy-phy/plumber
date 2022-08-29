from __future__ import annotations

import abc

from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
	from .codegen import CodeGenerator
	from .ast_directives import DirectiveAttributeValueParts
	from .ast_state import ExpansionState

from .ast_utils import ind, compute_effective_attribute_value
from .ast_node import ASTNode

class AttributeConditionOperand(ASTNode):
	def __init__(self, value_parts_condition: DirectiveAttributeValueParts, value_parts_bool: DirectiveAttributeValueParts
	) -> None:
		assert isinstance(value_parts_condition[0][1], str)
		assert isinstance(value_parts_bool[0][1], str)

		self.placeholder: str = value_parts_condition[0][1]
		if value_parts_bool[0][1] == "T":
			self.bool: bool = True
		elif value_parts_bool[0][1] == "F":
			self.bool = False
		else:
			raise SyntaxError("Invalid token for bool attribute")
	
	def to_str(self, indent: int) -> str:
		return f"ConditionOperand(placeholder: {self.placeholder}," + \
			f" bool: {self.bool})"

class AttributeOperand(ASTNode):
	def __init__(self, value_parts: DirectiveAttributeValueParts) -> None:
		assert isinstance(value_parts[0][1], str)		
		self.placeholder: str = value_parts[0][1]
	
	def to_str(self, indent: int) -> str:
		return f"Operand(placeholder: {self.placeholder})"

class AttributeAddress(ASTNode):
	class SetOrTag(ASTNode, metaclass=abc.ABCMeta):
		def __init__(self, value_parts: DirectiveAttributeValueParts) -> None:
			self.value_parts: DirectiveAttributeValueParts = value_parts
			# fixed offset can be defined by operators
			self.fixed_offset: int = 0
			# computed_offset contains the offset defined through
			# value_parts. Since value_parts may contain variables,
			# computation of computed_offset has to be delayed until
			# expansion.
			self.computed_offset: Optional[int] = None
			self.override: Optional[int] = None
		
		def placeholder(self) -> str:
			assert isinstance(self.value_parts[0][1], str)
			return self.value_parts[0][1]

		def expand(self, state: ExpansionState) -> None:
			self.computed_offset = compute_effective_attribute_value(self.value_parts, state)

		def offset(self) -> int:
			assert self.computed_offset is not None
			return self.computed_offset + self.fixed_offset

		def to_str(self, indent: int) -> str:
			result: str = ind(indent) + self.__class__.__name__ + "("
			result += "val: "
			for value_part in self.value_parts:
				result += str(value_part[1]) + " "
			if len(self.value_parts) > 0:
				result = result[:-1]
			result += f", fixedoff: {self.fixed_offset}"
			result += f", compoff: {self.computed_offset}"
			result += f", overr: {self.override}"
			result += f")"
			return result

	class Set(SetOrTag):
		pass
	class Tag(SetOrTag):
		pass

	class Offset(ASTNode):
		def __init__(self, offset: int) -> None:
			self.offset: int = offset

		def to_str(self, indent: int) -> str:
			result: str = self.__class__.__name__ + "("
			result += str(self.offset)
			result += ")"
			return result

	def __init__(self, value_parts_set: DirectiveAttributeValueParts, value_parts_tag: DirectiveAttributeValueParts) -> None:
		self.set: AttributeAddress.Set = AttributeAddress.Set(value_parts_set)
		self.tag: AttributeAddress.Tag = AttributeAddress.Tag(value_parts_tag)
		self.offset: AttributeAddress.Offset = AttributeAddress.Offset(0)

	def to_str(self, indent: int) -> str:
		return f"Address({self.set.to_str(0)}, {self.tag.to_str(0)}, {self.offset.to_str(0)})"