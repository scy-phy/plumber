from configparser import ConfigParser

from typing import Optional

class Config:

	def __init__(self, path: str) -> None:
		self.config: ConfigParser = ConfigParser()
		self.config.read(path)

	def get_str(self, section: str, option: str) -> Optional[str]:
		return self.config.get(section=section, option=option, fallback=None)

	def get_int(self, section: str, option: str) -> Optional[int]:
		value: Optional[str] = self.get_str(section, option)
		return None if value is None else int(value)

	def get_str_or_error(self, section: str, option: str) -> str:
		value: Optional[str] = self.get_str(section, option)
		if value is None:
			raise Exception(f"Missing configuration option: section={section}, option={option}")
		return value

	def get_int_or_error(self, section: str, option: str) -> int:
		value: str = self.get_str_or_error(section, option)
		try:
			value_int: int = int(value)
			return value_int
		except ValueError as err:
			raise ValueError(f"Expected integer value for configuration option: section={section}, option={option}. Got: {value}")