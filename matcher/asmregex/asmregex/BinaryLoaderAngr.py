__author__ = 'jordygennissen'

import os
import sys
import logging

try:
  import angr
except ImportError as err:
  print("Error while importing module angr: %s" % str(err))
  sys.exit(0)

from asmregex import AssemblyInstruction, AssemblyList


class BinaryLoader ( object ):
  """Static class loading a binary using The built-in capstone from angr.
  
  Loads the binary, disassembles the .text section and reformats the assembly into a usable format.
  """

  def __init__(self, angrproject=None, bindir=None, includes=None):
    """
    Creates the binary loader
    :param angrproj: angr's project object, needed for the disassembly
    :param includes: angr bin file list (each elt has to be one in project.loader.all_objects):
                     This should contain any binary loaded in angr that needs disassembly.
    """
    self.l = logging.getLogger("AsmRegex")
    if angrproject is None:
      if bindir is None or not os.path.exists(bindir):
        raise IOError('Binary given is not found, and no angr project!')
      self.angrproj = angr.Project(bindir)
    else:
      self.angrproj = angrproject
    self.includes = includes if includes is not None else []
    self.assemblies = []
    self.mappings = []
    
  def get(self, id=0):
    """
    Returns a list of asm objects with their address mapping
    :param id: id: which loaded binary to get asm from. Typically 0 is main binary, >0 is for libs etc.
    :return: a list of asm objects, list of address mapping
    """
    if len(self.assemblies) == 0:
      self.reload_all()
    return self.assemblies[id], self.mappings[id]
  
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
    # all dynamically included shared objects
    for include in self.includes:
      asmlist, address_map = self.load_binary(include_obj=include)
      self.assemblies.append(asmlist)
      self.mappings.append(address_map)
    
  def load_function(self, function_name="main"):
    symbol_obj = self.angrproj.loader.find_symbol(function_name)
    asmblock = self.angrproj.factory.block(symbol_obj.rebased_addr, size=symbol_obj.size).capstone.insns
    return self._load_capstone_insns(asmblock)
  
  def load_slice(self, slice_offset, size):
    return self._load_capstone_insns(self.angrproj.factory.block(slice_offset, size=size).capstone.insns)
    

  def load_binary(self, include_obj = None):
    if include_obj is None:
      binary = self.angrproj.loader.all_objects[0].sections_map['.text']  # TODO: Make sure this is the binary itself, this is hacky
    else:
      binary = include_obj.sections_map['.text']
    self.l.debug('Loading full binary '+str(binary))
    self.l.debug('binary disasm size is %d bytes' % (binary.max_addr - binary.min_addr))
    return self.load_slice(binary.min_addr, size=(binary.max_addr - binary.min_addr))
    
  def _load_capstone_insns(self, asmblock):
    asmlist = AssemblyList()
    address_map = dict()
    count = 0
    invalid_ctr = 0
    for i in range(0, len(asmblock) ):
      if not asmblock[i].insn.mnemonic:  # Not sure if still needed.
        invalid_ctr += 1
        self.l.debug('Assembly instance has no opcode skipping instr!')
        self.l.debug(asmblock[i])
        #self.l.warning('Bytes: 0x%02x' % r2obj[i]['bytes'])
        continue
      elif invalid_ctr > 4:
        self.l.warning(str(invalid_ctr) +
                       ' consecutive bytes labelled "invalid" until ' + "0x%02x" % asmblock[i].insn.address)
        invalid_ctr = 0
      asm = AssemblyInstruction()
      #asm['disasm'] = asmblock[i].insn.mnemonic + ' ' + asmblock[i].insn.op_str
      asm['opcode'] = asmblock[i].insn.mnemonic
      
      for arg in asmblock[i].insn.op_str.split(','):
        asm['args'].append(arg.replace('ptr', '').replace(' ', ''))  # remove spaces
      asm['addr'] = asmblock[i].insn.address
      asmlist.append(asm)
      address_map[asm['addr']] = count
      count += 1
    return asmlist, address_map

