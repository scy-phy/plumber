__author__ = 'jordygennissen'

import os
import sys
import json
import logging

from asmregex import AssemblyInstruction

class BinaryLoader ( object ):
  """Static class loading a binary using Radare2 (http://www.radare.org/r/) and the python pipe r2pipe.
  
  Loads the binary, disassembles the .text section and reformats the assembly into a usable format.
  """

  def __init__(self, bindir=None, **kwargs): # ignores angrprojects and all
    if bindir is None or not os.path.exists(bindir):
      raise IOError('Binary given is not found, and working inside R2pipe (no angr)!')
    self.binary_location = bindir
    self.l = logging.getLogger("AsmRegex")
    self.assemblies = []
    self.mappings = []
    try:  # https://github.com/countercept/radare2-scripts/blob/master/r2_bin_carver.py
      import r2pipe
    except ImportError as err:
      print("Error while importing module r2pipe: %s" % str(err))
      sys.exit(0)

  def get(self, id=0):
    if id != 0:
      raise NotImplementedError("R2pipe is not supported anymore and only works on direct binaries.")
    return self.assemblies[0], self.mappings[0]
  
  def get_all(self):
    """
    Returns a list of asm object lists with all their address mappings
    :return: a list of asm object lists, list of address mappings
    """
    if len(self.assemblies) == 0:
      self.reload_all()
    return self.assemblies, self.mappings
  
  def reload_all(self):
    self.assemblies = []
    self.mappings = []
    # main binary
    asmlist, address_map = self.load_binary()
    self.assemblies.append(asmlist)
    self.mappings.append(address_map)
    return  # includes are not (and will not be) implemented for Radare.
    # all dynamically included shared objects
  """
  for include in self.includes:
    asmlist, address_map = self.load_binary(include_obj=include)
    self.assemblies.append(asmlist)
    self.mappings.append(address_map)
  """
  
  @staticmethod
  def _set_bytesize(r2):
    """ Sets the radare2 bytesize to the complete size of the textfile, so we load the full disasm at once """
    sections = json.loads(r2.cmd('Sj'))
    for section in sections:
      """
      if section['name'] == "LOAD0":
        r2.cmd('b ' + str(section['size']))
        return section['size']
      """
      if section['name'] == ".text":
        r2.cmd('b ' + str(section['size']))
        r2.cmd('s 0x%x' % section['vaddr'])  # set the pointer to the beginning of .text too
        return section['size']
    raise SyntaxError('.text section not found!')

  def load_binary(self, include_obj=None):
    if include_obj is not None:
      self.get(id=1) # Cheeky solution, will throw an error
      return None, None
    return self.load(self.binary_location)


  def load(self, file_path):
    """Loads a binary into radare2, retrieves the assembly-code and reformats
    
    :param file_path:
    :returns: tuple (asmlist, address_map)
        WHERE
        list asmlist is a list of assembly objects
        dict address_map is a mapping from the assembly offset/address to the index in the asmlist
    """
    r2 = None
    try:
      r2 = r2pipe.open(file_path)
    except Exception as err:
      print('R2 open error: {err}'.format(err=err))
    r2.cmd('aa')
    #r2.cmd('aaa')
    BinaryLoader()._set_bytesize(r2)
    r2obj = json.loads(r2.cmd("pdj"))
    #CFG = json.loads(r2.cmd('agCj'))
    asmlist = AssemblyList()
    address_map = dict()
    count = 0
    invalid_ctr = 0
    for i in range(0, len(r2obj)):
      if 'opcode' not in r2obj[i]:  # TODO: Find out why and find a better solution
        assert(r2obj[i]['type'] == 'invalid')
        invalid_ctr += 1
        self.l.debug('Assembly instance has no opcode skipping instr!')
        self.l.debug(r2obj[i])
        #self.l.warning('Bytes: 0x%02x' % r2obj[i]['bytes'])
        continue
      elif invalid_ctr > 4:
        self.l.warning(str(invalid_ctr) + ' consecutive bytes labelled "invalid" until ' + "0x%02x" % r2obj[i]['offset'])
        invalid_ctr = 0
      asm = AssemblyInstruction()
      #asm['disasm'] = r2obj[i]['opcode']
      split = r2obj[i]['opcode'].split(' ',1)
      asm['opcode'] = split[0]
      if len(split) < 2:
        asm['args'] = None
      else: 
        asm['args'] = list()
        for arg in split[1].split(','): 
          asm['args'].append(arg.replace(' ', '')) # remove spaces
      asm['addr'] = r2obj[i]['offset']
      asmlist.append(asm)
      address_map[asm['addr']] = count
      count += 1
    return asmlist, address_map
