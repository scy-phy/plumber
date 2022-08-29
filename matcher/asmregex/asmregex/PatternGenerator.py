from asmregex.Assembly import *
import logging
from copy import deepcopy

GENTABLE_PROPERTIES_INDEX = 0
GENTABLE_ENTRY_OFFSET = 1


class PatternGenerator:
  """
  The process of generating patterns consists out of a certain amount of steps.
  (1) First, we need to be able to match two lists of instructions. This is done
      using the Least Common Subsequence algorithm, recurvisely used with different
      equality operators. This is stored in a table where the longest sequence of
      instructions is always the first entry by design.
      The table consists out of 4 rows. The first row [0] has indices one-to-one
      corresponding to the assembly instructions of the biggest asmlist, and the
      value is:
        - negative if it doesn't match another instruction on the other list, or
        - the index of row[1] / asmlist of the instruction matching.
      The same procedure is followed for row[1], so following non-negative incides
      twice should always give back the original index.
      The last two rows have a one-to-one correspondence with the first two and
      contain all the conditions that hold for the match (i.e. opcode being the
      same).
  (2) Given N lists of instructions, we have to create a table for all pairs.
      Note that table[i][j] == table[j][i].
  (3) Given a table for each pair, we have to generate one general table?  # TODO: TABLE?
    (a)
      We generate a 3-dimensional table, where:
        row "table[i][j]" will be the row in the match table with indices from
        asmlist[i] with pointers to asmlist[j].
      Furthermore, we have a table of pointers, each initially set to 0.
    (b)
      On each iteration, define:
            next_ptr(i,j) = ptr+k,  with k the lowest number such that table[i][j][ptr+k] >= 0.
            next(i,j) := table[i][j][ptr+k],  with k the lowest number such that next >= 0.
        Then, find all tuples (i,j) where the following holds:
            table[j][i][next(i,j)] == next_ptr(i,j)
            forall p,q in indices(table):  # TODO: Check this, might be a thought mistake with all these pointers
              table[p][j][ next_ptr(p,j) ] >= next(i,j)
              table[i][q][ next_ptr(i,q) ] >= next(i,j)
    (c)
      Given all tuples (i,j) that satisfy the condition above,
        we have to check if they are all chained.
        e.g. (0,1), (1,2), (3,2) is chained, but (0,1), (2,3) is not.
        If they are all chained, we can safely solve up until the next matching
        element, being the next element in any of the tuples.
        If instead we have multiple chains, this becomes an issue. We don't know which of
        the matches comes before or after the other half, or maybe it's an or statement instead.
        Afterwards, we update the pointer for each index used in the chain(s).
        TODO: Multiple chains should not just have a logical solution as well as a way of implementing
              this.
    (d)
      Iterating over all the next tuples with the gaps (i.e. the max amount of unmatched
        elements in between) gives us a spacial correct table with all requirements for the elements
        that have been matched before.
  (4) Using this table, we can loop through each index to generate a pattern element given the
      (strongest) matching condition for the group of assembly instructions to be matched in that
      general table entry.
  (5) The output is a string consistent with the asmregex language format. This can be safely loaded
      inside asmregex using the patternparser or the patternmatcher wrapper.
  """
  
  def __init__(self):
    
    self.l = logging.getLogger("PatternGenerator")
    self.l.setLevel(logging.DEBUG)
    
  def _update_match_table(self, table, traceback, offset=(0,0), items=(None, None)):
    for entry in traceback:
      zero_index = entry[0] + offset[0]
      one_index = entry[1] + offset[1]
      match_str = items[0][entry[0]].equality_types(items[1][entry[1]])
      self.l.debug(entry)
      assert(table[0][zero_index] == table[1][one_index] and table[1][one_index] == -1)
      assert (table[2][zero_index] == table[3][one_index] == -1)
      self.l.debug(str(zero_index) + ' -0-> ' + str(one_index) + ' (level: %d)' % AssemblyInstruction.MatchStrength)
      table[0][zero_index] = one_index
      table[2][zero_index] = match_str
      
      table[1][one_index] = zero_index
      table[3][one_index] = match_str
      self.l.debug(str(one_index) + ' -1-> ' + str(zero_index) + ' (level: %d)' % AssemblyInstruction.MatchStrength)
    assert(len([x for x in table[2] if type(x) is int and x<0]) == len([x for x in table[3] if type(x) is int and x<0]))
    return table

  def _recursive_match(self, table, biggest, smallest, strength_needed, offset=(0, 0)):
    self.l.debug('Recursive on %d, offset ' % strength_needed + str(offset))
    self.l.debug('biggest size: %d' % len(biggest))
    self.l.debug('smallest size: %d' % len(smallest))
    if strength_needed == -1 or len(biggest) < 1 or len(smallest) < 1:
      return table
    old_strength = AssemblyInstruction.MatchStrength
    AssemblyInstruction.MatchStrength = strength_needed
    traceback = biggest.lcs_traceback(smallest)
    AssemblyInstruction.MatchStrength = old_strength
    del old_strength
    table = self._update_match_table(table, traceback, offset, (biggest, smallest))
    child_offset = offset
    b_indices = [x[0] for x in traceback]
    self.l.debug('Full bindices: ' + str(b_indices))
    for bindex in b_indices:
      self.l.debug('Recursing with biggest[ %d : %d ] and smallest [ %d : %d ]' % (
        child_offset[0] - offset[0], bindex,
        child_offset[1] - offset[1], table[0][ bindex + offset[0] ] - offset[1],
      ))
      child_biggest = biggest[child_offset[0] - offset[0]: bindex ]
      child_smallest = smallest[child_offset[1] - offset[1] : table[0][ bindex + offset[0] ] - offset[1] ]
      
      self.l.debug('Child offset: ' + str(child_offset))
      table = self._recursive_match(table, child_biggest, child_smallest, strength_needed - 1, child_offset)
      child_offset = (offset[0]+bindex + 1, table[0][bindex+offset[0]] + 1)
      self.l.debug('Child offset updated to ' + str(child_offset))
    if child_offset[0] - offset[0] < len(biggest) and child_offset[1] - offset[1] < len(smallest):
      self.l.debug('Final recursion with biggest[ %d : ] and smallest [ %d :  ]' % (
        child_offset[0] - offset[0],
        child_offset[1] - offset[1],
      ))
      child_biggest = biggest[child_offset[0] - offset[0] : ]  # last part too
      child_smallest = smallest[child_offset[1] - offset[1] : ]
      self.l.debug('Child offset: ' + str(child_offset))
      return self._recursive_match(table, child_biggest, child_smallest, strength_needed-1, child_offset)
    return table
  
  def match_two(self, asmlist1, asmlist2):
    biggest = asmlist1 if len(asmlist1) >= len(asmlist2) else asmlist2
    smallest = asmlist1 if len(asmlist1) < len(asmlist2) else asmlist2
    shape = (4, len(biggest))
    match_table = np.full(shape, -1, dtype=object)  # fill it with -1's
    for i in range(len(smallest), len(biggest)):
      match_table[1][i] = -2
      match_table[3][i] = -2
    match_table = self._recursive_match(match_table, biggest, smallest, AsmEqualityIterator.EXACT_OPCODE)
    return match_table
  
  def _update_table_weights(self, table, asmlist1, asmlist2):
    for index in range(len(table[0])):
      if table[0][index] != -1:  # Match
        l2_index = table[0][index]
        table[2][index] = asmlist2[l2_index].equality_types(asmlist1[index])
        table[3][l2_index] = table[2][index]
    return table
  
  ##### start gentable functions #######
  
  def construct_general_table(self, match_table):
    gen_table = np.full( (3, 2*len(match_table[0])), None, dtype=object)
    self.l.debug('General table has size 2x%d'%(2*len(match_table[0])))
    last_match = (0, 0)
    fm1, fm2, ptr = 0, 0, 0
    valid_indices = [x for x in range(len(match_table[1])) if match_table[1][x] >= 0]
    for fm1 in valid_indices:
        fm2 = match_table[1][fm1]
        for _ in range(max(fm1-last_match[0]-1, fm2-last_match[1]-1)):
          gen_table[GENTABLE_ENTRY_OFFSET][ptr] = -1  # unknowns in between
          gen_table[GENTABLE_ENTRY_OFFSET+1][ptr] = -1  # unknowns in between
          gen_table[GENTABLE_PROPERTIES_INDEX][ptr] = -1  # unknowns in between
          ptr += 1
        gen_table[GENTABLE_ENTRY_OFFSET+1][ptr] = fm1
        self.l.debug('0[' + str(ptr) + '] gets value ' + str(fm2))
        self.l.debug('gentable[1]['+str(ptr)+'] gets value '+str(fm1))
        gen_table[GENTABLE_ENTRY_OFFSET][ptr] = fm2
        gen_table[GENTABLE_PROPERTIES_INDEX][ptr] = match_table[2][fm2]
        ptr += 1
        last_match = (fm1, fm2)
    while fm1 < len(match_table[0]) and fm2 < len(match_table[1]) and (
        match_table[0][fm1] >= -1 or match_table[1][fm2] >= -1
        ):
      gen_table[GENTABLE_ENTRY_OFFSET][ptr] = -1  # unknowns at the end
      gen_table[GENTABLE_ENTRY_OFFSET+1][ptr] = -1  # unknowns at the end
      gen_table[GENTABLE_PROPERTIES_INDEX][ptr] = -1
      fm1 +=1; fm2 +=1; ptr += 1
    return gen_table
  
  def _get_asm_column(self, asmlistlist, i, table):
    # REMINDER TO SELF, DONT DO AGAIN:
    # asmlist = [None if table[rindex][i] < 0 else asmlistlist[rindex][table[rindex][i]]
    #           for rindex in range(len(asmlistlist))]
    asmlist = []
    for rowindex in range(len(asmlistlist)):
      if table[GENTABLE_ENTRY_OFFSET+rowindex][i] is None or \
         table[GENTABLE_ENTRY_OFFSET+rowindex][i] < 0:
        asmobj = None
      else:
        asmindex = table[GENTABLE_ENTRY_OFFSET+rowindex][i]
        self.l.debug('asmlistlist[%d,%d] with size [%d,%d]' %
                     (rowindex, asmindex, len(asmlistlist), len(asmlistlist[rowindex]))
                     )
        self.l.debug('table[%d,%d] = %d' % (GENTABLE_ENTRY_OFFSET+rowindex, i, asmindex))
        asmobj = asmlistlist[rowindex][asmindex]
      asmlist.append(asmobj)
      self.l.debug(str(i) + ':' + str(rowindex) + ' -> ' + str(asmobj))
    return asmlist

  def general_table_to_pattern(self, table, asmlistlist):
    patternstring = ''
    self.l.debug('Should end with %d objects in list' % len(table[0]))
    for i in range(len(table[0])):
      if table[GENTABLE_ENTRY_OFFSET][i] is None:  # we're done here
        return self._postprocess_pattern(patternstring)
      asmlist = self._get_asm_column(asmlistlist, i, table)
      self.l.debug('properties: ' + str(table[GENTABLE_PROPERTIES_INDEX, i]))
      patternstring += self._asm_to_PPstring(table[:, i], asmlist) + '\n'
      continue
    return self._postprocess_pattern(patternstring)
  
  def _asm_to_PPstring(self, table, asmlist):
    asm, PPstring = self._to_PPstring_precheck(table, asmlist)
    if asm is None:
      return PPstring
    properties = table[GENTABLE_PROPERTIES_INDEX].split(',')
    PPstring = '<'
    if 'EXACT_OPCODE' in properties:
      PPstring += asm['opcode'] + ','
    elif 'COURSE_OPCODE' in properties:
      PPstring += self._get_opcode_group(asmlist) + ','
    else:
      PPstring += 'any,'
  
    if 'ALL_REG' in properties:
      PPstring += ','.join(asm['args']) + ','
    elif 'ALL_REG_SIM' in properties:
      PPstring += ','.join(self._get_arg_groups(asmlist, arglen=len(asm['args']))) + ','
    elif 'ANY_REG_SIM' in properties:
      PPstring += ','.join(self._get_arg_groups(asmlist, arglen=len(asm['args']))) + ','
    else:
      PPstring += ','
    PPstring += '>'
    return PPstring
    
  def _to_PPstring_precheck(self, table, asmlist):
    asm = None
    if type(table[GENTABLE_PROPERTIES_INDEX]) is str:
      for item in asmlist:
        if item is not None:
          asm = item
          break
      if asm is None:
        self.l.error('No working asm found! Continuing on any')
    return asm, '<any,>?'
      
  def _get_opcode_group(self, asmlist):
    from .PatternPiece import AsmPP
    for index in AsmPP.std_opcodes:
      if self._match_asm_opgroup(asmlist, AsmPP.std_opcodes[index]):
        return index
    return "ERROR"
    raise IndexError('Has no known opcode-group!')
  
  def _match_asm_opgroup(self, asmlist, opgroup):
    self.l.debug('Matching opgroup')
    for asm in asmlist:
      self.l.debug(asm)
      if asm is not None and asm['opcode'] not in opgroup:
        return False
    return True
    
  def _get_arg_groups(self, asmlist, arglen=0):
    groups = []
    from .PatternPiece import AsmPP
    for argindex in range(arglen):
      for pindex in AsmPP.std_patterns:
        if self._match_asm_argroup(asmlist, AsmPP.std_patterns[pindex], index=len(groups)):
          groups.append(pindex)
          break  # next arg
      if len(groups) == argindex:
        groups.append('')  # make sure alignment goes well
    return groups
  
  def _match_asm_argroup(self, asmlist, argre, index=0):
    for asm in asmlist:
      if asm is not None and len(asm['args']) <= index:
        return False
      if asm is not None and not argre.match(asm['args'][index]):
        return False
    return True
      
  def _postprocess_pattern(self, pattern):
    pattern = pattern.replace('[', '\[')
    pattern = pattern.replace(']', '\]')
    pattern = pattern.replace('+', '\+')
    return pattern
      
  def _set_table_iterator(self, asmlistlist):
    mti = MatchTableIterator()
    for i in range(len(asmlistlist)):
      for j in range(i,len(asmlistlist)):
        biggest  = i if len(asmlistlist[i]) >= len(asmlistlist[j]) else j
        smallest = i if len(asmlistlist[i]) < len(asmlistlist[j]) else j
        table = self.match_two(asmlistlist[biggest], asmlistlist[smallest])
        table = self._update_table_weights(table, asmlistlist[biggest], asmlistlist[smallest])
        mti.add_table(table, biggest, smallest)
    return mti
  
  def build_table(self, asmlistlist):
    clist = list()
    iterator = self._set_table_iterator(asmlistlist)
    for jumpspace, affected_tuples, constraints in iterator:
      for _ in range(jumpspace):
        clist.append("ALWAYS")
      clist.append(constraints)
    return clist

  def generate_pattern(self, asmlistlist):
    patternstring = ''
    iterator = self._set_table_iterator(asmlistlist)
    for jumpspace, affected_tuples, constraints in iterator:
      for _ in range(jumpspace):
        patternstring += '<any,>?'
      affected_asms = [asmlistlist[x[0]][x[2]] for x in affected_tuples]
      patinsn = self._asm_to_PPstring(affected_asms, affected_asms)
      patternstring += patinsn + '\n'
    return self._postprocess_pattern(patternstring)
    
    
  def build_intermediate_table(self, asmlistlist):
    assert(type(asmlistlist) == list )
    asmlistlist.sort(reverse=True)  # sorts the list of AsmList based on length, biggest first
    t_table = []
    for i in range(1, len(asmlistlist)):
      table = self.match_two(asmlistlist[0], asmlistlist[i])
      table = self._update_table_weights(table, asmlistlist[0], asmlistlist[i])
      t_table.append(table)
      
    # TODO: Finish function
    return t_table
  

"""
%%%%%%% MATCHTABLE ITERATOR

USED FOR CHANGING (x,y) Matches into a general pattern-parsing table
that becomes straightforward to turn into an asmregex pattern (to some extent).
"""


class MatchTableIterator( object ):
  
  def __init__(self, initial_table=None):
    self.l = logging.getLogger("asmregex.Generator.MatchTableIterator")
    self.l.setLevel(logging.DEBUG)
    self.tablematrix = [[]]
    self.property_dict = dict()
    if initial_table is not None:
      self.add_table(initial_table, 0, 1)
      
      
  def _reset_iter_pointer(self):
    self.pointer_matrix = []
    for x_index in range(len(self.tablematrix)):
      self.pointer_matrix.append([])
      for _ in self.tablematrix[x_index]:
        self.pointer_matrix[x_index].append(0)

  def __iter__(self):
    self._reset_iter_pointer()
    return self

  def __next__(self):
    potentials = self._find_next_elts()
    if len(potentials) < 1:
      raise StopIteration
    traces = self._get_match_traces(potentials)
    if len(traces) < 1:
      raise StopIteration
    elif len(traces) == 1:
      return self._return_next_from_trace(potentials)
    elif len(traces) > 1:
      maxlen = 0
      constraints = ''
      for trace in traces:
        tracemax, _, tracecon = self._return_next_from_trace([pot for pot in potentials if pot[0] in trace])
        maxlen = max(maxlen, tracemax)
        constraints = [x for x in constraints if x in tracecon.split(',')]
        for pot in potentials:  # so kind of fixed here, I think
          self.pointer_matrix[pot[0]][pot[1]] += 1
        #raise NotImplementedError('Found 2 independent next match traces. This isnt implemented yet :( ')
      return maxlen, map(lambda x: (x[0],x[1], self.pointer_matrix[x[0]] [x[1]] - 1), potentials), ','.join(constraints)
    raise RuntimeError('This can never be possible.')
  
  def _return_next_from_trace(self, potentials):
    ptrmatrix = self._get_updated_pointer_matrix(potentials)
    maxlen, constraints = self._get_dist_and_constraints(ptrmatrix)
    self.pointer_matrix = ptrmatrix  # This would be buggy, as it will repeatedly match the same "next"
    # because we don't have a +1
    for pot in potentials:  # so kind of fixed here, I think
      self.pointer_matrix[pot[0]][pot[1]] +=1
    return maxlen, [(x[0],x[1],self.pointer_matrix[x[0]][x[1]]-1) for x in potentials], constraints
  
  def _get_match_traces(self, potentials):
    traces = list()
    for pot in potentials:
      matched = False
      merge = [-1,-1]
      for i in range(len(traces)):
        tr = traces[i]
        if pot[0] in tr or pot[1] in tr:
          traces[i] = tr | {pot[0], pot[1]}
          if not matched:
            merge[0] = i
            matched = True
          else:
            merge[1] = i
      if not matched:
        newtrace = set() | {pot[0], pot[1]}
        traces.append(newtrace)
      elif merge[1] >= 0:
        elts = traces.pop(merge[1])
        traces[merge[0]] |= elts
    return traces
        
        
  
  def _get_dist_and_constraints(self, ptrmatrix):
    maxlen = 0
    constraints = deepcopy(AsmEqualityIterator.MATCH_MODES[AsmEqualityIterator.AMOUNT_OF_FUNCTIONS])
    for x in range(len(ptrmatrix)):
      for y in range(len(ptrmatrix[x])):
        if ptrmatrix[x][y] == self.pointer_matrix[x][y]:
          continue
        constraints = \
          [con for con in constraints if con in  # And I so promised myself not to do this anymore
           self.property_dict["{},{}".format(x,y)][ptrmatrix[x][y]].split(',')]
        # distance
        dist = ptrmatrix[x][y] - self.pointer_matrix[x][y]
        if dist > maxlen:
          maxlen = dist
    return maxlen, constraints
  
  
  def _get_updated_pointer_matrix(self, dependencies):
    # TODO: FINISH!!!
    new_pointer_matrix = []
    for x in range(len(self.tablematrix)):
      new_pointer_matrix.append([])
      for y in range(len(self.tablematrix[x])):
        if (x,y) in dependencies:
          new_pointer_matrix[x].append(self._get_next_match_ptr(x, y))
        else:
          new_pointer_matrix[x].append(self.pointer_matrix[x][y])
    return new_pointer_matrix
        
  def _get_dependencies(self, coord):
    new_dependencies = {coord, (coord[1], coord[0])}
    old_dependencies = set()
    while len(new_dependencies):
      newest_dependencies = set()
      for c in new_dependencies:
        next_c_ptr = self._get_next_match_ptr(c[0], c[1])
        for x in range(len(self.tablematrix)):
          if (x,c[1]) in old_dependencies or (x,c[1]) in new_dependencies:
            continue
          try:
            next_ptr = self._get_next_match_ptr(x, c[1])
            if next_ptr == next_c_ptr and (x,c[1]) not in old_dependencies:
              newest_dependencies.add((x,c[1]))
          except StopIteration:
            pass
      old_dependencies = old_dependencies | new_dependencies
      new_dependencies = newest_dependencies
    return old_dependencies
      
  
  def _get_next_match_ptr(self, x, y):
    self.l.debug('Getting next match ptr for (x,y)=({},{})'.format(x,y))
    self.l.debug('tablematrix size = {}'.format(len(self.tablematrix)))
    self.l.debug('tablematrix[x] size = {}'.format(len(self.tablematrix[x])))
    self.l.debug('tablematrix[x][y] size = {}'.format(len(self.tablematrix[x][y])))
    ptr = self.pointer_matrix[x][y]
    while self.tablematrix[x][y][ptr] < 0:
      ptr += 1
      if ptr == len(self.tablematrix[x][y]):
        raise StopIteration
    return ptr
  
  def _tracecheck_one(self, x, y, matchval):
    try:
      alt_match = self._get_next_match_ptr(x, y)
    except StopIteration:
      return True  # No need to check this one, as it's exhausted
    # if False, (x, y) is not to be matched yet: something else is in front
    return self.tablematrix[x][y][alt_match] >= matchval
    
  
  def _trace_match_ptr(self, x, y, is_reverted = False ):
    traced = {(x, y), (y, x)}  # set of 2-tuples
    try:
      matchptr = self._get_next_match_ptr(x, y)
    except StopIteration:  # has no valid matches anymore
      return traced, False
    matchval = self.tablematrix[x][y][matchptr]
    for alt_x in range(len(self.tablematrix[x])):
      if alt_x == y:
        continue  # comparing to self
      if not self._tracecheck_one(alt_x, y, matchval):
        # (x, y) is not to be matched yet, something else is in front
        return traced, False
      # Now either it's equal to (x,y) from where we traced it and it still has potential,
      # Or it's larger and hence should not be considered,
      traced.add((alt_x, y))
      traced.add((y, alt_x))
    if not is_reverted:
      return self._trace_match_ptr(y, x, is_reverted=True)
    return traced, True
      
     # if self.tablematrix[alt_x][y][alt_match] > self.tablematrix[x][y][matchptr]:
     #   traced.extend([ (alt_x, y), (y, alt_x) ])
     
  # UNUSED: WAS A BAD IDEA
  def _is_new_potential(self, potentials, new):
    for pot in potentials:
      if pot[0] == new[0] or \
         pot[1] == new[0] or \
         pot[0] == new[1] or \
         pot[1] == new[1]:
        return False
    return True # TODO: More finegrained pruning: trace the match (again)?
  
  def _find_next_elts(self):
    already_traced = set()
    potentials = set()
    for x in range(len(self.tablematrix)):
      for y in range(x,len(self.tablematrix[x])):
        if x==y or (x,y) in already_traced:
          continue
        traced, potential = self._trace_match_ptr(x, y)
        already_traced = already_traced | traced
        if potential:  #  and self._is_new_potential(potentials, (x,y)):
          potentials.add((x,y))
          potentials.add((y,x))
    self.l.debug('%d potentials found: '%len(potentials) + str(potentials))
    return potentials
  
  def add_table(self, table, index_0, index_1):
    self._preformat_table(index_0, index_1)
    dict_index = "{0},{1}".format(index_0, index_1)
    reversed_dict_index = "{1},{0}".format(index_0, index_1)  # reversed string doesn't work beyond 9
    self.l.debug('Len of table[0]: {}'.format((len(table[0]))))
    self.l.debug('Len of table[1]: {}'.format((len(table[1]))))
    self.tablematrix[index_0][index_1] = table[0]
    self.tablematrix[index_1][index_0] = table[1]
    self.l.debug('Len of table[{}][{}]: {}'.format(index_0,index_1,len(self.tablematrix[index_0][index_1])))
    self.l.debug('Len of table[{}][{}]: {}'.format(index_1, index_0, len(self.tablematrix[index_1][index_0])))
    self.property_dict[dict_index] = table[2]
    self.property_dict[reversed_dict_index] = table[3]

  def _preformat_table(self, index_0, index_1):
    self.l.debug('Building table with (x,y)=({},{})'.format(index_0, index_1))
    while len(self.tablematrix) <= index_0:
      self.tablematrix.append(list())
    while len(self.tablematrix) <= index_1:
      self.tablematrix.append(list())
    while len(self.tablematrix[index_1]) <= index_0:
      self.tablematrix[index_1].append(list())
    while len(self.tablematrix[index_0]) <= index_1:
      self.tablematrix[index_0].append(list())
  

