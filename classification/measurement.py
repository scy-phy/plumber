from __future__ import annotations

import abc
import os
import re
import json

from typing import Optional, Dict, List, Tuple, Match, TextIO

from .measurement_utils import readline_or_raise_on_eof, expect_or_raise, \
	move_until_str, move_until_regex

class Measurement(metaclass=abc.ABCMeta):
	def __init__(self, experiment_dir: str) -> None:
		self.experiment_dir: str = experiment_dir
		self._register_contents: Optional[Dict[str, int]] = None

		# start parsing the executor output
		executor_output_file_path: str = os.path.join(experiment_dir, f"uart.log")
		with open(executor_output_file_path, "r") as executor_output_file:
			# search for initial line ("Init complete.")
			move_until_str(executor_output_file, "Init complete.\n")
			# delegrate further parsing to subclasses
			self._parse_specific(executor_output_file)

	@abc.abstractmethod
	def _parse_specific(self, executor_output_file: TextIO) -> None:
		pass

	def register_contents(self) -> Dict[str, int]:
		# when this function is called for the first time, the register
		# contents are read from the experiment's register.json file. The
		# contents are then cached to be reused in later calls.
		if self._register_contents is None:
			registers_json_file_path: str = os.path.join(self.experiment_dir, "registers.json")
			if os.path.isfile(registers_json_file_path):
				with open(registers_json_file_path) as registers_json_file:
					self._register_contents = json.loads(registers_json_file.read())
			else:
				raise Exception("Cound not find registers.json file")
		assert self._register_contents is not None
		return self._register_contents

class MeasurementCache(Measurement):
	def __init__(self, experiment_dir: str) -> None:
		# Dict[Cache Level, List[Tuple[set, tag]]
		self.cache_contents: Dict[int, List[Tuple[int, int]]] = dict()
		super().__init__(experiment_dir)

	def _parse_specific(self, file: TextIO) -> None:
		while True:
			# read lines until "Experiment complete"
			line: str = readline_or_raise_on_eof(file).rstrip()
			if line == "Experiment complete.":
				break
			
			# Identify beginning of cache dump, extract cache level,
			# delegate parsing the contents
			rx_level: Optional[Match[str]] = re.match(r"^L(\d) output$", line)
			if rx_level:
				cache_level: int = int(rx_level.group(1))
				self.cache_contents[cache_level] = []
				self._parse_cache_contents(file, self.cache_contents[cache_level])

		if len(self.cache_contents) == 0:
			raise Exception("Error parsing executor output: No cache output found.")

	def _parse_cache_contents(self, file: TextIO, this_cache_contents: List[Tuple[int, int]]) -> None:
		# skip over the next two lines
		expect_or_raise(file.readline(), "print_cache_valid")
		expect_or_raise(file.readline(), "----")

		# parse cache contents and store them in the given data structure
		while True:
			line: str = file.readline()
			if len(line) == 0:
				raise Exception("Error parsing executor output: EOF while parsing cache contents.")
			if line == "----\n":
				break

			rx_content: Optional[Match[str]] = re.match(r"^(\d+)\s+::\d+\s+::\stag: ([0-9a-fA-F]+)\n$", line)
			if not rx_content:
				print(line)
				raise Exception("Error parsing executor output: Malformed cache content line.")
			
			set_no: int = int(rx_content.group(1))
			tag_no: int = int(rx_content.group(2), 16)
			this_cache_contents.append((set_no, tag_no))

class MeasurementInt(Measurement):
	def __init__(self, experiment_dir: str, name: str) -> None:
		self.name: str = name
		self.value: int
		super().__init__(experiment_dir)

	def _parse_specific(self, file: TextIO) -> None:
		rx: Match[str] = move_until_regex(file, rf"^{self.name};(\d+)$")
		result: int = int(rx.group(1))
		expect_or_raise(file.readline(), "Experiment complete.")
		self.value = result