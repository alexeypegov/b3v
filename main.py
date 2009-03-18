#!/usr/bin/env python

import os
import re
import uuid
import string
import logging
import wsgiref.handlers
import urllib

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from django.utils import simplejson
from django.core.paginator import ObjectPaginator, InvalidPage

IPP = 10
TEMPLATES_PATH = 'view'
NOTE_URL_PREFIX = '/note/'


class Note(db.Model):
  author = db.UserProperty()
  title = db.StringProperty()
  content = db.TextProperty()
  tags = db.ListProperty(db.Category)
  uuid = db.StringProperty()
  slug = db.StringProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
  updated_at = db.DateTimeProperty(auto_now=True)
  
  def encoded_slug(self):
    return urllib.quote(self.slug.encode('utf-8'))
  
  def w3cdtf(self):
    return self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

  @classmethod
  def get_by_slug(cls, slug):
    decoded_slug = urllib.unquote(slug).decode('utf8')
    logging.debug('Decoded slug: %s' % decoded_slug)
    return db.Query(Note).filter("slug =", decoded_slug).get()
    
  @classmethod
  def count(cls):
    return db.Query(Note).count()
    
  @classmethod
  def get_page(cls, page = 0):
    if Note.count() > page * IPP:
      return db.Query(Note).order('-created_at').fetch(10, page * IPP)
    return None
    
  @classmethod
  def get_recent(cls, count = 10):
    return db.Query(Note).order('-created_at').fetch(10)
    
  @classmethod
  def next_page(cls, page = 0):
    if Note.count() >= (page + 1) * 10 + 1:
      return page + 1
    else:
      return None
      
  @classmethod
  def get_comments(cls, id):
    note = Note.get_by_id(id)
    if not note:
      return []
    else:
      return note.comments


class Comment(db.Model):
  note = db.ReferenceProperty(Note, collection_name='comments')
  author = db.UserProperty()
  content = db.TextProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
  
  @classmethod
  def delete_for_note(cls, note):
    comments = db.Query(Comment).filter('note = ', note)
    for comment in comments:
      logging.debug('Deleting a comment: %s' % comment.content)
      comment.delete()
  
class Helpers:
  """ Just a helper methods """

  SLUGIFY_P = re.compile(r"[^\w\s-]", re.UNICODE)
  SLUGIFY_P2 = re.compile('\s+')
    
  def slugify(self, text):
    slug = Helpers.SLUGIFY_P.sub('', text.lower())
    return Helpers.SLUGIFY_P2.sub('-', slug)
  
  def get_html(self, template_name, _vars = {}, ext = 'html'):
    return template.render(os.path.join(os.path.dirname(__file__), TEMPLATES_PATH, '%s.%s' % (template_name, ext)), _vars)
  
  def render(self, response, template_name, _vars = {}, ext = 'html'):
    response.out.write(self.get_html(template_name, _vars, ext))

  def render_simple_json(self, response, _vars = {}):
    response.headers['Content-Type'] = 'application/json'
    simplejson.dump(_vars, response.out, ensure_ascii=False)
  
  def render_json(self, response, template_name, _vars = {}, _json_vars = {}):
    html = self.get_html(template_name, _vars)
    _tmp = { 'html' : html }
    _tmp.update(_json_vars)
    self.render_simple_json(response, _tmp)
    
  def render_a(self, response, template_name, _vars = {}):
    user = users.get_current_user()
    if user:
      url = users.create_logout_url(self.request.uri)
    else:
      url = users.create_login_url(self.request.uri)
    
    _tmp = {
      'admin': users.is_current_user_admin(),
      'url': url,
      'user': user,
      'total_notes': Note.count()
    }
    
    _tmp.update(_vars)
    self.render(response, template_name, _tmp)
  
class MainHandler(webapp.RequestHandler, Helpers):
  """ Handles index page """
  def get(self, page = 0):
    try:
      page = int(page)
    except ValueError:
      page = 0
      
    entries = Note.get_page(page)
    template_values = {
      'entries': entries,
      'next': Note.next_page(page),
      'prev': page - 1 if entries != None else -1
    }

    self.render_a(self.response, 'index', template_values)

class NewHandler(webapp.RequestHandler, Helpers):
  """ Will send a create form """
  def get(self):
    if users.is_current_user_admin():
      self.render_json(self.response, 'note-form')

class CreateHandler(webapp.RequestHandler, Helpers):
  """ Will add / update a note """
  def post(self):
    logging.debug('Adding/updating note...')
    if users.is_current_user_admin():
      note_id = self.request.get('note_id')
      if note_id:
        try:
          _id = int(note_id)
        except ValueError:
          logging.error('Unable to parse note id: %i' % _id)
        
        note = Note.get_by_id(_id)
      else:
        logging.debug('Initializing new note...')
        note = Note()
        note.uuid = str(uuid.uuid4())
        note.author = users.get_current_user()
      
      note.title = self.request.get('title')
      note.slug = self.slugify(note.title)
      note.content = self.request.get('text')
      
      tags = map(string.strip, self.request.get('tags').split(','))
      # tags = map(string.lowercase, tags)
      try: tags.remove('')
      except: pass
      
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
        self.error(404)
        return

      note = Note.get_by_id(_id)
      if not note:
        self.error(404)
        return
        
      self.render_json(self.response, 'note-form', {'entry': note})
    else:
      logging.error('Non-admin users can not edit notes!')

class DeleteHandler(webapp.RequestHandler, Helpers):
  """ Remove note """
  def post(self):
    status = False

    if users.is_current_user_admin():
      note_id = self.request.get('note_id')
      
      try:
        _id = int(note_id)

        note = Note.get_by_id(_id)
        if note:
          Comment.delete_for_note(note)
          note.delete()
          status = True
        else:
          logging.debug('Unable to find note for id: %i' % _id)
      except ValueError:
        logging.debug('Unable to parse note id: %i' % _id)
        return
    else:
      logging.error('Non-admin users can not delete notes!')

    self.render_simple_json(self.response, {'status': status})


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
      self.error(404)
      return

    template_vars = {
      'comments': Note.get_comments(_id)
    }
      
    self.render_json(self.response, 'comments', template_vars, { 'user': users.get_current_user() != None })
  

class NoteHandler(webapp.RequestHandler, Helpers):
  """ Will show a certain note """
  def get(self, slug):
    note = Note.get_by_slug(urllib.unquote(slug))
    if not note:
      logging.debug('Note for slug: %s was not found' % slug)
      self.error(404)
      return

    self.render_a(self.response, 'single-note', { 'entry': note })

class FeedHandler(webapp.RequestHandler, Helpers):
  """ Will generate a RSS feed """
  def get(self):
    self.response.headers['Content-Type'] = 'application/atom+xml'
    recent = Note.get_recent()
    if len(recent):
      updated = recent[0].w3cdtf()
    
    url_prefix = 'http://' + self.request.environ['SERVER_NAME']
    port = self.request.environ['SERVER_PORT']
    if port:
        url_prefix += ':%s' % port
    url_prefix += NOTE_URL_PREFIX
    
    self.render(self.response, 'atom', {'entries': recent, 'updated': updated, 'prefix': url_prefix}, ext = 'xml')
    

class FaqHandler(webapp.RequestHandler, Helpers):
  """ Will generate FAQ page """
  def get(self):
    self.render(self.response, 'faq')
    
def main():
  # set logging level
  logging.getLogger().setLevel(logging.DEBUG)
  
  application = webapp.WSGIApplication([
    (r'/([\d]*)', MainHandler),
    (r'/new', NewHandler),
    (r'/create', CreateHandler),
    (r'/add-comment', CommentHandler),
    (r'/fetch-comments', FetchCommentsHandler),
    (r'/note/([^/]+)', NoteHandler),
    (r'/edit', EditHandler),
    (r'/delete', DeleteHandler),
    (r'/feed', FeedHandler),
    (r'/faq', FaqHandler)
    ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
