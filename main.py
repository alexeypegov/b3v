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

from django.core.paginator import ObjectPaginator, InvalidPage
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
  
class Helpers:
  """ Just a helper methods """
  def get_html(self, template_name, _vars = {}):
    return template.render(os.path.join(os.path.dirname(__file__), '%s.html' % template_name), _vars)
  
  def render(self, response, template_name, _vars = {}):
    response.out.write(self.get_html(template_name, _vars))
  
  def render_json(self, response, template_name, _vars = {}):
    html = self.get_html(template_name, _vars)
    response.headers['Content-Type'] = 'application/json'
    simplejson.dump({'html': html}, response.out, ensure_ascii=False)
    
  def render_a(self, response, template_name, _vars = {}):
    user = users.get_current_user()
    if user:
      url = users.create_logout_url(self.request.uri)
    else:
      url = users.create_login_url(self.request.uri)
    
    _tmp = {
      'admin': users.is_current_user_admin(),
      'url': url,
      'user': user
    }
    
    _tmp.update(_vars)
    self.render(response, template_name, _tmp)
  
class MainHandler(webapp.RequestHandler, Helpers):
  """ Handles index page """
  def get(self, page = 0):
    try:
      page = int(page)
    except:
      page = 0
      
    entries = db.Query(Note).order('-created_at').fetch(10, page * 10)
    
    if db.Query(Note).count() >= (page + 1) * 10 + 1:
      next = page + 1
    else:
      next = -1
      
    template_values = {
      'view': 'index.html',
      'entries': entries,
      'next': next,
      'prev': page - 1
    }

    self.render_a(self.response, 'layout', template_values)

class NewHandler(webapp.RequestHandler, Helpers):
  """ Will send a create form """
  def get(self):
    self.render_json(self.response, 'note-form')

class CreateHandler(webapp.RequestHandler, Helpers):
  """ Will create a new post """
  def post(self):
    logging.debug('Creating a new post...')
    if users.is_current_user_admin():
      note_id = self.request.get('note_id')
      if note_id:
        try:
          _id = int(note_id)
        except ValueError:
          logging.error('Unable to parse note id: %i' % _id)
        
        note = Note.get_by_id(_id)
      else:
        note = Note()
        note.author = users.get_current_user()
      
      note.title = self.request.get('title')
      note.content = self.request.get('text')
      
      tags = map(string.strip, self.request.get('tags').split(','))
      # tags = map(string.lowercase, tags)
      try: tags.remove('')
      except: pass
      
      # TODO: remove unused tags?
      note.tags = map(db.Category, tags)
      
      note.put()
      logging.debug('Post created')
      
      template_vars = {
        'entry': note, 
        'admin': users.is_current_user_admin()
      }
      
      self.render_json(self.response, 'note', template_vars)
    else:
      logging.debug('Unable to create a post: user is not an admin')
      self.error(403)

class EditHandler(webapp.RequestHandler, Helpers):
  """ Edit note """
  def post(self):
    if users.is_current_user_admin():
      note_id = self.request.get('note_id')
      
      try:
        _id = int(note_id)
      except ValueError:
        logging.debug('Unable to parse note id: %i' % _id)

      note = Note.get_by_id(_id)
      if note:
        self.render_json(self.response, 'note-form', {'entry': note})
      else:
        logger.error('Unable to find note to edit: %s' % note_id)
    else:
      logger.error('Non-admin users can not edit notes!')
    logging.debug('Edit handler')

class DeleteHandler(webapp.RequestHandler, Helpers):
  """ Remove note & comments """
  def post(self):
    logging.debug('Remove handler')

class CommentHandler(webapp.RequestHandler, Helpers):
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
        
        self.render_json(self.response, 'comments', {'comments': [comment]})
      else:
        logging.debug('Unable to find a note for id: %s' % note_id)
    else:
      logging.debug('User should be logged in to be able to post comments!')

class FetchCommentsHandler(webapp.RequestHandler, Helpers):
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
        
      self.render_json(self.response, 'comments', template_vars)
    else:
      logging.debug('Unable to get note for id: %i' % _id)
  

class NoteHandler(webapp.RequestHandler, Helpers):
  """ Will show a certain note """
  def get(self, note_id):
    logging.debug('Show note id: %s' % note_id)
    
    try:
      _id = int(note_id)
      note = Note.get_by_id(_id)

      if note:
        template_values = {
          'title': '%s - ' % note.title,
          'view': 'full.html',
          'entry': note
        }

        self.render_a(self.response, 'layout', template_values)
      else:
        self.error(404)
      
    except ValueError:
      self.error(404)

def main():
  # set logging level
  logging.getLogger().setLevel(logging.DEBUG)
  
  application = webapp.WSGIApplication([
    ('/([\d]*)', MainHandler),
    ('/new', NewHandler),
    ('/create', CreateHandler),
    ('/add-comment', CommentHandler),
    ('/fetch-comments', FetchCommentsHandler),
    (r'/note/([0-9]+)-[^\?/#]+', NoteHandler),
    ('/edit', EditHandler),
    ('/delete', DeleteHandler)
    ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
