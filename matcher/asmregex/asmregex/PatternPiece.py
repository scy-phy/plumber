from __future__ import annotations
from typing import Optional, Dict, Tuple

__author__ = 'jordygennissen'

# global 
from enum import Enum
import logging
import re

class PatternConstraintType(Enum):
    CONSTRAINT_TYPE_ASSIGN = 0
    CONSTRAINT_TYPE_CHECK_EQ = 1
    CONSTRAINT_TYPE_CHECK_NEQ = 2
    
    @staticmethod
    def from_char(char: str) -> Optional[PatternConstraintType]:
      if char == "*":
        return PatternConstraintType.CONSTRAINT_TYPE_ASSIGN
      if char == "=":
        return PatternConstraintType.CONSTRAINT_TYPE_CHECK_EQ
      elif char == "!":
        return PatternConstraintType.CONSTRAINT_TYPE_CHECK_NEQ
      else:
        return None
    
    @staticmethod
    def to_char(constraint_type: PatternConstraintType) -> str:
      if constraint_type == PatternConstraintType.CONSTRAINT_TYPE_ASSIGN:
        return "*"
      elif constraint_type == PatternConstraintType.CONSTRAINT_TYPE_CHECK_EQ:
        return "="
      elif constraint_type == PatternConstraintType.CONSTRAINT_TYPE_CHECK_NEQ:
        return "!"
      else:
        return ""

class PatternConstraint:
  def __init__(self, arg_idx: int, capture_group: int, ctype: PatternConstraintType, name: str) -> None:
    self.arg_idx: int = arg_idx
    self.capture_group: int = capture_group
    self.ctype: PatternConstraintType = ctype
    self.name: str = name

  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} {self.arg_idx}:{self.capture_group}:{PatternConstraintType.to_char(self.ctype)}{self.name}>"

  def id(self) -> str:
    return self.name

class PatternConstraintStateStorage():
  def __init__(self) -> None:
    self.statestorage: Dict[str, str] = dict()

  def reset_state(self, constraint: PatternConstraint) -> None:
    del self.statestorage[constraint.id()]
  
  def set_state(self, constraint: PatternConstraint, state: str) -> None:
    self.statestorage[constraint.id()] = state

  def get_state(self, constraint: PatternConstraint) -> str:
    constraint_id: str = constraint.id()
    if constraint_id not in self.statestorage:
      raise RuntimeError("PatternConstraint: Tried to get empty state. Make sure to have an assign constraint (=) before using the corresponding check constriant (!).")
    return self.statestorage[constraint_id]

constraint_state_storage: PatternConstraintStateStorage = PatternConstraintStateStorage()

class PPType( Enum ):
  """Enumeration for the types of pieces inside an assembly regex """
  ASM = 0
  BEGIN = 1
  OR = 2
  END = 3
  ERROR = 4
  
def xor(bool1, bool2):
  return bool(bool1) != bool(bool2)


class PatternPiece ( object ):
  """Instance of a single piece of an assembly regex

  This class is an abstract class that is implemented in four ways:
  (0) The normal and general class is an assembly description.
      This is a general description of requirements 
      an assembly instruction should have to match the pattern
  (1) The second one is the Begin meta-object, specifying the beginning of a subpattern
  (2) The third is the OR Begin meta-object, specifying the beginning of an or subpattern
  (3) The fourth object is the End meta-object, specifying the end of the last subpattern
  attr: Type: PPType Enum specifying the type of piece
  """
  Type = PPType.ERROR


class PatternPieceTracker( object ):
  pass


class OrTracker( PatternPieceTracker ):
  
  def __init__(self, begin = None, middle = None, end = None):
    self.begin = begin
    self.middle = middle
    self.end = end
    self.subno = 'OR'

  def __getstate__(self):
    # Copy the object's state from self.__dict__ which contains
    # all our instance attributes. Always use the dict.copy()
    # method to avoid modifying the original state.
    state = self.__dict__.copy()
    # Remove the unpicklable entries.
    # del state['l']
    return state

  def __setstate__(self, state):
  # Restore instance attributes (i.e., filename and lineno).
    pass
  
  def reset(self):
    """ Returns self, as this tracker is stateless at runtime """
    return self  # OR tracker is stateless at runtime
  
  def is_valid(self):
    """ Returns True when all pointers are set """
    return self.begin is not None and self.middle is not None and self.end is not None
  
  def set_param(self, begin = None, middle = None, end = None):
    """ Sets one or more pointers """
    if begin is not None:
      self.begin = begin
    if middle is not None:
      self.middle = middle
    if end is not None:
      self.end = end
  
  def get_preferred_pptr(self):
    """ Returns the pointer towards the second (final) END object of this or """
    assert(self.is_valid())
    return self.end
  
  def get_alternative_pptr(self):
    """Returns pointer towards the first END object, hence the beginning of the second half of the or """
    assert (self.is_valid())
    return self.middle

class RepetitionTracker( PatternPieceTracker ):
  """The RepetitionTracker class tracks repetition subpatterns
  
  RepetitionTracker objects are objects linking the Begin meta-object (see above)
  and the End meta-object. Matching begins and ends both have a pointer to the same 
  RepetitionTracker. 
  
  :attr laziness: static default for each tracker on whether it should become lazy or not
  :attr begin: index in the regex list of the linked begin object
  :attr end: index in the regex list of the linked end object
  :attr subno: unique id for the subpattern, typically listing from 0 (all) onwards
  :attr lazy: if the mount if repetitions is a range, lazy will tell the matcher to 
              try to match with the least amount of repetitions (default: True) 
  :attr staticmin: min: minimum amount of repetitions according to the regular expression
  :attr min: minimum amount of repetitions to go (gets updated while matching)
  :attr staticmax: min: maximum amount of repetitions according to the regular expression
  :attr max: maximum amount of repetitions to go (gets updated while matching)
  :attr allowed: boolean indicating whether the current maximum is not 0
  :attr forced: boolean indicating whether the current minimum is 0 or None
  :attr l: the AsmRegex logger 
  """
  #laziness = True
  def __init__(self, subno):
    """Initialises a repetition tracker

    :param subno: unique id for the subpattern, typically listing from 0 (all) onwards
    :return: RepetitionTracker object
    """
    self.begin = None
    self.end = None
    self.subno = subno
    self.lazy = True # self.laziness
    self.staticmin = None
    self.min = None
    self.staticmax = None
    self.max = None
    self.allowed = False
    self.forced = True
    self.l = logging.getLogger('AsmRegex')

  def __getstate__(self):
    # Copy the object's state from self.__dict__ which contains
    # all our instance attributes. Always use the dict.copy()
    # method to avoid modifying the original state.
    state = self.__dict__.copy()
    # Remove the unpicklable entries.
    del state['l']
    return state

  def __setstate__(self, state):
    # Restore instance attributes (i.e., filename and lineno).
    self.l = logging.getLogger('AsmRegex')
    self.__dict__.update(state)
    
  def get_preferred_pptr(self):
    """Returns the next pattern pointer to use minus one
    
    :return: pattern pointer int
    """
    if not self.allowed or self.lazy and not self.forced:
      self.l.debug('Preferred next (forward)ptr: ' + str(self.end+1))
      return self.end
    else:
      self.l.debug('Preferred next (back)ptr: ' + str(self.begin + 1))
      return self.begin  # Not +1 because the pointer still gets updated after the check
  
  def get_alternative_pptr(self):
    """Returns the pptr value of the not preferred try
    
    Upon requesting this function, the choice should be true
    :return: pptr value
    """
    assert(self.choice())
    if self.is_lazy:
      self.l.debug('Alternative next (back)ptr: ' + str(self.begin + 1))
      return self.begin  # lazy so return the greedy one
    else:
      self.l.debug('Alternative next (forward)ptr: ' + str(self.end + 1))
      return self.end

  def set_param(self, begin=None, end=None):
    """Sets the index of the linked Begin or End meta-object

    :param begin: pointer to the linked Begin piece
    :param end: pointer to the linked End piece
    :return: None
    """
    if end is not None:
      self.end = end
    if begin is not None:
      self.begin = begin

  def set_minmax(self, minimum, maximum):
    """Sets the minimum and maximum amount of repetitions to be done.

    This is ONLY to be used while initialising, NOT while matching! This resets the static values.
    :param minimum: minimum amount of repetitions according to the regular expression
    :param maximum: maximum amount of repetitions according to the regular expression
    :return: None
    """
    if minimum and maximum and minimum > maximum:
      raise RuntimeWarning( "Mimimum loop is bigger than max: will never match!" )
    self.min = minimum
    self.max = maximum
    self.staticmin = self.min
    self.staticmax = self.max
    self.allowed = True  # max of 0 wouldn't make sense unless we start generating patterns?
    self.forced = False
    if self.min:  # min is not None and min is not 0
      self.forced = True

  def set_lazy(self, boolean):
    """Makes the subpattern matching lazy (already True by default)

    Lazy matching means it will try as few repetitions as possible,
    compared to greedy matching which is set by giving False as parameter
    :param boolean: whether the subpattern should be matched lazily or greedy
    :return: self
    """
    self.lazy = boolean
    return self

  @property
  def is_lazy(self):
    """Returns whether the subpattern should be matched lazily or not
    
    :return: True if lazy, False if greedy
    """
    return self.lazy

  def update(self):
    """Updates the tracker after a full match

    Decreases the mimimum and maximum amount of repetitions left to go by 1
    :return: self
    """
    if self.min and self.min > 0:
      self.min -= 1
      if self.min == 0: self.forced = False
    if self.max and self.max > 0:
      self.max -= 1
      if self.max == 0: self.allowed = False
    self.l.debug('RepTracker updates to ('+str(self.min)+', '+ str(self.max) + ')')
    return self

  def choice(self):
    """Returns if we are allowed to both continue or repeat

    :return: boolean
    """
    return self.allowed and not self.forced

  def loop_priority(self):
    """Returns whether another repetition should be done (forced or unforced).

    If another repetition is required, returns True
    If we have a choice (see function above) and we're greedy, returns True
    Else the function returns False
    :return: boolean
    """
    return self.choice() and not self.lazy or \
      not self.choice() and self.forced

  def reset(self):
    """Sets min and max back to the original amount. Done on encountering the subpattern Begin object.

    :return: self
    """
    self.set_minmax(self.staticmin, self.staticmax)
    return self

class BeginPP ( PatternPiece ):
  """BeginPP is a PatternPiece denoting the beginning of a new subpattern

  :attr Type: inherited type specifying this is a PPType.Begin piece
  :attr tracker: pointer to the RepetitionTracker for this subpattern, shared with its End piece
  """
  def __init__(self, tracker=None):
    """Initialises a new Begin PatternPiece

    :param tracker: pointer to the RepetitionTracker for this subpattern, shared with its End piece
    """
    self.Type = PPType.BEGIN
    self.tracker = tracker

class OrPP ( PatternPiece ):
  
  def __init__(self, tracker=None):
    """Initialises a new Or Begin PatternPiece
    
    :param tracker: pointer to the RepetitionTracker for this subpattern, shared with its End piece
    """
    self.Type = PPType.OR
    self.tracker = tracker

class EndPP ( PatternPiece ):
  """EndPP is a PatternPiece denoting the end of the last started subpattern

  :attr Type: inherited type specifying this is a PPType.End piece
  :attr tracker: pointer to the RepetitionTracker for this subpattern, shared with its Begin piece
  """
  def __init__(self, tracker=None):
    """Initialises a new End PatternPiece

    :param tracker: pointer to the RepetitionTracker for this subpattern, shared with its Begin piece
    """
    self.Type = PPType.END
    self.tracker = tracker


class AsmPP ( PatternPiece ):
  """The Assembly PatternPiece is a piece of the assembly regex with details on matching one assembly instruction

  This class can be heavily extended to do any kind of matching on an assembly instruction.
  It parses the asmregex string and saves it to attributes.
  Matching is done using the match(asmobj) function.
  :attr static std_patterns: a dictionary from 2 char placeholders to precompiled regexes. More to be added
  :attr static std_opcodes: a dictionary from 2-3 char placeholders to a preset list of opcodes.
  :attr invert_opcode: Boolean specifying if the opcode match should be inverted. Default: False
  :attr opcode: list of opcodes allowed when matching an instruction
  :attr args: max-2-element list of object containing a match(string) function (typically a precompiled regex) or None.
  :attr invert_arg: 2-element boolean list, telling whether any regex match should be logically inverted. Default False.
  :attr jmp: whether it should jump to the given address on a conditional jump after matching. Unused so far
  :attr l: the AsmRegex logger
  :attr Type: inherited type specifying this is a PPType.ASM piece
  """

  # ARM extensions based on https://www.cs.princeton.edu/courses/archive/fall19/cos217/reading/ArmInstructionSetOverview.pdf
  # general purpose registers (w0..w30, x0..x30, wsp, sp, wzr, xzr)
  pattern_ARMGPR = r"((?:[xw]\d{1,2})|(?:w?sp)|(?:[xw]zr))"

  std_patterns = {
      #  Referenced reg (i.e. [rax - 0xa] )
      # on word[eax-0x20]: g1->word, g2->eax, g3->-0x20, g4->-, g5->0x20, g6->0x
      'RR' : re.compile('^([dqbw][a-z]{3,4})?\\[([a-z][a-z0-9]{1,2})(([+-])((0x)?[0-9a-f]+))?\\]$'),
      #  Direct register (i.e. rax, ebx, edi, al)
      'DR' : re.compile('^[a-z][a-z0-9]{1,2}$'),
      #  Concrete constant (any) (i.e. 0x400737, 1)
      'CC' : re.compile('^(0x[0-9a-f]{1,8})|([0-9])$'),
      #  (likely to be) Random Constant: 0x10 - 0xfffffffe, but not 0x40xxxx (pointer)
      'RC' : re.compile('(?!^0x[f]{8}$)(?!^0x40[0-9a-f]{4}$)^0x[0-9a-f]{2,8}$'),
      #  (likely to be) Pointer Value: 0x0040xxxx
      'PV' : re.compile('^0x(00)?40[0-9a-f]{4}$'),
      # ARM general purpose registers
      "AG" : re.compile(rf"^{pattern_ARMGPR}$"),
      # ARM general purpose registers, optionally surrounded by square brackets
      "AR" : re.compile(rf"^\[?{pattern_ARMGPR}\]?$"),
      # opening square bracket and register name
      "QR": re.compile(rf"^\[{pattern_ARMGPR}.*$"),
      # register name and closing square bracket
      "RQ": re.compile(rf"^{pattern_ARMGPR}\]$"),
      # register name and OPTIONAL closing square bracket
      "RO": re.compile(rf"^{pattern_ARMGPR}\]?$"),
  }
  std_opcodes = { # Mind that no std opcode is allowed to start with I, as this specifies an inverted opcode match
      'JC' : ['ja', 'jae', 'jb', 'jbe', 'jc', 'je', 'jg', 'jge', 'jl', 'jle', 'jo', 'jp', 'jpe', 'js', 'jz'],
      'JS' : ['je', 'jne', 'jz'],
      'ALU': ['add', 'sub', 'inc', 'dec', 'and', 'or', 'xor', 'not', 'mul', 'imul', 'div', 'idiv'],
      'SS' : ['shl', 'sal', 'shr', 'sar'],
      'RR' : ['rol', 'rcl', 'ror', 'rcr'],
      'FL' : ['stc', 'cls', 'cmc', 'std', 'cld', 'sti', 'cli'],
      'PU' : ['push', 'pusha', 'pushf'],
      'PO' : ['pop', 'popa', 'popf'],
      'PP' : ['push', 'pusha', 'pushf', 'pop', 'popa', 'popf'],
      'MO' : ['mov', 'lea'],
      'ARMBR' : ["b.eq", "b.ne", "b.hs", "b.cs", "b.lo", "b.cc", "b.mi", "b.pl", "b.vs", "b.vc", "b.hi", "b.ls", "b.ge", "b.lt", "b.gt", "b.le", "b.al", "b.nv", "cbnz", "cbz", "tbnz", "tbz", "b", "bl", "blr", "br"],
      "ARMLD" : ["ldr", "ldrb", "ldrsb", "ldrh", "ldrsh", "ldrsw", "ldur", "ldurb", "ldursb", "ldurh", "ldursh", "ldursw","ldp", "ldpsw", "ldnp", "ldar", "ldarb", "ldarh", "ldaxp", "ldaxr", "ldaxrb", "ldaxrh", "ldtr", "ldtrb", "ldtrh", "ldtrsb", "ldtrsh", "ldtrsw", "ldxp", "ldxr", "ldxrb", "ldxrh"],
      "ARMST" : ["str", "strb", "strh","stur", "sturb", "sturh","stp", "stnp", "stlr", "stlrb", "stlrh", "stlxp", "stlxr", "stlxrb", "stlxrh", "sttr", "sttrb", "sttrh", "stxp", "stxr", "stxrb", "stxrh"],
  }
  anylist = ['any']

  # patternstr should be a string as defined, either including or excluding the delimiting <>
  # EVERY PATTERN MUST END WITH A DOT AND POSSIBLE OPTIONS!
  # The function itself splits the dots and executes the
  def __init__(self, patternstr):
    """Initialises a new Asm PatternPiece

    :param patternstr: string consisting out of one assembly regex instruction, with or without delimiting <>.
                       i.e. 'mov,,RR,' or '<any,>'. The last comma is always required for parsing purposes.
    """
    self.opcode = []
    self.invert_opcode = False
    self.args = []
    self.invert_arg = dict()
    self.jmp = False
    self.l = logging.getLogger("AsmRegex")
    self.Type = PPType.ASM
    if patternstr[0] == '<':
      patternstr = patternstr[1:-1]
    split = patternstr.split(',')
    self._parse_op(split[0])
    # handle the options, should always be there (even then empty!)
    self.constraints = self._parse_options(split[len(split)-1])
    split.pop()
    for arg_idx in range(1, len(split)):
      self._parse_arg_append(split[arg_idx])
    
  # @staticmethod
  # def _match_regex(string, regex):
  #   match = regex.match(string)
  #   return match is not None

  def _match_arg(self, index, asmobj) -> Tuple[bool, Optional[re.Match]]:
    match_invert_arg = True if (index in self.invert_arg) and (self.invert_arg[index] == True) else False
    self.l.debug('Matching arg-condition on arg ' + str(index+1))
    self.l.debug(f"Pattern: {str(self.args)} vs ASM: {str(asmobj['args'])}")
    if index >= len(self.args):
      return (False, None)
    if self.args[index] is None:
      return (True, None)
    if index >= len(asmobj['args']):
      return (False, None)
    if asmobj['args'][index] is None:
      return (match_invert_arg, None)
    if hasattr(self.args[index], "match") and callable(getattr(self.args[index], "match")):
      # Python parsed Regex object
      # include the arg invert option
      match: re.Match = self.args[index].match(asmobj['args'][index])
      return (xor(match is not None, match_invert_arg), match)
    else:
      raise NotImplementedError ( "Object has no match function." )


  def match(self, asmobj):
    """Tries to match the assembly object to its known expression

    :param asmobj: asmobj dict as used throughout the code
    :return: True on a match, False if it didn't match
    """
    self.l.debug("Check if '" + asmobj['opcode'] + "' is in " + str(self.opcode) )
    if self.opcode[0] == 'any' and not self.invert_opcode:
      self.l.debug('Anything is possible')
    elif xor(not asmobj['opcode'] in self.opcode, self.invert_opcode):  # Add the match invert possibility using xor
      return False

    match_per_arg_idx: Dict[int, re.Match] = dict()
    for arg_idx, arg in enumerate(self.args):
      if arg is None:
        continue
      match_success, match = self._match_arg(arg_idx, asmobj)
      if not match_success:
        if arg_idx < len(asmobj['args']):
          self.l.debug('Not a match on arg ' + str(arg_idx) + ' "' + str(asmobj['args'][arg_idx]) + '"')
        else:
          self.l.debug('Not a match on arg ' + str(arg_idx) + ', there is no such arg.')
        return False
      else:
        self.l.debug('Match success on ' + asmobj ['args'][arg_idx])
      match_per_arg_idx[arg_idx] = match
    
    # check constraints
    self.l.debug("checking constraints...")
    for constraint in self.constraints:
      # get match object for the constrained arg_idx
      if not constraint.arg_idx in match_per_arg_idx:
        self.l.debug("constrained argument does not provide a match object to compare with.")
        return False
      match: re.Match = match_per_arg_idx[constraint.arg_idx]
      # get contents of constrained capture group
      match_data: str = match.group(constraint.capture_group)

      # store data in / compare data with global constraint state storage
      if constraint.ctype == PatternConstraintType.CONSTRAINT_TYPE_ASSIGN:
        # put match_data into the global constraint state store
        constraint_state_storage.set_state(constraint, match_data)
        self.l.debug(f"Stored constraint state: {str(constraint)} -> {match_data}")
      elif constraint.ctype in [PatternConstraintType.CONSTRAINT_TYPE_CHECK_EQ, PatternConstraintType.CONSTRAINT_TYPE_CHECK_NEQ]:
        stored_data = constraint_state_storage.get_state(constraint)
        if stored_data == match_data and constraint.ctype == PatternConstraintType.CONSTRAINT_TYPE_CHECK_NEQ:
          self.l.debug(f"Constraint state mismatch for {str(constraint)}: {stored_data} == {match_data}")
          self.l.debug(f"No match!")
          return False
        elif stored_data != match_data and constraint.ctype == PatternConstraintType.CONSTRAINT_TYPE_CHECK_EQ:
          self.l.debug(f"Constraint state mismatch for {str(constraint)}: {stored_data} != {match_data}")
          self.l.debug(f"No match!")
          return False
        elif stored_data == match_data and constraint.ctype == PatternConstraintType.CONSTRAINT_TYPE_CHECK_EQ:
          self.l.debug(f"Constraint state match for {str(constraint)}: {stored_data} == {match_data}")
        elif stored_data != match_data and constraint.ctype == PatternConstraintType.CONSTRAINT_TYPE_CHECK_NEQ:
          self.l.debug(f"Constraint state match for {str(constraint)}: {stored_data} != {match_data}")

    return True  # it made it past all checks!

  def _parse_op(self, instrstr):
    """ Reads and parses the opcode placeholder """
    if instrstr[0] == "I":
      self.invert_opcode = True
      instrstr = instrstr[1:]
    #self.opcode = instrstr.split('.')  # just basic, for testing purposes
    self.opcode = [instrstr] # just basic, for testing purposes
    for op in self.opcode:
      if op == 'any':
        self.opcode = self.anylist  # only one obj
      if op in self.std_opcodes:
        self.opcode.remove(op)
        self.opcode += self.std_opcodes[op]
      
  def _parse_options(self, optionstr):
    """ Reads and parses the options placeholder """
    if optionstr == '':
      return []

    constraint_regex = r'{(\d+):(\d+):([*=!])([a-zA-Z0-9_]+)}'
    constraints = []
    for constraint_match in re.finditer(constraint_regex, optionstr):
      constraint = PatternConstraint(
        arg_idx=int(constraint_match.group(1)),
        capture_group=int(constraint_match.group(2)),
        ctype=PatternConstraintType.from_char(constraint_match.group(3)),
        name=constraint_match.group(4)
      )
      self.l.debug(f"parsed constraint {str(constraint)}")
      constraints.append(constraint)

    return constraints

  def _parse_arg_append(self, argstr):
    """Parses the argstr, saving a None or an object with a match().

    :param argstr: string to parse
    :return: self
    """
    if argstr == '':
      self.args.append(None)
      return self
    self.l.debug('argcondition "'+ argstr +'" detected on arg "' + str(argstr) + '" of ' + self.opcode[0])
    if argstr[0:2] in self.std_patterns:
      self.l.debug('It\'s a standard pattern!')
      self.args.append(self.std_patterns[argstr[0:2]])
    elif argstr[0] == "I" and argstr[1:3] in self.std_patterns:
      self.l.debug('It\'s an inverted standard pattern!')
      self.args.append(self.std_patterns[argstr[1:3]])
      self.invert_arg[index] = True
    else:
      self.l.debug('Not a standard pattern: "' + str(argstr) + '"')
      try:
        self.args.append(re.compile( argstr ))
      except Exception:
        self.l.critical( "Only full regexes work right now, undoing condition" )
        self.args.append(None)
    return self




