#!/usr/bin/env python
__author__ = 'jordygennissen'

import sys
import angr

from asmregex.PatternMatcher import * 

def main(binary, patternfile, pat=None):
  """Checks one binary on all patterns given in the file of arg2, and reports the amount of matches only"""
  m = AssemblyMatcher() 
  m.loadPatternFromFile(patternfile)
  angrproject = angr.Project(binary)
  m.loadBinaries(angrproject=angrproject)
  print('On binary ' + binary)
  if pat is not None and pat in m.patterns.keys():
    print('On ' + pat + ' only')
    matches = m.match(pattern=pat)
    return
  for patname in m.patterns.keys():
    print('='*20)
    print('On '+patname)
    matches = m.match(pattern=patname)
    #if len(matches) > 0:
    #  print(str(len(matches)) + ' matches found in ' + patname + ':')
      



if __name__ == '__main__':
  arg = sys.argv
  if len(arg) > 3:
    main(arg[1], arg[2], pat=arg[3])
  else:
    main(arg[1], arg[2])
