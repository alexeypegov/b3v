#!/usr/bin/env python
#
# (c) alexey aegov (spleaner@gmail.com) 2009-2010
#
import logging
import inspect

from google.appengine.ext import db
from google.appengine.api import users
from django.utils import simplejson

from datamanager import *

def admin(fn):
  def new(*args, **kwargs):
    if not users.is_current_user_admin():
      return { 'status': False }
    return fn(*args, **kwargs)
  new.__original__ = fn
  return new

class Command(object):
  def __init__(self):
    pass

  def fun(self, *args):
    raise NotImplementedError
    
  def execute(self, data):
    self.validate(data)
    args = []
    for attr in self.get_attrs():
      args.append(data[attr])
    return self.fun(*args)
    
  def get_attrs(self):
    argspec = inspect.getargspec(self.fun.__original__ or self.fun)
    args = argspec[0]
    args.remove('self')
    return args # list of parameters
    
  def validate(self, data):
    for attr in self.get_attrs():
      if attr not in data: raise Exception, "'%s' should be given for '%s'!" % (attr, self.NAME)
      
  def error(self, msg):
    return {'status': False, 'error': msg}
  
  def ok(self, data):
    _map = {'status': True}
    _map.update(data)
    return _map

class NoteSave(Command):
  NAME = "note:save"

  @admin
  def fun(self, id, text, tags, publish):
    note = update_or_create_note(id, text, tags, publish)
    return self.ok({ 'id': note.key().id() })

class Commands(object):
  def __init__(self):
    self.commands = {}
    for command in Command.__subclasses__():
      self.commands[command.NAME] = command
  
  def error(self, msg):
    return {'status': False, 'error': msg}
    
  def _exec(self, command, with_id=False):
    if 'name' not in command: return self.error("Required attribute 'name' is missing for the command!")
    if with_id and 'id' not in command: return self.error("Required attribute 'id' is missing for command: '%s'" % command['name'])

    result = self.commands[command['name']]().execute(command)
    if with_id: 
      logging.debug(command)
      return {'id': command['id'], 'result': result}
    return result
  
  def execute(self, data):
    if not isinstance(data, dict): raise TypeError, "Command should be a dict type!"
    
    if 'json' not in data:
      return self.error("Required attribute 'json' is missing!")

    logging.debug(data['json'])
  
    object = simplejson.loads(data['json'])
    if isinstance(object, list):
      response = []
      for c in object:
        response.append(self._exec(command=c, with_id=True))
      return response
    elif isinstance(object, dict):
      return self._exec(object)
    else:
      return self.error("Unknown 'json' object type (nor list or dict)!")