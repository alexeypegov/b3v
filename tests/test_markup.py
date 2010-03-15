#!/usr/bin/env python
#
# (c) alexey pegov (spleaner@gmail.com) 2009-2010
#
import os
import sys
import unittest

# is there any better way to import something from another location?
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/../app')

from markup import NoteParser

class TestProcessor(object):
  def __init__(self):
    self.buffer = []
    self._hyphen = False
  
  def error(self, fsm):
    self.buffer.append('Error: %s' % str(fsm.input_symbol))
    
  def append(self, fsm):
    if self._hyphen:
      if len(fsm.memory) and fsm.memory[-1] == ' ' and fsm.input_symbol != ' ':
        fsm.memory.append('<i>')
      elif len(fsm.memory) and fsm.memory[-1] != ' ' and fsm.input_symbol == ' ':
        fsm.memory.append('</i>')
      else: fsm.memory.append('-')
      self._hyphen = False
        
    fsm.memory.append(fsm.input_symbol)
  
  def hyphen(self, fsm):
    self._hyphen = True
    
  def string(self, fsm):
    print "memory: %s" % str(fsm.memory)
    self.buffer.append(''.join(fsm.memory))
    fsm.memory = []

class TestMarkup(unittest.TestCase):
  def setUp(self):
    pass
  
  def test_text_styling(self):
    text = "This is a -simple styled text- which whould not treat hyphens inside-of-the-words\n"
    processor = TestProcessor()
    NoteParser(processor=processor).parse(text)
    self.assertEquals("This is a <i>simple styled text</i> which whould not treat hyphens inside-of-the-words", 
      ''.join(processor.buffer))
  
if __name__ == '__main__':
  unittest.main()