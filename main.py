#!/usr/bin/env python

import os
import wsgiref.handlers
import re
import string
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from django.utils import simplejson

class Note(db.Model):
  author = db.UserProperty()
  title = db.StringProperty()
  content = db.TextProperty()
  tags = db.ListProperty(db.Category)
  created_at = db.DateTimeProperty(auto_now_add=True)
  
  def encode_name(self):
    # todo: !?&, etc!
    return u'%i-%s' % (self.key().id(), re.sub('\s+', '-', self.title.lower()))

class Comment(db.Model):
  note = db.ReferenceProperty(Note, collection_name='comments')
  author = db.UserProperty()
  content = db.StringProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
  
class MainHandler(webapp.RequestHandler):
  """ Handles index page """
  def get(self):
    try:
      entries = db.Query(Note).order('-created_at').fetch(limit=7)
      user = users.get_current_user()
      if user:
        url = users.create_logout_url(self.request.uri)
      else:
        url = users.create_login_url(self.request.uri)

      template_values = {
        'title': 'test',
        'admin': users.is_current_user_admin(),
        'url': url,
        'user': user,
        'view': 'index.html',
        'entries': entries
      }

      path = os.path.join(os.path.dirname(__file__), 'layout.html')
      self.response.out.write(template.render(path, template_values))
    except:
      logging.error('Unable to get notes from the datastore')

class NewHandler(webapp.RequestHandler):
  """ Will send a create form """
  def get(self):
    html = template.render(os.path.join(os.path.dirname(__file__), 'create.html'), {})
    self.response.headers['Content-Type'] = 'application/json'
    simplejson.dump({'html': html}, self.response.out, ensure_ascii=False)

class CreateHandler(webapp.RequestHandler):
  """ Will create a new post """
  def post(self):
    logging.debug('Creating a new post...')
    if users.is_current_user_admin():
      note = Note()
      note.author = users.get_current_user()
      note.title = self.request.get('title')
      note.content = self.request.get('text')
      
      tags = map(string.strip, self.request.get('tags').split(','))
      # tags = map(string.lowercase, tags)
      try: tags.remove('')
      except: pass
      
      note.tags = map(db.Category, tags)
      note.put()
      
      logging.debug('Post created')
    else:
      logging.debug('Unable to create a post: user is not an admin')
      self.error(403)

class CommentHandler(webapp.RequestHandler):
  """ Will add a comment """
  def post(self):
    logging.debug('Adding a comment...')
    if users.get_current_user():
      note_id = self.request.get('note_id')
      
      try:
        _id = int(note_id)
      except ValueError:
        logging.debug('Unable to parse note id: %i' % _id)

      note = Note.get_by_id(_id)
      if note:
        logging.debug('Ok, adding the comment to: %s' % note.title)
        
        comment = Comment()
        comment.note = note
        comment.author = users.get_current_user()
        comment.content = self.request.get('comment')
          
        comment.put()
      else:
        logging.debug('Unable to find a note for id: %s' % note_id)
    else:
      logging.debug('User should be logged in to be able to post comments!')

class FetchCommentsHandler(webapp.RequestHandler):
  """ Will return comments for the given note """
  def post(self):
    note_id = self.request.get('note_id')
    
    try:
      _id = int(note_id)
    except ValueError:
      logging.debug('Unable to parse note id: %s' % note_id)

    note = Note.get_by_id(_id)
    if note:
      template_vars = {
        'comments': note.comments
      }
        
      html = template.render(os.path.join(os.path.dirname(__file__), 'comments.html'), template_vars)
      self.response.headers['Content-Type'] = 'application/json'
      simplejson.dump({'html': html}, self.response.out, ensure_ascii=False)
    else:
      logging.debug('Unable to get note for id: %i' % _id)
  

class NoteHandler(webapp.RequestHandler):
  """ Will show a certain note """
  def get(self, note_id):
    logging.debug('Show note id: %s' % note_id)
    
    try:
      _id = int(note_id)
      note = Note.get_by_id(_id)

      if note:
        user = users.get_current_user()
        if user:
          url = users.create_logout_url(self.request.uri)
        else:
          url = users.create_login_url(self.request.uri)

        template_values = {
          'title': 'test',
          'admin': users.is_current_user_admin(),
          'url': url,
          'user': user,
          'view': 'full.html',
          'entry': note
        }

        path = os.path.join(os.path.dirname(__file__), 'layout.html')
        self.response.out.write(template.render(path, template_values))
      else:
        self.error(404)
      
    except ValueError:
      self.error(404)

def main():
  # set logging level
  logging.getLogger().setLevel(logging.DEBUG)
  
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/new', NewHandler),
    ('/create', CreateHandler),
    ('/add-comment', CommentHandler),
    ('/fetch-comments', FetchCommentsHandler),
    (r'/note/([0-9]+)-.*', NoteHandler)
    ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
