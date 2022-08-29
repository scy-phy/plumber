__author__ = 'jordygennissen'

# global
import copy
import logging  # Is used, even if pycharm says it is not
import sys
try:
  import angr  # for testing purposes, because loadBinaries gets an angr Project to pass on to the loader.
  import asmregex.BinaryLoaderAngr as BinaryLoader
except ImportError as e:
  try:
    import r2pipe
    import asmregex.BinaryLoaderRadare as BinaryLoader
  except ImportError as e:
    raise RuntimeError('No angr no R2Pipe found. Can\'t load assembly code')



# local
from asmregex.PatternPiece import *
import asmregex.PatternParser as PatternParser

class AssemblyMatcher ( object ) : 
  """Main class for matching assembly regexes
  
  :attr patterns: dict of asmregex patterns.
        Needs as least one pattern on 'main'. Secondary patterns currently unimplemented.
  :attr asms: list of a list of assembly objects, the haystacks
  :attr address_maps: a list of mappings from the assembly offset/address to the index in the asmlist
  :attr l: AsmRegex logger
  """

  def __init__(self):
    """Initialises an AssemblyMatcher Object """
    self.patterns = dict()
    self.asms = []
    self.address_maps = []
    self.l = logging.getLogger("AsmRegex")
    # handler = logging.StreamHandler()
    # formatter = logging.Formatter(
    #       '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    #   formatter = logging.Formatter(
    #         '%(levelname)-8s %(message)s')
    # handler.setFormatter(formatter)
    # self.l.addHandler(handler)
    self.l.setLevel(logging.WARNING)

  def loadPatternFromFile(self, filename):
    """
    Loads a set of one or more patterns from a file, preprocesses it and sends it to the parser
    
    :param filename: directory including filename, containing asmregex patterns
    :return: self
    """
    tempstr = ''
    pattern_name = ''
    with open(filename, "r") as patternfile:
      for line in patternfile:
        line = ''.join(line.split())  # I believe this removed the ending newlines?
        # remove all comments, but allow escaped \#
        char_idx = 0
        while char_idx < len(line):
          if line[char_idx] == '#':
            if char_idx - 1 >= 0 and line[char_idx-1] == '\\':
              line = line[:char_idx-1] + line[char_idx:]
            else:
              line = line[:char_idx]
              break
          char_idx += 1
        if not line:
          continue
        if line[0] == '[':  # new pattern
          if not pattern_name == '':   # not the first one, save the old pattern we have buffered
            self.loadPattern(tempstr, pattern=pattern_name)
          pattern_name = line.replace('[','').replace(']','')
          tempstr = ''
        else:  # append
          tempstr += line
    self.loadPattern(tempstr, pattern=pattern_name)  # add the last one
    return self

  def loadPattern(self, patternstring, pattern = 'main'):
    """Loads a single assembly regex patternstring and parses it.
    
    :param patternstring: assembly regex string to be used
    :param pattern: the name of the pattern (only main pattern implemented thus far).
    :return: self
    """
    self.l.debug('Loading pattern "' + pattern + '"')
    self.l.debug('P: ' + patternstring)
    stripped = ''.join(patternstring.split()) # remove whitespace
    self.patterns[pattern] = PatternParser.PatternParser().fromString(stripped)
    self.l.debug("Pattern loaded")
    return self

  def loadBinary(self, binary):
    """Loads a single binary and retrieves the assembly code
    Uses the old BinaryLoader based on radare2
    
    :param binary: path to the binary to be loaded
    :return: self
    """
    return self.loadBinaries(bindir=binary)
 
  def loadBinaries(self, angrproject=None, bindir=None, includes=list()):
    loader = BinaryLoader.BinaryLoader(angrproject=angrproject, bindir=bindir, includes=includes)
    asms, mappings = loader.get_all()
    self.l.debug('%d patterns loaded' %len(asms))
    self.asms.extend(asms)
    self.address_maps.extend(mappings)
    return self
  
  def replace_fcn(self, pattern="main", ):
    #  TODO: Decide if I want to implement/use this anyway, and if so, decide if it goes here or within the matcher
    #  TODO: The idea was to have placeholders for a function name, jit converted to the address of the function
    pass
    

  def match(self, pattern="main", assembly_id = 0):
    """Does a standard match of the main pattern on the assembly code of the loaded binary and prints the matches
    
    :return: list of matches (assembly object lists)
    """
    asm = self.asms[assembly_id]
    address_map = self.address_maps[assembly_id]
    if len(asm) == 0:
      raise RuntimeError( "No binary loaded!")
    if len(address_map) == 0:
      raise RuntimeWarning( "No address map found!")
    if len(self.patterns) == 0: 
      raise RuntimeError( "No expressions loaded!")
    matches = self.find_matches(pattern=pattern, assembly_id=assembly_id)
    print('-'*20)
    print('Found %d matches' % len(matches))
    for match in matches:
      print('-'*20)
      print('Next match: ') 
      print('Index start = %d' % address_map[match[0]['addr']])
      print('Index endi  = %d' % address_map[match[-1]['addr']])
      print('Match length = %d' % len(match))
      print('-'*20)
      self.print_asm(match)
    return matches

  @staticmethod
  def print_asm(asmlist):
    """ Prettyprints an assembly object list """
    for asm in asmlist: 
      sys.stdout.write('0x%08x\t' % asm['addr'])
      sys.stdout.write(asm['disasm'] + '\n')
  
  def match_all_binaries(self, pattern="main"):
    """
    Matches the given pattern on *all* binaries given (including libs) and returns one big list
    :param pattern: name of the loaded pattern to use for matching
    :return: one big list of all the matches
    """
    matches = list()
    for i in range(0, len(self.asms)):
      matches.extend(self.find_matches(pattern=pattern, assembly_id=i))
    return matches
    

  def find_matches(self, pattern="main", assembly_id = 0):
    """
    Matches the given loaded assembly code with the given pattern and returns all matches
    
    :param pattern: The name of the loaded pattern to use for matching
    :param assembly_id: which loaded binary to match on. Typically 0 is main binary, 0< is for libs etc.
    :return: list of matches (match == list of assembly instructions)
    """
    assert(pattern in self.patterns)
    matcher = AssemblyMatcherIterator(self.patterns[pattern],
        asm_list = self.asms[assembly_id], address_map = self.address_maps[assembly_id])
    self.l.debug("Matcher created. ")
    return matcher.match_all()



class AssemblyMatcherIterator ( object ) :
  """Class to match an assembly regex to a list of assembly objects
  
  :attr l: AsmRegex logger
  :attr pattern: assembly regex
  :attr asm: list of assemply objects
  :attr amap: a mapping from the assembly offset/address to the index in the asmlist, used for e.g. jumps
  :attr pptr: "pattern pointer" to the current location in the pattern to be matched
  :attr asmptr: "asm pointer" to the current location in the assembly list to be matched
  :attr unexplored: list of states that have been stored for later matching due to a choice in matching (repetition)
        i.e. when using '?', you can either match one or continue without matching, the other gets stored here.
  :attr startptr: pointer to the first assembly object where matching started
  :attr tracker_stack: list/stack of Begin/End trackers while matching
  :attr asmatch: list of the current assembly object being matched
  :attr matches: list of succesful matches
  """

  def __init__(self, patternList, asm_list = None, address_map = None):
    """Initialises an AssemblyMatcherIterator (more than just the iterator in the end due to design decisions)
    
    :param patternList: parsed assembly pattern
    :param asm_list: haystack, list of assembly objects to match as used throughout this code
    :param address_map: a mapping from the assembly offset/address to the index in the asmlist
    """
    self.l = logging.getLogger("AsmRegex")
    self.pattern = patternList 
    self.asm = asm_list
    self.amap = address_map
    self.pptr = 0
    self.asmptr = 0
    self.unexplored = [] 
    self.startptr = 0 
    self.tracker_stack = []
    self.asmatch = []
    self.matches = []

  def _print_trackerstack(self, trackerstack):
    stacks = str(trackerstack[0].subno)
    for i in range(1, len(trackerstack)):
      stacks += ', ' + str(trackerstack[i].subno)
    self.l.debug('Tracker stack ids: ' + stacks)
    self.l.debug('Tracker stack size: ' + str(len(trackerstack)))

    
  def _print_unexplored(self):
    # PRINTS DEBUG INFO
    for j in range(0, len(self.unexplored)):
      self.l.debug('On unexplored ' + str(j))
      self._print_trackerstack(self.unexplored[j]['tracker_stack'])


  def _copy_trackerstack(self):
    """ didn't work properly before, so keeping this code just in case for now
    tracker_stack_copy = list()
    for tracker in self.tracker_stack:
      tracker_copy = copy.deepcopy(tracker)
      tracker_stack_copy.append(tracker_copy)
      self.l.info('Copying tracker: ' + str(tracker.subno))
    self.l.debug(str(len(tracker_stack_copy)) + ' trackers copied ')
    """
    return copy.deepcopy(self.tracker_stack)

  def _save_unexplored_state(self, tracker, start=False):
    """Saves the unprioritised state, taking into account laziness of the subpattern
    
    :param tracker: tracker of the subpattern that gave the choice
    :param start: boolean telling whether this is at the beginning of the first match (on minimum repetition 0, like *?)
    :return: None
    """
    state = dict() 
    state['startptr'] = self.startptr
    state['asmptr'] = self.asmptr
    tracker_stack_copy = self._copy_trackerstack()
    state['tracker_stack'] = tracker_stack_copy
    state['asmatch'] = copy.copy(self.asmatch)  # No deepcopy needed as these are immutable
    state['pptr'] = tracker.get_alternative_pptr() + 1  # +1 is because normally it gets updated after this next_match
    if type(tracker) is RepetitionTracker and tracker.loop_priority():
      # is greedy repetition , so save the lazy one for later
      state['tracker_stack'].pop()  # remove the loop
    elif not start:
      state['tracker_stack'][-1].update()  # update the tracker, we did a full iteration
    self.unexplored.append(state)
    self.l.debug('From _save_state (end):')
    self._print_unexplored()

  def _pop_unexplored_state(self):
    """Retrieves the saved, unexplored state as the own state to explore
    
    :return: None
    """
    self.l.debug('From pop_state (begin):')
    self._print_unexplored()
    state = self.unexplored.pop() 
    self.startptr = state['startptr']
    self.asmptr = state['asmptr']
    # mind that the objects don't align with 'end' anymore!
    self.tracker_stack = state['tracker_stack'] 
    self.asmatch = state['asmatch']
    self.pptr = state['pptr']
    self.l.debug('Popped to ' + str(self.pptr))
    
    return 

  def _check_begin(self):
    """Gets executed at a "Begin" PatternPiece, handles what needs to be done (e.g. checking for skips on repeat=*)
    
    :return: None
    """
    tracker = self.pattern[self.pptr].tracker.reset()
    assert(type(tracker) is RepetitionTracker)
    self.tracker_stack.append(tracker)
    # check if no-repeat is allowed first 
    # Maybe need to check if allowed, but {0,0} repeat doesn't make sense
    if not tracker.forced: 
      # Save the looping state and take the preferred one
      self._save_unexplored_state(tracker, start=True)
      if tracker.is_lazy:  # greedy one is saved, jump towards after the match
        self.l.debug('Lazy skip jump')
        self.pptr = tracker.end
        self.tracker_stack.pop()  # remove the tracker on a jump as we're not looping this one anymore
        
  def _check_or(self):
    """Gets executed at an "Or" PatternPiece, saving the alternative or and saving the tracker"""
    tracker = self.pattern[self.pptr].tracker.reset()
    assert(type(tracker) is OrTracker)
    self.tracker_stack.append(tracker)
    self._save_unexplored_state(tracker, start=True)

  def _check_end(self):
    """Gets executed at an "End" PatternPiece, handles what needs to be done (e.g. check for repetitions)
    
    :return: None
    """
    if len(self.tracker_stack) == 0:
      raise RuntimeError('End PatternPiece detected on an empty tracker stack.')
    tracker = self.tracker_stack[-1]
    if type(tracker) is OrTracker:
      self.pptr = tracker.get_preferred_pptr()
      self.tracker_stack.pop()
    elif type(tracker) is RepetitionTracker:
      tracker.update() # we're at the end so did one full match
      if tracker.choice(): # save
        self.l.debug('Potential end of tracker #' + str(tracker.subno))
        self._save_unexplored_state(tracker)
      else:
        self.l.debug('No choice on tracker #' + str(tracker.subno))
      self.pptr = tracker.get_preferred_pptr()
      if not tracker.loop_priority():
        self.tracker_stack.pop()
    else:
      raise RuntimeError("Unknown tracker type: " + str(type(tracker)))

  def _asm_jmp(self, addr):
    """Changes the assembly pointer to the index where the assembly instruction has address param 'addr'
    
    :param addr: the address of the assembly instruction to jump to
    :return: True on jump success, False on error (i.e. if address not concrete or not matched)
    """
    self.l.debug('Jumping through the asm, wheeee') 
    if (addr == '0' or addr.startswith('0x') ) and int(addr,16) in self.amap:
      self.asmptr = self.amap[int(addr,16)]
      return True
    else:
      self.l.debug('Cannot jump to an unknown address: ' + addr)
      return False 

  def _move_asmptr(self):
    """Checks if a jump in the asmptr is expected and jumps if so
    
    :return: True on a jump, False otherwise
    """
    asm = self.asm[self.asmptr]
    if asm['opcode'][0] not in 'jcr': # jump* call ret 
      self.asmptr += 1
      return False 
    #  if asm['opcode'] == 'jmp': # unconditional, dont automatically jump, only when specified
    #  return self._asm_jmp(asm['args'][0])
    if asm['opcode'][0] == 'j' and self.pattern[self.pptr].jmp:
      # conditional jump
      return self._asm_jmp(asm['args'][0])
    # TODO: Add if call / return + stack 
    self.asmptr += 1 
    return False

  def _match_asm(self):
    """Matches an assembly object to the current assembly pattern piece
    
    :return: boolean whether match succeeded
    """
    if len(self.asm) <= self.asmptr:
      return False
    asmPiece = self.pattern[self.pptr]
    assert(type(asmPiece) is AsmPP)
    match = asmPiece.match(self.asm[self.asmptr]) 
    if match: 
      self.asmatch.append(self.asm[self.asmptr])
    self._move_asmptr()
    return match

  def _match_next(self):
    """Matches the next item in the pattern.
    
    :return: True on match, False on a non-match
    """
    self.l.debug("Next Match on " + str(self.pptr) + \
        " -> " + str(self.pattern[self.pptr].Type))
    if self.pattern[self.pptr].Type == PPType.BEGIN:
      self._check_begin() 
      return True 
    if self.pattern[self.pptr].Type == PPType.END: 
      self._check_end() # forced but not allowed
      return True
    if self.pattern[self.pptr].Type == PPType.OR:
      self._check_or()
      return True
    if self.pattern[self.pptr].Type == PPType.ASM: 
      return self._match_asm()
    raise RuntimeError( "UPP Detected: Unidentified Pattern Piece: " \
      + str(self.pattern[self.pptr].Type) )
      
  # Tries to match the pattern against the assembly code with a given state
  def match_from_state(self):
    """Tries to match the pattern with the assembly objects, given the current state
    
    This function does not change the stack, any pointers or whatsoever.
    It just naively starts matching given the current state of the object.
    :return: True on a complete match, False otherwise
    """
    failed = False 
    while not failed and self.pptr != len(self.pattern): 
      if not self._match_next():
        self.l.debug("Matching failed.") 
        failed = True  # no match
      self.pptr += 1
    return self.pptr == len(self.pattern)
      
  def match_from_start(self, max=1):
    """Tries to match anything, given that the match in assembly should start at self.startptr
    
    By default, stops matching after it found a single one (to avoid obvious duplicates)
    :param max: maximum amount of matches before it stops matching (set None for "match all")
    :return: the amount of matches it still needed to match, or None if max=None.
    """
    new_state = True # A sort of do-while emulation
    while (max is None or max > 0) and new_state:
      self.l.debug("Matching new unexplored state.") 
      new_state = False 
      is_match = self.match_from_state() 
      if is_match:
        if max is not None: max = max - 1
        self.l.debug(
          "Match found! " + (str(max) if max is not None else "all") + " matches to go on start "+ str(self.startptr)
        )
        self.matches.append(copy.copy(self.asmatch))
      if len(self.unexplored) > 0: 
        self._pop_unexplored_state()
        new_state = True 
    # After the while loop
    return max
  
  def reset_state(self):
    """Resets the current state of the matching process, EXCEPT the start pointer
    
    This function is specifically used when changing the start pointer
        and starting from there with a fresh start.
    :return: None
    """
    self.pptr = 0
    self.asmptr = self.startptr
    self.unexplored = [] 
    self.tracker_stack = []
    self.asmatch = [] 
 
  def match_all(self):
    """Returns all matches it could find.
    
    Max 1 match per start pointer.
    On a match the start pointer jumps to the point right after the last element of the match
    This is a terrible idea if you're matching unconditional jumps (where the jump is taken within pattern matching)
    Or any kind of jump / call / ret once this is implemented.
    Just an FYI
    :return: List of all the matches
    """
    self.l.debug("Match all on regex of size " + str(len(self.pattern))) 
    if not self.asm or not self.pattern: 
      raise RuntimeError( "I don't have both an asmregex and a binary yet!" )
    start = 0 # need to be able to jump the loop
    while start < len(self.asm):
      self.l.debug('Matching next start pointer: ' + str(start) + ' @ ' + '0x%08x\t' % self.asm[start]['addr'] )
      self.startptr = start 
      self.reset_state()
      failed = self.match_from_start() # max 1 per starting point
      if failed is not None and not failed and len(self.matches[-1])>0:
        # TODO: might want to check for jumps taken or sth here
        start = self.amap[self.matches[-1][-1]['addr']] 
        self.l.debug('Matched so jumping to ' + str(start))
      start +=1
    return self.matches 
      

