# (c) Alexey Pegov (spleaner@gmail.com) 2009-2010
import util
import logging

from commands import Commands

class MainHandler(util.TemplateHandler):
  def __init__(self):
    util.TemplateHandler.__init__(self, "main")
    
class DataHandler(util.JSONHandler):
  def prepare_data(self, user):
    return Commands().execute(self.request.params.mixed())