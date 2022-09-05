from __future__ import annotations

import abc

from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
	from .ast_directives import Directive
	from .ast_state import ExpansionState

class ASTNode(metaclass=abc.ABCMeta):
	"""
	This class describes common methods to all AST nodes.
	"""
	def __init__(self) -> None:
		pass
	
	@abc.abstractmethod
	def to_str(self, indent: int) -> str:
		"""
		Returns a string representation of this node in the AST.
		
		:param      indent:  The current indentation level
		:type       indent:  int
		
		:returns:   String representation of this ASTNode
		:rtype:     str
		"""
		pass
	
	def hash(self) -> int:
		"""
		Returns a hash of this node (including all child nodes). Can be
		used to check ASTNodes for equality.
		
		:returns:   Hash of this ASTNode (including its children)
		:rtype:     int
		"""
		return hash(self.to_str(0))

	def __repr__(self) -> str:
		return self.to_str(0)

class ASTNodeExpandable(ASTNode, metaclass=abc.ABCMeta):
	@abc.abstractmethod
	def expand(self, state: ExpansionState) -> List[List[Directive]]:
		"""
		Reduces this ASTNode (incl. all of its child nodes) to a set of
		experiments. Each experiments only consists of a list of
		directives.
		
		:param      state:  The current state (keeps track of variable
		                    definitions and values, etc.)
		:type       state:  ExpansionState
		
		:returns:   Set of experiments, where each experiment only consists
		            of Directives.
		:rtype:     List[List[Directive]]
		"""
		pass
