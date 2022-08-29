from __future__ import annotations

import random

from typing import Optional, Set, List

class Pool:
	"""
	Data structure to keep the available sets/tags. I used
	random.shuffle(List[int]) and list.pop() before, but it was very slow
	because shuffling needs many random numbers and random number
	generation is slow.
	
	This solution is way faster since it reduces the number of required
	random numbers significantly. This is how it works:
	- this data structure only keeps numbers from <lower> to <upper-1>.
	- while many elements are remaining in the pool, just choose a random
	  element, take a note that this element was used, and return it. On
	  collisions, just retry.
	- once 70% of the elements are taken, it will be more likely that
	  randomly chosen values are already taken. Therefore change the
	  strategy: build a list of the remaining elements and shuffle the
	  list. Since this list is smaller than the list of all elements, it
	  does not require that many random values for shuffling. All
	  subsequent requests will now be served by just removing the last
	  element from the list and returning it (List.pop() is O(1)).
	"""
	def __init__(self, lower: int, upper: int):
		self.lower: int = lower # incl
		self.upper: int = upper # excl
		self._remaining: int = self.capacity()
		self._taken: Set[int] = set()
		self._remainder: List[int] = []

	def __len__(self) -> int:
		return self._remaining

	def capacity(self) -> int:
		"""
		Returns the maximum number of elements in this pool

		:returns:   Maximum number of elements
		:rtype:     int
		"""
		return self.upper - self.lower

	def in_bounds(self, value: int) -> bool:
		"""
		Returns whether the given value is between self.lower and
		self.upper, i.e., a valid element of this pool.
		
		:param      value:  The value
		:type       value:  int
		
		:returns:   Whether the given value is a valid element of this pool
		            (True) or not (False)
		:rtype:     bool
		"""
		return value >= self.lower and value < self.upper

	def poprand(self) -> Optional[int]:
		"""
		Returns a random element from the pool and removes it from the pool.

		:returns:   int if len(self) > 0, None otherwise.
		:rtype:     Optional[int]
		"""
		if self._remaining == 0:
			return None
		if (self._remaining / (self.capacity())) > 0.3:
			candidate: int = random.randrange(self.lower, self.upper)
			while candidate in self._taken:
				candidate = random.randrange(self.lower, self.upper)

			self._taken.add(candidate)
			self._remaining -= 1
			return candidate
		else:
			if len(self._remainder) == 0:
				for i in range(self.lower, self.upper):
					if i not in self._taken:
						self._remainder.append(i)
				random.shuffle(self._remainder)
			self._remaining -= 1
			self._taken.add(candidate)
			return self._remainder.pop()

	def pop(self, value: int) -> None:
		"""
		Removes the given value from the pool.
		
		:param      value:  The value
		:type       value:  int
		
		:returns:   -
		:rtype:     None
		"""
		if self.in_bounds(value) and value not in self._taken:
			self._taken.add(value)
			self._remaining -= 1
			if len(self._remainder) > 0:
				self._remainder.remove(value)

	def taken(self, value: int) -> bool:
		"""
		Returns whether the given value is taken (no longer element of the
		pool) or not.
		
		:param      value:  The value
		:type       value:  int
		
		:returns:   Whether the given value is taken or not
		:rtype:     bool
		"""
		return value in self._taken

	def reset(self) -> None:
		"""
		Resets the pool to its initial state, i.e. after reset, it contains
		the values [0, ..., n-1] again.
		
		:returns:   -
		:rtype:     None
		"""
		self._taken = set()
		self._remainder = []
		self._remaining = self.capacity()