__author__ = 'jordygennissen'

# global

# local 
# Import Patternpiece, AsmPP, BeginPP, EndPP and the PPType enum 
from asmregex.PatternPiece import * 



class PatternParser ( object ):
  """Static class used to parse an assembly regex pattern into a list of PatternPieces

  Usage: PatternParser.fromString(patternstring)
  patternstring should already be preformatted (i.e. no spaces or newlines, etc.)
  :attr l: the AsmRegex logger
  :attr PatternList: list where the pattern is being created before returning
  :attr repetition_starts: array of characters that indicate the declaration of a repetition
  :attr subsetctr: the next id to give to the newest subpattern
  :attr or_end_stack
  """
  PatternList = list()
  repetition_starts = '*?+{LG'
  subpattern_ends = ')*+?}'
  subsetctr = 0
  patternstring = ''
  l = None
  
  
  def fromString(self, patternstring):
    """Initiates a string parse into an assembly regex

    :param patternstring: the string to be parsed into an assembly regex
    :return: a PatternPiece list, in other words an assembly regex
    """
    self.l = logging.getLogger("AsmRegex")
    self.PatternList = list()
    self.subsetctr = 0
    self.patternstring = self._preprocess_string(patternstring)
    self._parse_string()
    self.l.debug('Pattern parsed')
    for i in range(0,len(self.PatternList)):
      piece = self.PatternList[i]
      self.l.debug('PP #' + str(i) + '\t ' + str(type(piece))
                   + ('' if type(piece) is AsmPP else ' - ' + str(piece.tracker.subno))
                   )
      if type(piece) is not AsmPP and type(piece.tracker) is OrTracker:
        tracker = piece.tracker
        self.l.debug('(begin, middle, end) = (' + str(tracker.begin) + ', ' + str(tracker.middle) +
                     ', ' + str(tracker.end) + ')')
    return self.PatternList

  @staticmethod
  def toString(PatternList = None):
    """Reverts an assembly regex back to their string format, but does so incorrectly. Is very difficult by design.
    
    Broken af and will not work anymore by design
    :param PatternList: list of PatternPieces being an assembly regex.
    :return: a possibly incorrect corresponding assembly regex string
    """
    string = ''
    for piece in PatternList: 
      if piece.Type == PPType.BEGIN or piece.Type == PPType.OR:
        string += '('
      elif piece.Type == PPType.END:
        if not isinstance(piece.tracker, PatternPieceTracker):
          raise RuntimeError('Broken PatternPiece tracker.')
        if isinstance(piece.tracker, OrTracker):
          if PatternList[piece.tracker.middle] == piece:
            string += ')|('
          else:
            string += ')'
        elif isinstance(piece.tracker, RepetitionTracker):
          string += ')L{' if piece.tracker.lazy else ')G{'
          string += str(piece.tracker.min if piece.tracker.min is not None else '') + ',' + \
                    str(piece.tracker.max if piece.tracker.max is not None else '') + '}'
        else:
          print('WTF IS GOING ON!')  # Something clearly goes wrong here
      elif piece.Type == PPType.ASM:
        string += '<' + '.'.join(piece.opcode) + ','
        for i in range(0,2):
          if piece.args[i] is not None:
            string += piece.args[i].pattern
          string += ','
        string += '>'
    return string 

  def _preprocess_string(self, string):
    self.l.debug('String preprocessing')
    string = ''.join(string.split())  # remove whitespace
    string = '' + string + '$'  # finishing character, so forward search doesn't crash
    # add extra brackets: <st>{3,5}|<st>  =>  (<st>{3,5})|<st>
    string = re.sub('(<[^>]+>([*+?]|(\{\d+(,\d+)?\})))\|', '(\\1)|',string)
    # similarly: <st> | <st>{3,5}  =>  <st> | (<st>{3,5})
    string = re.sub('\|(<[^>]+>([*+?]|(\{\d+(,\d+)?\})))', '|(\\1)', string)
    return string

  def _gen_begin_end(self):
    rt = RepetitionTracker(self.subsetctr)
    rt.set_minmax(1,1)  # possibly to be overwritten
    self.subsetctr += 1
    begin = BeginPP(tracker = rt)
    end = EndPP(tracker = rt)
    return begin, end
  
  def _gen_or_pps(self):
    ot = OrTracker()
    begin = OrPP(tracker=ot)
    middle = EndPP(tracker=ot)
    end = EndPP(tracker=ot)
    return begin, middle, end

  def _parse_repetition(self, string, i, tracker):
    self.l.debug('Parsing repetition')
    if string[i] == 'L':
      tracker.set_lazy(True)
      i+=1
    if string[i] == 'G': # greedy
      tracker.set_lazy(False)
      i+=1 
    if string[i] == '?': 
      tracker.set_minmax(0,1)
      return i+1
    if string[i] == '+': 
      tracker.set_minmax(1, None)
      return i+1
    if string[i] == '*': 
      tracker.set_minmax(None, None)
      return i+1
    if string[i] != '{':
      raise SyntaxError( "Error while parsing the AsmRegex repetition! (i = %d)" % i )
    i += 1
    j = i
    while string[j] != ',' and string[j] != '}': j += 1
    if j==i: 
      minimum = None # Unbounded
    else: 
      minimum = int(string[i:j])
    if string[j] == '}': 
      tracker.set_minmax( minimum, minimum )
      return j+1
    j += 1
    i = j
    while string[j] != '}': j +=1
    if i==j: 
      maximum = None # Unbounded
    else: 
      maximum = int(string[i:j])
    tracker.set_minmax( minimum, maximum )
    return j+1

  def _parse_AsmPP(self, string, i, patternlist):
    self.l.debug('Parsing asm')
    j = i+1
    while string[j] != '>': j+=1 # find the end of the piece
    j += 1
    piece = AsmPP(string[i:j])
     
    if string[j] in self.repetition_starts: 
      # The next one is a repetition, so add hidden brackets
      begin, end = self._gen_begin_end()
      patternlist.append(begin)
      patternlist.append(piece)
      j = self._parse_repetition(string, j, end.tracker)
      patternlist.append(end)
    else:
      patternlist.append( piece )
    return j
  
  def _parse_alternative_or(self, string, j ):
    if string[j] == '(':
      pattern, j = self._parse_subpattern(string, j + 1)
      assert (string[j] == ')')
      j += 1
    else:  # single statement
      pattern = []
      j = self._parse_AsmPP(string, j, pattern)  # already parses single repetition
    return pattern, j
    
  def _parse_brackets(self, string, i):
    pattern = []
    subpattern, j = self._parse_subpattern(string, i + 1)
    if string[j] != '|':  # not a direct 'or'
      pattern = subpattern
      return pattern, j
    else:  # OR statement
      begin, middle, end = self._gen_or_pps()
      pattern.append(begin)
      pattern.extend(subpattern)
      pattern.append(middle)
      subpattern, j = self._parse_alternative_or(string, j + 1)
      pattern.extend(subpattern)
      pattern.append(end)
    return pattern, j
    
  def _parse_subpattern(self, string, i):
    """Recursive function parsing the string into a list of PPs, starting at index i and returning the resulting list"""
    self.l.debug('Parsing subpattern ' + str(self.subsetctr))
    subpattern_begin, subpattern_end = self._gen_begin_end()
    pattern = [subpattern_begin]
    j = i  # start with a defined j
    while True:
      if string[i] == ')':
        if string[i+1] in self.repetition_starts:  # parse the repetition inside: it's still part of the subpattern
          j = self._parse_repetition(string, i+1, pattern[0].tracker)
        else:
          j = i + 1
        self.l.debug('Ending subpattern')
        pattern.append(subpattern_end)
        return pattern, j
      
      elif string[i] == '$':
        pattern.append(subpattern_end)
        return pattern, i
      
      elif string[i] == '<':
        j = self._parse_AsmPP(string, i, pattern)  # already parses single repetition
        
      elif string[i] == '(':
        subpattern, j = self._parse_brackets(string, i)
        pattern.extend(subpattern)
          
      elif string[i] == '|':
        j = i
        begin, middle, end = self._gen_or_pps()
        #  if the asm had repetition, extra brackets have been added during prepocessing
        #  if it was a subpattern of multiple asms or had brackets^, it's not processed here.
        asm_piece = pattern.pop()
        pattern.append(begin)
        pattern.append(asm_piece)
        pattern.append(middle)
        subpattern, j = self._parse_alternative_or(string, j + 1)
        pattern.extend(subpattern)
        pattern.append(end)
      if i == j:
        raise SyntaxError ('RegexError: Cannot match next character: "' + string[i] + '"')
      else:
        i = j  # end of the loop
  
  def _update_or_tracker(self, tracker, i):
    if tracker.begin is None:
      tracker.set_param(begin = i)
      return True
    if tracker.middle is None:
      tracker.set_param(middle = i)
      return True
    if tracker.end is None:
      tracker.set_param(end = i)
      return True
    return False
  
  def _update_repetition_tracker(self, tracker, i):
    if tracker.begin is None:
      tracker.set_param(begin = i)
      return True
    if tracker.end is None:
      tracker.set_param(end = i)
      return True
    return False
  
  def _retrieve_indices(self):
    tracker = None
    check = True
    for i in range(len(self.PatternList)):
      if type(self.PatternList[i]) is AsmPP:
        continue
      tracker = self.PatternList[i].tracker
      if type(tracker) is OrTracker:
        check = check and self._update_or_tracker(tracker, i)
      else:
        check = check and self._update_repetition_tracker(tracker, i)
    return check
    
      

  def _parse_string(self):
    """Parses a given asmregex string, saving the results in self.PatternList.

    After parsing the string, indices that would have been given would not be valid by design.
    Hence, _retrieve_indices() is used afterwards to give matching pointers to all the trackers.
    :return: None
    """
    string = self.patternstring
    pattern, i = self._parse_subpattern(string, 0)
    assert(string[i] == '$')
    self.PatternList = pattern
    if not self._retrieve_indices():
      self.l.warning('Indices retrieval failed!')
    
    return

