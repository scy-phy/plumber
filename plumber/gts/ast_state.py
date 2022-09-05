from __future__ import annotations

import re

from typing import Dict, Optional, List, Set

from .codegen import CodeGenerator

class ExpansionState:
	"""
	This class keeps state information during expansion of operators. Most
	importantly, it provides access to the loop variables that are
	currently valid (in scope). It further provides access to a code
	generator object which is used by the fuzzing operators to get the bit
	positions to fuzz (which address bits are offset bits or set bits?).
	"""
	class Scope:
		def __init__(self, variables: Dict[str, int] = {}) -> None:
			self.variables: Dict[str, int] = variables
		
		def put_var(self, identifier: str, value: int) -> None:
			self.variables[identifier] = value
		
		def get_var(self, identifier: str) -> Optional[int]:
			if identifier in self.variables:
				return self.variables[identifier]
			else:
				return None
		
		def is_defined(self, identifier: str) -> bool:
			return identifier in self.variables

	def __init__(self, generator: CodeGenerator) -> None:
		self.scopes: List[ExpansionState.Scope] = []
		self.generator: CodeGenerator = generator
		
	def get_var_value(self, identifier: str) -> Optional[int]:
		for scope in reversed(self.scopes):
			result = scope.get_var(identifier)
			if result is not None:
				return result
		return None

	def is_var_defined(self, identifier: str) -> bool:
		for scope in reversed(self.scopes):
			if scope.is_defined(identifier):
				return True
		return False

	def push_scope(self, scope: Scope) -> None:
		self.scopes.append(scope)

	def pop_scope(self) -> None:
		self.scopes.pop()
