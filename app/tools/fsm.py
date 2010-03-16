#
# see http://code.activestate.com/recipes/146262-finite-state-machine-fsm/ for details
#
class FSMException(Exception):
  def __init__(self, value):
    self.value = value
    
  def __str__(self):
    return `self.value`

class FSM(object):
  """ Finite-State Machine """
  
  def __init__(self, initial, processor):
    self.state_transitions = {}
    self.state_any = {}
    self.state_empty = {}
    
    self.processor = processor
    self.default = None
    self.input_symbol = None
    self.initial_state = initial
    self.current_state = initial
    self.next_state = None
    self.action = None
  
  def reset(self):
    self.current_state = self.initial_state
    self.input_symbol = None
    
  def add_transition(self, input_symbol, state, action=None, next_state=None):
    if next_state is None:
      next_state = state
    self.state_transitions[(input_symbol, state)] = (action, next_state)
    
  def add_transition_list(self, list_input_symbols, state, action=None, next_state=None):
    if next_state is None:
      next_state = state
    for input_symbol in list_input_symbols:
      self.add_transition(input_symbol, state, action, next_state)
      
  def add_transition_any(self, state, action=None, next_state=None):
    if next_state is None:
      next_state = state
    self.state_any[state] = (action, next_state)
    
  def add_transition_empty(self, state, action = None, next_state=None):
    if next_state is not None:
      self.state_empty[state] = (action, next_state)
    
  def set_default_transition(self, action, next_state):
    self.default = (action, next_state)
    
  def get_transition(self, input_symbol, state):
    if self.state_transitions.has_key((input_symbol, state)):
      return self.state_transitions[(input_symbol, state)]
    elif self.state_any.has_key(state):
      return self.state_any[state]
    elif self.state_empty.has_key(state):
      (action, next_state) = self.state_empty[state]
      if action is not None:
        getattr(self.processor, action)(self)
      return self.get_transition(input_symbol, next_state)
    elif self.default is not None:
      return self.default
    else: raise FSMException, "Transition is unknown (%s, %s)" % (str(input_symbol), str(state))
  
  def process(self, input_symbol):
    self.input_symbol = input_symbol
    (self.action, self.next_state) = self.get_transition(self.input_symbol, self.current_state)
    if self.action is not None:
      getattr(self.processor, self.action)(self)
    self.current_state = self.next_state
    self.next_state = None
    
  def process_list(self, input_symbols):
    for s in input_symbols:
      self.process(s)
      
    # EOF
    getattr(self.processor, 'eof')(self)