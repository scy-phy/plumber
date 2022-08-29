import functools
import numpy as np
import sys


class AsmEqualityIterator(list):
  """
  Iterator class returning various functions (AssemblyInstruction, AssemblyInstruction) => Bool
  on whether the two instructions are equal(/similar) from a certain perspective.
  Used to do various checks in an incremental fashion.
  """
  TYPE            = 0  # True iff object types are equal, so basically a mere sanity check
  COURSE_OPCODE   = 1  # True iff opcodes reside in a mutual class
  FINE_OPCODE     = 2  # True iff substring 1:3 of opcode are equal
  EXACT_OPCODE    = 3  # True iff the opcodes are equal
  OP_SIMARG       = 4  # True iff opcodes equal and arguments similar
  STRICT          = 5  # True iff the opcode and arguments are equal
  EXACT           = 6  # True iff the addresses are equal
  NEVER           = 7  # False
  AMOUNT_OF_FUNCTIONS = 8
  
  MATCH_MODES = {
    0 : ['TYPE'],
    1 : ['TYPE', 'COURSE_OPCODE'],
    2 : ['TYPE', 'FINE_OPCODE'],
    3 : ['TYPE', 'EXACT_OPCODE'],
    4 : ['TYPE', 'EXACT_OPCODE', 'ALL_REG_SIM'],
    5 : ['TYPE', 'EXACT_OPCODE', 'ALL_REG'],
    6 : ['TYPE', 'EXACT_OPCODE', 'ALL_REG', 'ADDR'],
    7 : ['NEVER'],
    8 : ['ALWAYS', 'TYPE', 'COURSE_OPCODE', 'FINE_OPCODE', 'EXACT_OPCODE', 'ONE_REG_SIM', 'ALL_REG_SIM',
         'ONE_REG', 'ALL_REG', 'ADDR', 'NEVER']
  }

  def __init__(self, strength=None):
    """
    Initialises the iterator.
    :param max_strength: The max strength the iterator should be used for to check for equality.
    """
    super().__init__()
    self.weights = list()
    self.names = list()
    self.funs = list()
    self.strength = AsmEqualityIterator.STRICT if strength is None else strength
    self.set_mode(self.strength)
    self._register_std_match_functions()
  
  def __iter__(self):
    self.n = 0
    self.set_funs_to_self()
    return self
  
  def __next__(self):
    self.n += 1
    if self.n <= len(self):
      return self[self.n - 1]
    raise StopIteration

  def _register_match_function(self, name, weight, fun):
    self.names.append(name)
    self.weights.append(weight)
    self.funs.append(fun)
    return

  def match_modes(self, modelist, asm1, asm2):
    for name in modelist:
      index = self.names.index(name)
      if not self.funs[index](asm1, asm2):
        return False
    return True

  def set_mode(self, mode):
    if type(mode) is int and 0 <= mode < len(AsmEqualityIterator.MATCH_MODES):
      self.match_list = AsmEqualityIterator.MATCH_MODES[self.strength]
    elif type(mode) is list:
      self.match_list = mode
    else:
      raise RuntimeWarning('Set mode requires either a number within range or a list, not ' +
                           str(mode) + '(%s)' % str(type(mode)))

  def _register_std_match_functions(self):
    self._register_match_function("NEVER", np.infty, lambda x, y: False)
    self._register_match_function("ALWAYS", 0, lambda x, y: True)
    self._register_match_function("TYPE", 1, AsmEqualityIterator.type_eq)
  
    self._register_match_function("COURSE_OPCODE", 2, AsmEqualityIterator.course_opcode_eq)
    self._register_match_function("FINE_OPCODE", 3, AsmEqualityIterator.course_opcode_eq)
    self._register_match_function("EXACT_OPCODE", 5, AsmEqualityIterator.exact_opcode_eq)
  
    self._register_match_function("ANY_REG_SIM", 2, AsmEqualityIterator.one_reg_similar)
    self._register_match_function("ALL_REG_SIM", 4, AsmEqualityIterator.all_reg_similar)
    self._register_match_function("ANY_REG", 4, AsmEqualityIterator.one_reg_eq)
    self._register_match_function("ALL_REG", 7, AsmEqualityIterator.all_reg_eq)
  
    self._register_match_function("ADDR", 10, AsmEqualityIterator.addr_eq)
    return

  @property
  def weight(self):
    w = 0
    for name in self.match_list:
      w += self.weights[self.names.index(name)]
    return w

  def set_funs_to_self(self):
    del self[:]
    for name in self.match_list:
      index = self.names.index(name)
      self.append(self.funs[index])
    return

  @staticmethod
  def type_eq(obj1, obj2):
    return type(obj1) == type(obj2)

  @staticmethod
  def one_reg_eq(asm1, asm2):
    for i in range(min(len(asm1['args']), len(asm2['args']))):
      if asm1['args'][i] == asm2['args'][i]:
        return True
    return False
  
  @staticmethod
  def one_reg_similar(asm1, asm2):
    from .PatternPiece import AsmPP
    for i in range(min(len(asm1['args']), len(asm2['args']))):
      for index in AsmPP.std_patterns:
        regex = AsmPP.std_patterns[index]
        if regex.match(asm1['args'][i]) and regex.match(asm2['args'][i]):
          return True
    return False
  
  @staticmethod
  def all_reg_similar(asm1, asm2):
    from .PatternPiece import AsmPP
    check = False
    for i in range(min(len(asm1['args']), len(asm2['args']))):
      for index in AsmPP.std_patterns:
        regex = AsmPP.std_patterns[index]
        if regex.match(asm1['args'][i]) and regex.match(asm2['args'][i]):
          check = True
          break
      if not check:
        return False
      check = False
    return True

  @staticmethod
  def course_opcode_eq(asm1, asm2):
    if AsmEqualityIterator.exact_opcode_eq(asm1, asm2):
      return True  # for any opcodes that don't appear in our groupings
    from .PatternPiece import AsmPP
    for key in AsmPP.std_opcodes:  # TODO: Extend std_opcodes
      if asm1['opcode'] in AsmPP.std_opcodes[key] and asm2['opcode'] in AsmPP.std_opcodes[key]:
        return True
    return False
  
  @staticmethod
  def fine_opcode_eq(asm1, asm2):
    """ Checks whether characters 1:3 are equal
    i.e. div & idiv, pop & popa, push & pushf"""
    return asm1['opcode'][1:3] == asm2['opcode'][1:3]
    # raise NotImplementedError  # TODO
  
  @staticmethod
  def exact_opcode_eq(asm1, asm2):
    """Comparison on 2 asm object, returns whether the opcodes are equal / similar """
    return asm1['opcode'] == asm2['opcode']
  
  @staticmethod
  def all_reg_eq(asm1, asm2):
    """Comparison of 2 asm objects, doing additional strict checks on the instructions """
    if len(asm1['args']) != len(asm2['args']):
      return False
    for i in range(len(asm1['args'])):
      if asm1['args'][i] != asm2['args'][i]:
        return False
    return True
  
  @staticmethod
  def addr_eq(asm1, asm2):
    return asm1['addr'] == asm2['addr']



class AssemblyInstruction(object):
  """AssemblyInstruction is one piece of assembly as an object

  :static attr MatchStrength: Defines the way comparison will be done.
  :attr _dict: private dictionary containing the address, opcode and arguments
  """
  MatchStrength = AsmEqualityIterator.STRICT
  
  def __init__(self):
    self._dict = {
      'addr': -1,
      'disasm': '',
      'opcode': '',
      'args': list()
    }
    
  def _get_disasm_str(self):
    str_repr = self['opcode']
    if len(self['args']) > 0:
      str_repr += ' %s' % self['args'][0]
    for i in range(1, len(self['args'])):
      str_repr += ', %s' % self['args'][i]
    return str_repr
  
  def __str__(self):
    """Prettyprint string representation of an assembly instruction """
    return "0x%08x\t" % self['addr'] + self._get_disasm_str()
      
  
  def __repr__(self):
    """Informative concise representation of the object"""
    return '<asm obj (%s) @ 0x%x>' % (self['opcode'], self['addr'])
  
  def __getitem__(self, key):
    if key == 'disasm':
      return self._get_disasm_str()
    if key in self._dict:
      return self._dict[key]
    raise KeyError('Unknown property of an assembly instr: %s' % key)
  
  def __setitem__(self, key, value):
    if key == 'disasm':
      raise PermissionError('Cannot change the disasm value!')
    if key in self._dict:
      self._dict[key] = value
    else:
      raise KeyError('Unknown property of an assembly instr: %s ' % key)
    return
  
  def __eq__(self, other):
    """ Equality override, comparing 2 asm instructions using the Iterator.
    Strength of the iterator is decided by the static variable AssemblyInstruction.MatchStrength.
    :param other: The second AssemblyInstruction
    :return: boolean, True iff comparison succeeds until and including the given strength.
    """
    equality_iterator = AsmEqualityIterator(AssemblyInstruction.MatchStrength)
    for equality_function in equality_iterator:
      if not equality_function(self, other):
        return False
    return True
  
  def __ne__(self, other):
    result = self.__eq__(other)
    if not type(result) is bool:  # because the not operator will crash on a NotImplemented object
      return result
    return not result
  
  def __gt__(self, other):
    return self.__ne__(other)
  
  def __lt__(self, other):
    return self.__ne__(other)
  
  def equality_estimator(self, other):
    score = 0
    AsmEq = AsmEqualityIterator()
    for index in range(len(AsmEq.funs)):
      if AsmEq.funs[index](self, other):
        score += AsmEq.weights[index]
    return score

  def equality_types(self, other):
    string = ''
    AsmEq = AsmEqualityIterator()
    for index in range(len(AsmEq.funs)):
      if AsmEq.funs[index](self, other):
        string = AsmEq.names[index] if string == '' else string + ',' + AsmEq.names[index]
    return string

class AssemblyList(list):
  
  def __init__(self, listlike_obj=list()):
    super().__init__()
    for item in listlike_obj:
      self.append(item)
      
  def __lt__(self, other):
    return len(self) < len(other)
  
  def __gt__(self, other):
    return len(self) > len(other)
  
  def __str__(self):
    string = ''
    for asm in self:
      string += str(asm) + "\n"
    return string
  
  def __repr__(self):
    return '<AsmList of size %d>' % len(self)
  
  def __getitem__(self, key):
    if isinstance(key, slice):
      start = 0 if key.start is None else key.start
      stop = len(self) if key.stop is None else key.stop
      step = key.step
      if step is None:
        step = 1 if start < stop else -1
      #print('My size: ' + str(len(self)) + ", on range (%d, %d, %d)" % (start, stop, step), file=sys.stderr)
      return AssemblyList([self[i] for i in range(start, stop, step)])
    else:
      return super().__getitem__(key)
  
  def _lcs_table_entry(self, other, table, sindex, oindex):
    if self[sindex - 1] == other[
      oindex - 1]:  # mind that the offsets are one-off because of the null-rows at the beginning
      return table[sindex - 1][oindex - 1] + 1
    return max(table[sindex - 1][oindex], table[sindex][oindex - 1])
  
  def _generate_lcs_table(self, other):
    ssize = len(self)
    osize = len(other)
    table = np.zeros((ssize + 1, osize + 1))
    for sindex in range(1, ssize + 1):
      for oindex in range(1, osize + 1):
        table[sindex][oindex] = self._lcs_table_entry(other, table, sindex, oindex)
    return table
  
  def _get_all_lcs(self, table, maxval, currlist=list()):
    raise NotImplementedError('This is impossible by design unless diagonals have been tracked, and this is '
                              'not implemented.')
  
  def _get_an_lcs_traceback(self, table, maxval):
    assert (type(maxval) is tuple)
    results = list()
    sindex = maxval[0]
    oindex = maxval[1]
    val = table[sindex][oindex]
    if val == 0: return results  # not a single match
    while val != 0:
      if sindex != 0 and table[sindex - 1][oindex] == val:
        sindex -= 1
      elif oindex != 0 and table[sindex][oindex - 1] == val:
        oindex -= 1
      else:
        results.append((sindex-1, oindex-1, self[sindex - 1]))
        sindex -= 1
        oindex -= 1
        val -= 1
    assert (val == 0)
    results.reverse()  # We backtraced from end to beginning, so need to reverse
    return results
  
  def lcs_traceback(self, other):
    table = self._generate_lcs_table(other)
    return self._get_an_lcs_traceback(table, (len(self), len(other)))
      
  
  @functools.lru_cache(maxsize=None)
  def LCS2(self, other, i, j):
    if i == len(self) or j == len(other):
      return 0
    return (
      1 + self.LCS2(other, i + 1, j + 1)
      if self[i] == other[j] else
      max(self.LCS2(other, i + 1, j), self.LCS2(other, i, j + 1))
    )
    # raise NotImplementedError('Coming soon...')
