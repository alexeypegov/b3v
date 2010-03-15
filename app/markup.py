# (c) alexey pegov (spleaner@gmail.com) 2009-2010
# 
# markup description:
#
# -strike-through-
# _italic_
# *bold*
#
# http://somesite.com|title for <a href="http://somesite.com">title</a>
# http://somesite.com|"long title" for <a href="http://somesite.com">long title</a>
# http://somesite.com for <a href="http://somesite.com">http://somesite.com</a>
# 
# # first item
# # second item
# # third item
#
# * item
# * another
# * yet another one
#
# there are also a number of advanced things like youtube, vimeo, flickr or music mp3 files or images so
# http://www.youtube.com/watch?a=GHJGD67I will be converted to an html with embedded player
#
#
from tools import FSM

class NoteProcessor(object):
  def __init__(self):
    pass
  
  def error(fsm):
    print 'Symbol error: %s' % str(fsm.input_symbol)
  
class NoteParser(object):
  def __init__(self, processor=NoteProcessor()):
    self.fsm = FSM('INIT', processor)
    self.fsm.set_default_transition('error', 'INIT')
    self.fsm.add_transition_any ('INIT', 'append', 'INIT')
    self.fsm.add_transition('\n', 'INIT', 'string', 'INIT')
    self.fsm.add_transition('-', 'INIT', 'hyphen', 'INIT')
  
  def parse(self, text):
    self.fsm.process_list(text)

  