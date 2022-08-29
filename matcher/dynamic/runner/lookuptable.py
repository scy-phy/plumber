from typing import List

from util import cache_line_id, page_id, set_id
from constants import SET_MASK, SET_SHIFT

class Access:
	def __init__(self, idx: int, instruction_counter: int):
		self.idx: int = idx
		self.instruction_counter: int = instruction_counter

class LookupTableWithAccesses:
	def __init__(self, base_addr: int, element_size: int, no_elements: int) -> None:
		self.base_addr: int = base_addr
		self.element_size: int = element_size
		self.no_elements: int = no_elements
		self.accesses: List[Access] = []

	def _validate_idx(self, idx: int) -> None:
		if idx < 0 or idx >= self.no_elements:
			raise Exception("Invalid index.")
	
	def record_access(self, idx: int, instruction_counter: int) -> None:
		self._validate_idx(idx)
		self.accesses.append(Access(idx, instruction_counter))
	
	def idx_to_addr(self, idx: int) -> int:
		self._validate_idx(idx)
		return self.base_addr + idx * self.element_size

	def idx_to_cache_line_id(self, idx: int) -> int:
		self._validate_idx(idx)
		element_addr = self.idx_to_addr(idx)
		return cache_line_id(element_addr)

	def idx_to_page_id(self, idx: int) -> int:
		self._validate_idx(idx)
		element_addr = self.idx_to_addr(idx)
		return page_id(element_addr)

	def idx_to_set(self, idx: int) -> int:
		self._validate_idx(idx)
		element_addr = self.idx_to_addr(idx)
		return set_id(element_addr)