import re

from typing import TextIO, Match, Optional

# some helper functions for TextIO
def readline_or_raise_on_eof(file: TextIO) -> str:
	line: str = file.readline()
	if len(line) == 0: # end of file
		raise Exception("Error parsing executor output. Unexpected EOF.")
	return line

def expect_or_raise(line: str, expected: str) -> None:
	if line.rstrip() != expected:
		raise Exception(f"Error parsing executor output. Expected '{expected.rstrip()}', got '{line.rstrip()}'.")

def move_until_str(file: TextIO, expected: str) -> None:
	while True:
		line: str = readline_or_raise_on_eof(file)
		if line == expected:
			return

def move_until_regex(file: TextIO, regex: str) -> Match[str]:
	while True:
		line: str = readline_or_raise_on_eof(file)
		rx: Optional[Match[str]] = re.match(regex, line)
		if rx:
			return rx

# Helper function to read Makefile.config
def read_measurement_method(file_path: str) -> str:
	with open(file_path, "r") as file:
		for line in file:
			rx: Optional[Match[str]] = re.match(r"^MEASUREMENT\s+=([A-Za-z_]*)$", line)
			if rx:
				return rx.group(1)
	raise Exception("Could not find measurement method in Makefile.config")