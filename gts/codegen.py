from __future__ import annotations

import abc
import random
import re
import json

from enum import Enum
from typing import List, Callable, Dict, Tuple, Set, Optional, TYPE_CHECKING
if TYPE_CHECKING:
	from .ast_directives import Directive, DirectiveAttributeValueParts
	from .ast_attributes import AttributeAddress, AttributeOperand, AttributeConditionOperand

from .codegen_pool import Pool

class CGDestination(Enum):
	SETUP = 0
	PRECONDITION = 1
	MAIN = 2

class CodegenOffsetException(Exception):
	pass

class CodeGenerator(metaclass=abc.ABCMeta):
	def __init__(self) -> None:
		self.pool_sets: Pool # to be initialized in subclass
		self.pool_tags: Pool # to be initialized in subclass
		self.reset()

	# may be overridden/extended by subclasses!
	def reset(self, reset_mappings: bool = True) -> None:
		"""
		Resets the internal state of the code generator. If the same code
		generator object is used to generate code for multiple experiments,
		this function should be called after each experiment. If subsequent
		experiments shall use the same placeholder mappings as the previous
		experiment, specifiy `reset_mappings`=False.
		
		:param      reset_mappings:  Whether placeholder mappings shall be
		                             reset
		:type       reset_mappings:  bool
		
		:returns:   -
		:rtype:     None
		"""
		self.code_setup: str = ""
		self.code_precondition: str = ""
		self.code_main: str = ""
		self.destination: CGDestination = CGDestination.MAIN

		self.pool_register: List[str] = self._build_pool_register()
		if reset_mappings:
			self.pool_sets.reset()
			self.pool_tags.reset()

			self.table_set_name_to_set_no: Dict[str, int] = dict()
			self.table_tag_name_to_tag_no: Dict[str, int] = dict()
			self.table_operand_name_to_value: Dict[str, int] = dict()
			self.table_condition_name_to_stored_operand_offset: Dict[str, int] = dict()
		self.table_value_to_reg: Dict[int, str] = dict()

		# handle state of store_base_address etc.
		if reset_mappings:
			# generate random base address for storing comparison operators
			# for B directive.
			store_set: Optional[int] = self.pool_sets.poprand()
			store_tag: Optional[int] = self.pool_tags.poprand()
			assert store_set is not None and store_tag is not None
			self.store_reserved_sets: Set[int] = set({store_set})
			self.store_reserved_tags: Set[int] = set({store_tag})
			self.store_base_address: int = 0 \
				| (store_set << self.shift_set()) \
				| (store_tag << self.shift_tag())
			self.store_next_offset: int = 0
		else:
			# if deterministic mode, recover setup code to keep operands in
			# memory
			self._restore_store_base_address()

	def _restore_store_base_address(self) -> None:
		if len(self.table_condition_name_to_stored_operand_offset) > 0:
			self._write_code_setup_store_base_register()
			for stored_operand_offset in self.table_condition_name_to_stored_operand_offset.values():
				self._write_code_setup_store_int(stored_operand_offset, 0)
				if stored_operand_offset > self.store_next_offset:
					self.store_next_offset = stored_operand_offset
			self.store_next_offset += 8

	# functions to store/load the placeholder mappings to/from JSON
	# (required for deterministic mode)
	def dump_mappings(self) -> str:
		return json.dumps({
			"table_set_name_to_set_no": self.table_set_name_to_set_no,
			"table_tag_name_to_tag_no": self.table_tag_name_to_tag_no,
			"table_operand_name_to_value": self.table_operand_name_to_value,
			"table_condition_name_to_stored_operand_offset": self.table_condition_name_to_stored_operand_offset,
			"store_base_address": self.store_base_address
		})
	def load_mappings(self, json_state: str) -> None:
		self.reset(reset_mappings=True)
		state: Dict = json.loads(json_state)
		if "table_set_name_to_set_no" in state:
			self.table_set_name_to_set_no = state["table_set_name_to_set_no"]
		if "table_tag_name_to_tag_no" in state:
			self.table_tag_name_to_tag_no = state["table_tag_name_to_tag_no"]
		if "table_operand_name_to_value" in state:
			self.table_operand_name_to_value = state["table_operand_name_to_value"]
		if "table_condition_name_to_stored_operand_offset" in state:
			self.table_condition_name_to_stored_operand_offset = state["table_condition_name_to_stored_operand_offset"]
		if "store_base_address" in state:
			self.store_base_address = state["store_base_address"]
			self.pool_sets.reset()
			self.pool_tags.reset()
			self._restore_store_base_address()

		for set_no in self.table_set_name_to_set_no.values():
			self.pool_sets.pop(set_no)
		for tag_no in self.table_tag_name_to_tag_no.values():
			self.pool_tags.pop(tag_no)
		for stored_operand_offset in self.table_condition_name_to_stored_operand_offset.values():
			offset: int = self._assign_stored_value_offset()
			self._write_code_setup_store_int(offset, 0)

	# helper functions to build the mappings from placeholders (like s1, t1, c1, o1)
	# to actual values (set address bits, tag address bits, etc.)
	def _placeholder_to_tag(self, tag_name: str) -> int:
		if tag_name not in self.table_tag_name_to_tag_no:
			tag_no_tmp: Optional[int] = self.pool_tags.poprand()
			if tag_no_tmp is not None:
				self.table_tag_name_to_tag_no[tag_name] = tag_no_tmp
			else:
				raise Exception("No tag left.")
		tag_no: int = self.table_tag_name_to_tag_no[tag_name]
		return tag_no

	def _placeholder_to_set(self, set_name: str) -> int:
		if set_name not in self.table_set_name_to_set_no:
			set_no_tmp: Optional[int] = self.pool_sets.poprand()
			if set_no_tmp is not None:
				self.table_set_name_to_set_no[set_name] = set_no_tmp
			else:
				raise Exception("No set left.")
		set_no: int = self.table_set_name_to_set_no[set_name]
		return set_no

	def _placeholder_to_operand_value(self, operand_name: str) -> int:
		if operand_name not in self.table_operand_name_to_value:
			self.table_operand_name_to_value[operand_name] = random.randrange(0, 1 << 64)
		return self.table_operand_name_to_value[operand_name]

	def _placeholder_to_condition_stored_operand_offset(self, condition_name: str) -> int:
		if condition_name not in self.table_condition_name_to_stored_operand_offset:
			offset: int = self._assign_stored_value_offset()
			self.table_condition_name_to_stored_operand_offset[condition_name] = offset
			self._write_code_setup_store_int(offset, 0)
		return self.table_condition_name_to_stored_operand_offset[condition_name]

	def _map_value_to_register(self, value: int) -> str:
		"""
		Reserves a general-purpose register and sets it to the specified
		value in the setup code.
		
		:param      value:      The value
		:type       value:      int
		
		:returns:   Name of the reserved register
		:rtype:     str
		
		:raises     Exception:  Raised if no registers are left in the
		                        register pool.
		"""
		if value not in self.table_value_to_reg:
			if len(self.pool_register) > 0:
				reg = self.pool_register.pop()
				self.table_value_to_reg[value] = reg
				self._write_code_set_up_register(reg, value)
			else:
				raise Exception("No register left.")
		return self.table_value_to_reg[value]

	def _assign_stored_value_offset(self) -> int:
		# ensure that we have the store base address stored in a register.
		# if not, write it into the register that was reserved for this purpose.
		if self.store_next_offset == 0:
			self._write_code_setup_store_base_register()
			
		# assign offset for this value in memory
		offset: int = self.store_next_offset
		# check for set/tag collisions and invalid offsets
		set_no: int = ((self.store_base_address + offset) & self.mask_set()) >> self.shift_set()
		if set_no not in self.store_reserved_sets:
			if self.pool_sets.taken(set_no):
				raise CodegenOffsetException("Could not write store for branch: set collision with prior Memory Directive.")
			else: 
				self.pool_sets.pop(set_no)
				self.store_reserved_sets.add(set_no)
		tag_no: int = ((self.store_base_address + offset) & self.mask_tag()) >> self.shift_tag()
		if tag_no not in self.store_reserved_tags:
			if self.pool_tags.taken(tag_no):
				raise CodegenOffsetException("Could not write store for branch: tag collision with prior Memory Directive.")
			else: 
				self.pool_tags.pop(tag_no)
				self.store_reserved_tags.add(tag_no)

		if offset >= self._max_immediate_offset():
			raise Exception("Maximum immediate offset exceeded.")

		self.store_next_offset += 8
		return offset

	# helper functions to put the setup code and main code together
	def _write(self, codeline: str) -> None:
		self._write_to_dest(self.destination, codeline)
	def _write_to_setup(self, codeline: str) -> None:
		self._write_to_dest(CGDestination.SETUP, codeline)
	def _write_to_dest(self, destination: CGDestination, codeline: str) -> None:
		if not codeline[-1] == "\n":
			codeline += "\n"
		if not codeline[0] == "\t":
			codeline = "\t" + codeline
		if destination == CGDestination.SETUP:
			self.code_setup += codeline
		elif destination == CGDestination.PRECONDITION:
			self.code_precondition += codeline
		elif destination == CGDestination.MAIN:
			self.code_main += codeline
		else:
			raise Exception("Unknown CGDestination")

	def generate_setup(self) -> str:
		"""
		Returns the generated setup code

		:returns:   The generated setup code
		:rtype:     str
		"""
		return "\t// SETUP\n" + self.code_setup + "\n\t// PRECONDITION\n" + self.code_precondition

	def generate_main(self) -> str:
		"""
		Returns the generated main code
		
		:returns:   The generated main code
		:rtype:     str
		"""
		return self.code_main[:]

	def generate_register_contents_json(self) -> str:
		return json.dumps({regname: value for value, regname in self.table_value_to_reg.items()})

	# Code generation functions for each of the directives (to be called from DirectiveXXX.codegen)
	def arithmetic(self, op1: AttributeOperand, op2: AttributeOperand) -> None:
		op1_value: int = self._placeholder_to_operand_value(op1.placeholder)
		op2_value: int = self._placeholder_to_operand_value(op2.placeholder)
	
		reg_op1: str = self._map_value_to_register(op1_value)
		reg_op2: str = self._map_value_to_register(op2_value)

		self._write_code_arithmetic(reg_op1, reg_op2)

	def branch(self, condition_operand_imm: AttributeConditionOperand, distance: int) -> None:
		stored_operand_offset: int = self._placeholder_to_condition_stored_operand_offset(condition_operand_imm.placeholder)
		self._write_code_branch(stored_operand_offset, condition_operand_imm.bool, distance)

	def store_condition_operand(self, condition_operand_stored: AttributeConditionOperand) -> None:
		stored_operand_offset: int = self._placeholder_to_condition_stored_operand_offset(condition_operand_stored.placeholder)
		value: int = 0 if condition_operand_stored.bool else 1
		self._write_code_main_store_int(stored_operand_offset, value)

	def memory_load(self, address: AttributeAddress) -> None:
		set_no: int = 0
		if address.set.override is None:
			set_no = self._placeholder_to_set(address.set.placeholder())
			set_offset: int = address.set.offset()
			if set_offset > 0:
				set_no += address.set.offset()
				if not self.pool_sets.in_bounds(set_no):
					raise CodegenOffsetException("Set offset not in bounds!")
				else:
					self.pool_sets.pop(set_no)
		else:
			set_no = self.pool_sets.lower + address.set.override
			self.pool_sets.pop(set_no)
			if not self.pool_sets.in_bounds(set_no):
				raise CodegenOffsetException("Set offset not in bounds!")
		
		tag_no: int = 0
		if address.tag.override is None:
			tag_no = self._placeholder_to_tag(address.tag.placeholder())
			tag_offset: int = address.tag.offset()
			if tag_offset > 0:
				tag_no += address.tag.offset()
				if not self.pool_tags.in_bounds(tag_no):
					raise CodegenOffsetException("Tag offset not in bounds!")
				else:
					self.pool_tags.pop(tag_no)
		else:
			tag_no = self.pool_tags.lower + address.tag.override
			self.pool_tags.pop(tag_no)
			if not self.pool_tags.in_bounds(tag_no):
				raise CodegenOffsetException("Tag offset not in bounds!")
		
		offset: int = address.offset.offset
		if offset >= self.no_offsets():
			raise CodegenOffsetException("Address offset too large!")

		addr: int = 0 \
			| (tag_no << self.shift_tag()) \
			| (set_no << self.shift_set()) \
			| (offset << self.shift_offset())	
		reg_addr: str = self._map_value_to_register(addr)
		self._write_code_memory_load(reg_addr)
	
	def nop(self) -> None:
		self._write_code_nop()

	# abstract functions that describe the target architecture
	# - list of general-purpose registers
	@staticmethod
	@abc.abstractmethod
	def _build_pool_register() -> List[str]:
		pass
	# - specification of address bits
	@staticmethod
	@abc.abstractmethod
	def address_bits_offset() -> Tuple[int, int]:
		pass
	@staticmethod
	@abc.abstractmethod
	def address_bits_set() -> Tuple[int, int]:
		pass
	@staticmethod
	@abc.abstractmethod
	def address_bits_tag() -> Tuple[int, int]:
		pass
	# - max. immediate offset for load instruction
	@staticmethod
	@abc.abstractmethod
	def _max_immediate_offset() -> int:
		pass
	
	# convenience functions to work with addresses
	@classmethod
	def no_sets(cls) -> int:
		lower, upper = cls.address_bits_set()
		return (1 << (upper - lower))
	@classmethod
	def no_tags(cls) -> int:
		lower, upper = cls.address_bits_tag()
		return (1 << (upper - lower))
	@classmethod
	def no_offsets(cls) -> int:
		lower, upper = cls.address_bits_offset()
		return (1 << (upper - lower))
	@classmethod
	def shift_set(cls) -> int:
		return cls.address_bits_set()[0]
	@classmethod
	def shift_tag(cls) -> int:
		return cls.address_bits_tag()[0]
	@classmethod
	def shift_offset(cls) -> int:
		return cls.address_bits_offset()[0]
	@classmethod
	def mask_set(cls) -> int:
		lower, upper = cls.address_bits_set()
		return ((1 << (upper - lower)) - 1) << lower
	@classmethod
	def mask_tag(cls) -> int:
		lower, upper = cls.address_bits_tag()
		return ((1 << (upper - lower)) - 1) << lower
	@classmethod
	def mask_offset(cls) -> int:
		lower, upper = cls.address_bits_offset()
		return ((1 << (upper - lower)) - 1) << lower

	# (abstract) assembly code generation functions
	@abc.abstractmethod
	def _write_code_arithmetic(self, reg_op1: str, reg_op2: str) -> None:
		pass
	@abc.abstractmethod
	def _write_code_branch(self, operand_addr_offset: int, bool_immediate: bool, distance: int) -> None:
		pass
	@abc.abstractmethod
	def _write_code_memory_load(self, reg_source: str) -> None:
		pass
	@abc.abstractmethod
	def _write_code_nop(self) -> None:
		pass
	@abc.abstractmethod
	def _write_code_set_up_register(self, reg: str, value: int) -> None:
		pass
	@abc.abstractmethod
	def _write_code_setup_store_base_register(self) -> None:
		pass
	@abc.abstractmethod
	def _write_code_setup_store_int(self, offset: int, value64: int) -> None:
		pass
	@abc.abstractmethod
	def _write_code_main_store_int(self, offset: int, value: int) -> None:
		pass

class CodeGeneratorARMA64(CodeGenerator):
	def __init__(self) -> None:
		self.pool_sets: Pool = Pool(0, self.no_sets())
		self.pool_tags: Pool = Pool(0x80000000 >> self.shift_tag(), 0xC0000000 >> self.shift_tag())
		self.store_base_register: str = "x1"
		super().__init__()

	@staticmethod
	def address_bits_offset() -> Tuple[int, int]:
		# (incl., excl.)
		return (0, 6)
	@staticmethod
	def address_bits_set() -> Tuple[int, int]:
		return (6, 13)
	@staticmethod
	def address_bits_tag() -> Tuple[int, int]:
		return (13, 32)
	@staticmethod
	def _max_immediate_offset() -> int:
		return 4096
	@staticmethod
	def _build_pool_register() -> List[str]:
		return [f"x{i}" for i in range (30, 1, -1)]

	def _write_code_arithmetic(self, reg_op1: str, reg_op2: str) -> None:
		mnemonic: str = random.choice([
			"add", "eor"
		])
		self._write(f"{mnemonic} x0, {reg_op1}, {reg_op2}")

	def _write_code_branch(self, operand_addr_offset: int, bool_immediate: bool, distance: int) -> None:
		assert self.store_base_register is not None
		assert distance % 4 == 0
		self._write(f"ldr x0, [{self.store_base_register}, #{operand_addr_offset}]")
		self._write(f"cmp x0, #{1 if bool_immediate else 0}")
		self._write(f"b.ne 0x{distance:x}")

	def _write_code_memory_load(self, reg_source: str) -> None:
		self._write(f"ldr x0, [{reg_source}]")
	
	def _write_code_nop(self) -> None:
		self._write("nop")

	def _write_code_set_up_register(self, reg: str, value: int) -> None:
		self._write_to_setup(f"// {reg} = {value:016x}")
		# info: str = f"// set: {((value >> self.shift_set()) & (self.mask_sets()))}"
		# info += f", tag: {((value >> self.shift_tag()) & (self.mask_tags()))}"
		# info += f", off: {((value >> self.shift_offset()) & (self.mask_offsets()))}"
		# self._write_to_setup(info)
		for i in range(0, 64, 16):
			self._write_to_setup(f"movk {reg}, #0x{(value & (0xffff << i)) >> i:04x}, lsl #{i}")

	def _write_code_setup_store_base_register(self) -> None:
		self._write_to_setup("// Base address for memory stores")
		self._write_code_set_up_register(self.store_base_register, self.store_base_address)

	def _write_code_setup_store_int(self, offset: int, value64: int) -> None:
		# generate code to write the given value64 to memory
		self._write_to_setup(f"// MEM[0x{self.store_base_address:016x} + {offset}] =LONG= 0x{value64:016x}")
		self._write_code_set_up_register("x0", value64)
		self._write_to_setup(f"str x0, [{self.store_base_register}, #{offset}]")
		self._write_to_setup(f"mov x0, #0")

	def _write_code_main_store_int(self, offset: int, value: int) -> None:
		assert self.store_base_register is not None
		self._write(f"mov x0, #{value}")
		self._write(f"str x0, [{self.store_base_register}, #{offset}]")
