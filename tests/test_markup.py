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
    self.memory = []
    self._hyphen = False
    self.italic = False
  
  def error(self, fsm):
    self.buffer.append('Error: %s' % str(fsm.input_symbol))
    
  def append(self, fsm):
    if 0 == len(self.memory):
      self.memory.append('<p>%s' % (self.italic and '<i>' or ''))
    if self._hyphen:
      if len(self.memory) and self.memory[-1] == ' ' and fsm.input_symbol != ' ':
        self.italic = True
        self.memory.append('<i>')
      elif len(self.memory) and self.memory[-1] != ' ' and fsm.input_symbol == ' ':
        self.italic = False
        self.memory.append('</i>')
      else: self.memory.append('-')
      self._hyphen = False
        
    self.memory.append(fsm.input_symbol)
  
  def hyphen(self, fsm):
    self._hyphen = True
    
  def string(self, fsm):
    self.buffer.append('%s%s</p>' % (''.join(self.memory), self.italic and '</i>' or ''))
    print self.buffer
    self.memory = []
  
  def eof(self, fsm):
    self.string(fsm)

class TestMarkup(unittest.TestCase):
  def setUp(self):
    pass
  
  def test_text_styling(self):
    self._do("This is a -simple styled text- and it should not treat hyphens inside-of-the-words", 
      "<p>This is a <i>simple styled text</i> and it should not treat hyphens inside-of-the-words</p>")
      
  def test_para(self):
    self._do("This is a -simple styled text which\nspans several different- lines", 
      "<p>This is a <i>simple styled text which</i></p><p><i>spans several different</i> lines</p>")
  
  def _do(self, text, expected):
    processor = TestProcessor()
    processor.buffer = []
    NoteParser(processor=processor).parse(text)
    self.assertEquals(expected, ''.join(processor.buffer))
  
if __name__ == '__main__':
  unittest.main()