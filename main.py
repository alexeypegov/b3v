#!/usr/bin/env python
#
# (c) Alexey Pegov (spleaner@gmail.com) 2009-2010
#
import wsgiref.handlers
import logging
import app.util

from google.appengine.ext import webapp
from app.views import *
    
def main():
  if util.is_dev_env(): logging.getLogger().setLevel(logging.DEBUG)
  
  application = webapp.WSGIApplication(
    [
      ('/', MainHandler),
      ('/data', DataHandler),
      # ('/tests', TestsHandler)
    ], debug=True)
                                       
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()