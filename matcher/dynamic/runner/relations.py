from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
	from lookuptable import LookupTableWithAccesses, Access

from constants import PREFETCH_DELTA_MAX
from util import page_id

def _compute_n(accesses: Tuple[Access, Access, Access]) -> Tuple[int, int]:
	n1 = accesses[1].instruction_counter - accesses[0].instruction_counter
	n2 = accesses[2].instruction_counter - accesses[1].instruction_counter
	return (n1, n2)

def _compute_stride_distances(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> Tuple[int, int]:
	sets = (
		lut.idx_to_set(accesses[0].idx),
		lut.idx_to_set(accesses[1].idx),
		lut.idx_to_set(accesses[2].idx)
	)
	dist1 = sets[1] - sets[0]
	dist2 = sets[2] - sets[1]
	return (dist1, dist2)

def _compute_addresses(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> Tuple[int, int]:
	addr_min = lut.idx_to_addr(accesses[0].idx)
	addr_max = lut.idx_to_addr(accesses[2].idx)
	return (addr_min, addr_max)

def _N3(accesses: Tuple[Access, Access, Access]) -> bool:
	n1, n2 = _compute_n(accesses)
	return (
		(n1 < 3 and n2 < 3) or
		(n1 == 5 and n2 == 0) or
		(n1 == 0 and n2 == 5)
	)

def _N4(accesses: Tuple[Access, Access, Access]) -> bool:
	n1, n2 = _compute_n(accesses)
	return (
		(n1 == 3 and n2 == 0) or
		(n1 == 0 and n2 == 3)
	)

def _N7(accesses: Tuple[Access, Access, Access]) -> bool:
	n1, n2 = _compute_n(accesses)
	return (
		(n1 == 4 and n2 == 0) or
		(n1 == 0 and n2 == 4)
	)

def _fulfills_P0(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	dist1, dist2 = _compute_stride_distances(lut, accesses)
	addr_min, addr_max = _compute_addresses(lut, accesses)
	
	return (
		(dist1 != dist2) or
		(dist1 == 0) or
		(abs(dist1) > PREFETCH_DELTA_MAX) or
		(page_id(addr_min) != page_id(addr_max)) or
		(page_id(addr_min) != page_id(addr_max + dist1))
	)

def _fulfills_P1(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	dist1, _ = _compute_stride_distances(lut, accesses)
	_, addr_max = _compute_addresses(lut, accesses)
	
	return (
		(_N3(accesses) or _N4(accesses) or _N7(accesses)) and
		(page_id(addr_max) != page_id(addr_max + 2 * dist1))
	)

def _fulfills_P2(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	dist1, _ = _compute_stride_distances(lut, accesses)
	_, addr_max = _compute_addresses(lut, accesses)
	
	return (
		(_N3(accesses) or _N4(accesses) or _N7(accesses)) and
		(page_id(addr_max) != page_id(addr_max + 3 * dist1))
	)

def _fulfills_P3(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	dist1, _ = _compute_stride_distances(lut, accesses)
	_, addr_max = _compute_addresses(lut, accesses)
	
	return (
		_N3(accesses) or (
			(_N4(accesses) or _N7(accesses)) and
			(page_id(addr_max) != page_id(addr_max + 4 * dist1))
		)
	)

def _fulfills_P4(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	dist1, _ = _compute_stride_distances(lut, accesses)
	_, addr_max = _compute_addresses(lut, accesses)
	
	return (
		_N4(accesses) or (
			_N7(accesses) and
			(page_id(addr_max) != page_id(addr_max + 5 * dist1))
		)
	)

def _fulfills_P5(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	dist1, _ = _compute_stride_distances(lut, accesses)
	_, addr_max = _compute_addresses(lut, accesses)
	
	return (
		_N7(accesses) and
		(page_id(addr_max) != page_id(addr_max + 6 * dist1))
	)

def _fulfills_P6(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	dist1, _ = _compute_stride_distances(lut, accesses)
	_, addr_max = _compute_addresses(lut, accesses)
	
	return (
		_N7(accesses) and
		(page_id(addr_max) != page_id(addr_max + 7 * dist1))
	)

def _fulfills_P7(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> bool:
	return (
		_N7(accesses)
	)

def relations_classify(lut: LookupTableWithAccesses, accesses: Tuple[Access, Access, Access]) -> str:
	if _fulfills_P0(lut, accesses):
		return "P0"
	elif _fulfills_P1(lut, accesses):
		return "P1"
	elif _fulfills_P2(lut, accesses):
		return "P2"
	elif _fulfills_P3(lut, accesses):
		return "P3"
	elif _fulfills_P4(lut, accesses):
		return "P4"
	elif _fulfills_P5(lut, accesses):
		return "P5"
	elif _fulfills_P6(lut, accesses):
		return "P6"
	elif _fulfills_P7(lut, accesses):
		return "P7"
	else:
		return "undecidable"