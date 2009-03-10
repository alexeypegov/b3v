#!/usr/bin/env python

import os
import wsgiref.handlers


from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from django.utils import simplejson

class MainHandler(webapp.RequestHandler):

	def get(self):
		path = os.path.join(os.path.dirname(__file__), 'layout.html')
		
		template_values = {
		  'title': 'test',
		  'admin': True,
		  'view': 'index.html'
		}
		
		self.response.out.write(template.render(path, template_values))

class CreateHandler(webapp.RequestHandler):
  """ Will send a create form """
  def get(self):
    html = template.render(os.path.join(os.path.dirname(__file__), 'create.html'), {})
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({'html': html}))


def main():
	application = webapp.WSGIApplication([
	  ('/', MainHandler),
	  ('/create', CreateHandler)
	  ], debug=True)
 	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
