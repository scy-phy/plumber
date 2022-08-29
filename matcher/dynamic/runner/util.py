import time

from typing import List, IO

from constants import CACHE_LINE_SHIFT, PAGE_SHIFT, SET_SHIFT, SET_MASK

def cache_line_id(addr: int) -> int:
	return addr >> CACHE_LINE_SHIFT

def page_id(addr: int) -> int:
	return addr >> PAGE_SHIFT

def set_id(addr: int) -> int:
	return (addr & SET_MASK) >> SET_SHIFT

def proc_wait_for_output(stream: IO[bytes], msg: str) -> None:
	while True:
		line = stream.readline()
		if msg in line.decode():
			break
		time.sleep(0.05)

def hit_ratios_to_classification(hit_ratios_per_cache_line: List[float]) -> List[str]:
	pre = [0, 1, 2, 3, 4, 5, 6]
	tab = [7, 8, 9]
	post = [10, 11, 12, 13, 14, 15, 16]

	classifications = []
	pre_count = 0
	for idx in reversed(pre):
		if hit_ratios_per_cache_line[idx] < 0.5:
			break
		pre_count += 1
	if pre_count > 0:
		classifications.append(f"P{pre_count}")
		# classifications.append(f"-P{pre_count}")
	
	post_count = 0
	for idx in post:
		if hit_ratios_per_cache_line[idx] < 0.5:
			break
		post_count += 1

	if post_count > 0:
		classifications.append(f"P{post_count}")

	if len(classifications) == 0:
		classifications.append("P0")

	return classifications
