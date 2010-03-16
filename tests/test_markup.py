#!/usr/bin/env python
#
# (c) alexey pegov (spleaner@gmail.com) 2009-2010
#
import os
import sys
import unittest
import string

# is there any better way to import something from another location?
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/../app')

from markup import NoteParser

class NoteProcessor(object):
  def __init__(self):
    self.chars = []
    self.current = []
    self.output = []
    self.style_stack = []
    self.style_char = None
  
  def error(self, fsm):
    self.current.append('<p><i>Error: %s</i></p>' % str(fsm.input_symbol))
    
  def style(self, fsm):
    self.style_char = fsm.input_symbol
    
  def eof(self, fsm):
    self.para(fsm)

  def para(self, fsm):
    line = string.strip(''.join(self.current))
    if len(line): # discard empty paragraphs
      style_continuation = []
      for c in self.style_stack[::-1]:
        style_continuation.append('*' == c and '</strong>' or '</i>') 
      self.output.append('<p>%s%s</p>' % (line, ''.join(style_continuation)))
    self.current = []
    self.chars = []

  def append(self, fsm):
    line_start = 0 == len(self.chars)
    if self.style_char is not None:
      c, self.style_char = self.style_char, None
      if '*' == c or '_' == c:
        if line_start or ' ' == self.chars[-1]: # start
          if c in self.style_stack: # ignore
            self.current.append('*' == c and '*' or '_')
          elif fsm.input_symbol != ' ':
            self.current.append('*' == c and '<strong>' or '<i>')
            self.style_stack.append(c)
        elif not line_start and ' ' != self.chars[-1] and fsm.input_symbol == ' ' and c in self.style_stack:
          self.current.append('*' == c and '</strong>' or '</i>')
          self.style_stack.pop()
        else:
          self.current.append('*' == c and '*' or '_')
    elif line_start and len(self.style_stack):
      for c in self.style_stack:
        self.current.append('*' == c and '<strong>' or '<i>')
    
    self.chars.append(fsm.input_symbol)
    self.current.append(fsm.input_symbol)
    
  def result(self):
    return ''.join(self.output)

class TestMarkup(unittest.TestCase):
  def setUp(self):
    pass
  
  def test_ignore_empty(self):
    self._do("    \nshould ignore empty lines\n    \n    ",
      "<p>should ignore empty lines</p>")

  def test_styles(self):
    self._do("This is a _simple styled text_ and it should not treat underscores inside_of_the_words", 
      "<p>This is a <i>simple styled text</i> and it should not treat underscores inside_of_the_words</p>")
      
  def test_ignore(self):
    self._do("This is a *simple styled text and *some asterisks should be* ignored",
      "<p>This is a <strong>simple styled text and *some asterisks should be</strong> ignored</p>")
      
  def test_ignore2(self):
    self._do("This is a *simple styled text* and some asterisks* should be ignored",
      "<p>This is a <strong>simple styled text</strong> and some asterisks* should be ignored</p>")
      
  def test_styles_continuation(self):
    self._do("This is a _simple styled text which\nspans several different_ lines", 
      "<p>This is a <i>simple styled text which</i></p><p><i>spans several different</i> lines</p>")
      
  def test_styles_overlapping(self):
    self._do("more _styled *bold text* which *is\nbold and* italic_",
      "<p>more <i>styled <strong>bold text</strong> which <strong>is</strong></i></p><p><i><strong>bold and</strong> italic</i></p>")
  #     
  # def test_list1(self):
  #   self._do("* this is an item 1\n* this is an item 2",
  #     "<p><ul><li>this is an item 1</li><li>this is an item 2</li></ul></p>")
  # 
  # def test_list2(self):
  #   self._do("list follow\n# this is an item 1\n# this is an item 2\nend of list",
  #     "<p>list follow</p><p><ol><li>this is an item 1</li><li>this is an item 2</li></ol></p><p>end of list</p>")
      
  def _do(self, text, expected):
    processor = NoteProcessor()
    processor.buffer = []
    NoteParser(processor=processor).parse(text)
    self.assertEquals(expected, ''.join(processor.result()))
  
if __name__ == '__main__':
  unittest.main()