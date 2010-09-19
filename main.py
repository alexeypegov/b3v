#!/usr/bin/env python
# coding=utf-8
import os
import re
import uuid
import string
import logging
import wsgiref.handlers
import urllib
import cgi
import xmlrpclib

from time import gmtime, strftime

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import mail
from django.utils import simplejson
from django.core.paginator import ObjectPaginator, InvalidPage

"""Load custom Django template filters"""
webapp.template.register_template_library('filters')

IPP = 10
TEMPLATES_PATH = 'view'
NOTE_URL_PREFIX = '/note/'
PERMLINK_PREFIX = '/permlink/'
URL_PATTERN = re.compile(r"((^| )+http://[^ ]+)")

class Note(db.Model):
  author = db.UserProperty()
  title = db.StringProperty(multiline=False)
  content = db.TextProperty()
  tags = db.ListProperty(db.Category)
  uuid = db.StringProperty(multiline=False)
  slug = db.StringProperty(multiline=False)
  created_at = db.DateTimeProperty(auto_now_add=True)
  updated_at = db.DateTimeProperty(auto_now=True)
  
  def encoded_slug(self):
    return urllib.quote(self.slug.encode('utf-8'))
  
  def w3cdtf(self):
    return self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    
  def newer(self):
    return db.Query(Note).filter("created_at >", self.created_at).order('created_at').get()
  
  def older(self):
    return db.Query(Note).filter("created_at <", self.created_at).order('-created_at').get()

  @classmethod
  def get_by_slug(cls, slug):
    decoded_slug = urllib.unquote(slug).decode('utf8')
    return db.Query(Note).filter("slug =", decoded_slug).order('-created_at').get()
    
  @classmethod
  def get_by_uid(cls, uid):
    return db.Query(Note).filter("uuid =", uid).get()

  @classmethod
  def count(cls):
    return db.Query(Note).count()
    
  @classmethod
  def get_notes(cls, key=None):
    if key:
      return db.Query(Note).filter("__key__ < ", key).order('-__key__').fetch(IPP + 1)
    return db.Query(Note).order('-created_at').fetch(IPP + 1)
    
  @classmethod
  def get_recent(cls, count = 10):
    return db.Query(Note).order('-created_at').fetch(10)
    
  def sorted_comments(self):
    return Note.get_comments(self);
  
  @classmethod
  def get_comments(cls, _note):
    """ get sorted comments by note id or note instance """
    if isinstance(_note, Note):
      note = _note
    else:
      note = Note.get_by_id(_note)
    
    if not note:
      return []
    else:
      return db.Query(Comment).filter("note = ", note).order('created_at')

class Comment(db.Model):
  note = db.ReferenceProperty(Note, collection_name='comments')
  author = db.UserProperty()
  content = db.TextProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
  
  @classmethod
  def delete_for_note(cls, note):
    db.delete(map(lambda c: c.key(), db.Query(Comment).filter('note = ', note)))
  
class Helpers:
  """ Just a helper methods """

  SLUGIFY_P = re.compile(r"[^\w\s-]", re.UNICODE)
  SLUGIFY_P2 = re.compile('\s+')
  SLUGIFY_P3 = re.compile('-+')
  
  def get_note_url_prefix(self, request):
    url_prefix = 'http://' + request.environ['SERVER_NAME']
    port = request.environ['SERVER_PORT']
    if port and port != '80':
        url_prefix += ':%s' % port
    return url_prefix + NOTE_URL_PREFIX
    
  def get_permlink_prefix(self, request):
    url_prefix = 'http://' + request.environ['SERVER_NAME']
    port = request.environ['SERVER_PORT']
    if port and port != '80':
      url_prefix += ':%s' % port
    return url_prefix + PERMLINK_PREFIX
    
  def slugify(self, text):
    slug = Helpers.SLUGIFY_P.sub('', text.lower())
    slug = Helpers.SLUGIFY_P2.sub('-', slug)
    return Helpers.SLUGIFY_P3.sub('-', slug)
  
  def get_html(self, template_name, _vars = {}, ext = 'html'):
    _tmp = { 'debug': is_dev_env() }
    _tmp.update(_vars)
    return template.render(os.path.join(os.path.dirname(__file__), TEMPLATES_PATH, '%s.%s' % (template_name, ext)), _tmp)
  
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
    
  def render_json_a(self, response, template_name, _vars = {}, _json_vars = {}):
    self.render_json(response, template_name, self.add_auth_info(_vars), _json_vars)
    
  def render_error_json(self, response, msg):
    logging.debug(msg)
    self.render_simple_json(response, {'status': False, 'msg': msg})
    
  def user_kind(self):
    user = users.get_current_user()  
    if user:
      return users.is_current_user_admin() and 'admin' or 'auth'
    else:
      return 'plain'
  
  def mod_count(self):
    value = memcache.get('modification_count')
    return 0 if value is None else int(value)
    
  def inc_count(self):
    memcache.incr('modification_count', initial_value = 0)
  
  def get_cached(self, key, namespace=None):
    v = memcache.get(key, namespace=namespace)
    if v:
      logging.debug('Cached for %s [%s == %s]' % (key, str(v[1]), str(self.mod_count())))
      return v[1] == self.mod_count() and v[0] or None
    return None
    
  def repl_auth_block(self, _s):
    user = users.get_current_user()
    if user:
      url = users.create_logout_url(self.request.uri)
      s = "%s&nbsp;|&nbsp;<a href=\"%s\">Выйти</a>" % (user.nickname(), url)
      if users.is_current_user_admin():
        s += "&nbsp;|&nbsp;<a href=\"#\" class=\"l_create\">Написать</a>"
      return _s.replace("{*auth_block*}", s)
    else:
      url = users.create_login_url(self.request.uri)
      return _s.replace("{*auth_block*}", "<a href=\"%s\">Войти</a>" % url)
      
class MainHandler(webapp.RequestHandler, Helpers):
  """ Handles index page """
  def get(self):
    kind = self.user_kind()
    cache_key = 'index-%s' % kind
    cached = self.get_cached(cache_key, namespace='pages')
    if not cached:
      entries = Note.get_notes()
      template_values = {
        'entries': len(entries) == IPP + 1 and entries[:-1] or entries,
        'next': len(entries) == IPP + 1 and str(entries[-2].key()) or False,
        'admin': kind == 'admin',
        'user': kind in ('admin', 'auth')
      }
      
      cached = self.get_html('index', template_values)
      memcache.set(cache_key, (cached, self.mod_count()), 3600 * 12, namespace='pages')
    self.response.out.write(self.repl_auth_block(cached))

class MoreHandler(webapp.RequestHandler, Helpers):
  def post(self):
    str_key = self.request.get('key')
    kind = self.user_kind()
    cache_key = "%s-%s" % (str_key, kind)
    cached = self.get_cached(cache_key, namespace='next')
    if not cached:
      key = db.Key(encoded=str_key)
      entries = Note.get_notes(key)
      template_values = {
        'entries': len(entries) == IPP + 1 and entries[:-1] or entries,
        'next': len(entries) == IPP + 1 and str(entries[-2].key()) or False,
        'admin': kind == 'admin',
        'user': kind in ('admin', 'auth')
      }
      
      cached = self.get_html('more', template_values)
      memcache.set(cache_key, (cached, self.mod_count()), 3600 * 12, namespace = 'next')
    self.render_simple_json(self.response, {'html': cached})

class NewHandler(webapp.RequestHandler, Helpers):
  """ Will send a create form """
  def get(self):
    if users.is_current_user_admin():
      self.render_json(self.response, 'note-form', {'title': strftime("%d-%m-%Y %H:%M", gmtime())})

class CreateHandler(webapp.RequestHandler, Helpers):
  """ Will add / update a note """
  def post(self):
    if users.is_current_user_admin():
      note_id = self.request.get('note_id')
      if note_id:
        try:
          _id = int(note_id)
        except ValueError:
          self.render_error_json(self.request, 'Unable to parse note id: %i' % _id)
          return
        
        note = Note.get_by_id(_id)
      else:
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
      self.inc_count()
      
      self.ping_feedburner(self.request);
      
      logging.debug('New note: %s' % note.title)
      
      template_vars = {
        'entry': note, 
        'admin': users.is_current_user_admin()
      }
      
      self.render_json(self.response, 'note', template_vars)
    else:
      self.render_error_json(self.response, 'Unable to create a post: user is not an admin')

  def ping_feedburner(self, req):
    if not is_dev_env():
      rpc = xmlrpclib.Server('http://ping.feedburner.google.com/')
      url = 'http://' + req.environ['SERVER_NAME']
      port = req.environ['SERVER_PORT']
      if port and port != '80':
          url += ':%s' % port
      rpc.weblogUpdates.ping("Ложное движение", url)

class EditHandler(webapp.RequestHandler, Helpers):
  """ Edit note """
  def get(self, note_id):
    if users.is_current_user_admin():
      try:
        _id = int(note_id)
        note = Note.get_by_id(_id)
        if not note:
          self.render_error_json(self.response, 'Note for id: %i was not found' % _id)
          return

        self.render_json(self.response, 'note-form', {'entry': note, 'title': ''}, {'content': note.content.encode('utf-8')})
      except ValueError:
        self.render_error_json(self.response, 'Unable to parse note id: %i' % _id)
    else:
      self.render_error_json(self.response, 'Restricted area')

class DeleteHandler(webapp.RequestHandler, Helpers):
  """ Remove note """
  def post(self):
    if users.is_current_user_admin():
      note_id = self.request.get('note_id')
      
      try:
        _id = int(note_id)

        note = Note.get_by_id(_id)
        if not note:
          self.render_error_json(self.response, 'Unable to find note for id: %i' % _id)
          return
          
        Comment.delete_for_note(note)
        note.delete()
        self.inc_count()
        self.render_simple_json(self.response, {'status': True})
      except ValueError:
        self.render_error_json(self.response, 'Unable to parse note id: %i' % _id)
    else:
      self.render_error_json(self.response, 'Restricted area')

class CommentHandler(webapp.RequestHandler, Helpers):
  """ Will add a comment """
  def post(self):
    if users.get_current_user():
      note_id = self.request.get('note_id')
      
      try:
        _id = int(note_id)
        
        note = Note.get_by_id(_id)
        if not note:
          self.render_error_json(self.response, 'Unable to find a note for id: %s' % note_id)
          return
        
        comment = Comment()
        comment.note = note
        comment.author = users.get_current_user()
        
        escaped = cgi.escape(self.request.get('comment'))
        comment.content = URL_PATTERN.sub(r'<a href="\1">\1</a>', escaped)

        comment.put()
        self.inc_count()
        
        recipients = self.email_comment(self.request, note, comment, self.request.get('comment'))
        names = ''
        for r in recipients:
          names += '%s, ' % r.nickname()
        names = names.strip(" ,")
        
        self.render_json(self.response, 'comments', {'comments': [comment], 'recipients': names, 'user': self.user_kind() in ('admin', 'auth')})
      except ValueError:
        self.render_error_json(self.response, 'Unable to parse note id: %i' % _id)
    else:
      self.render_error_json(self.response, 'Login to be able to post comments!')
  
  """ e-mail comment to admin & to recepient(s) if specified """
  def email_comment(self, request, note, comment, original_text):
    comments = Note.get_comments(note)
    authors = {}
    for c in comments:
      nick = c.author.nickname()
      if nick not in authors:
        at_char = nick.find('@')
        if at_char > 0:
          nick = nick[0:at_char]
        authors[nick] = c.author
    
    to = []
    if len(authors):
      # will find all the recipients of the comment
      text = comment.content.encode('utf-8')
      parts = text.split(' ')
      for part in parts:
        word = part.strip()
        if word and word[0] == '@':
          ref = word[1:len(word)]
          if ref in authors:
            to.append(authors[ref])
    
    note_url = self.get_note_url_prefix(request) + note.encoded_slug()
    subject = self.get_html('email_subject', {'from': comment.author.nickname()}, 'txt')
    
    # send a copy to notes author if he's not commenter or not in 'to' list
    if (comment.author != note.author) and (note.author not in to):
      admin_vars = {
        'comment': comment,
        'note': note,
        'url': note_url,
        'text': original_text
      }
      
      admin_text = self.get_html('admin_email', admin_vars, 'txt')
      logging.debug('Sending mail to %s (admin)' % note.author.email())
      try: mail.send_mail(note.author.email(), note.author.email(), subject, admin_text)
      except: pass
    
    for recipient in to:
      user_vars = {
        'comment': comment,
        'note': note,
        'to': recipient.nickname(),
        'url': note_url,
        'text': original_text
      }

      user_text = self.get_html('email', user_vars, 'txt')
      logging.debug('Sending comment mail to %s' % recipient.email())
      try: mail.send_mail(note.author.email(), recipient.email(), subject, user_text)
      except: pass
    return to

class FetchCommentsHandler(webapp.RequestHandler, Helpers):
  """ Will return comments for the given note """
  def post(self):
    note_id = self.request.get('note_id')
    
    try:
      _id = int(note_id)
      
      cache_key = 'comments-%s' % _id
      cached = self.get_cached(cache_key, namespace="comments")
      if not cached:
        cached = Note.get_comments(_id)
        memcache.set(cache_key, (cached, self.mod_count()), 12 * 3600, namespace="comments")

      template_vars = {
        'comments': cached,
        'recipients': None,
        'user': self.user_kind() in ('admin', 'auth')
      }

      # todo: cache resulting html
      self.render_json(self.response, 'comments', template_vars)
    except ValueError:
      self.render_error_json(self.response, 'Unable to parse note id: %s' % note_id)

class NoteHandler(webapp.RequestHandler, Helpers):
  """ Will show a certain note """
  def get(self, slug):
    _slug = urllib.unquote(slug)
    kind = self.user_kind()
    cache_key = 'note-%s-%s' % (_slug, kind)
    cached = self.get_cached(cache_key, namespace="note")
    if not cached:
      note = Note.get_by_slug(_slug)
      if not note:
        logging.debug('Note for slug: %s was not found' % slug)
        self.error(404)
        self.render(self.response, '404')
        return
      
      cached = self.get_html('single-note', { 'entry': note, 'older': note.older(), 'newer': note.newer(), 'user': kind in ('admin', 'auth'), 'admin': kind == 'admin' })
      memcache.set(cache_key, (cached, self.mod_count()), 3600 * 12, namespace="note")      
    self.response.out.write(self.repl_auth_block(cached))

class PermLinkHandler(webapp.RequestHandler, Helpers):
  """ Will show a query by it's permlink """
  def get(self, uid):
    note = Note.get_by_uid(uid)
    if not note:
      logging.debug('Note for UID %s was not found' % uid)
      self.error(404)
      self.render(self.response, '404')
      return
    
    self.redirect(self.get_note_url_prefix(self.request) + note.encoded_slug())

class FeedHandler(webapp.RequestHandler, Helpers):
  """ Will generate a RSS feed """
  def get(self):
    self.response.headers['Content-Type'] = 'application/atom+xml'
    cached = self.get_cached('feed')
    if not cached:
      recent = Note.get_recent()
      if recent:
        updated = recent[0].w3cdtf()
      else:
        updated = None
        recent = None
      cached = self.get_html('atom', {'entries': recent, 'updated': updated, 'prefix': self.get_permlink_prefix(self.request)}, ext = 'xml')
      memcache.set('feed', (cached, self.mod_count()), 12 * 3600)
    self.response.out.write(cached)

class FaqHandler(webapp.RequestHandler, Helpers):
  """ Will generate FAQ page """
  def get(self):
    self.render(self.response, 'faq')
    
class NotFoundPageHandler(webapp.RequestHandler, Helpers):
  """ Will render a 404 page """
  def get(self):
    self.error(404)
    self.render(self.response, '404')

def is_dev_env():
  """ Checks whatever we are under devel environment (localhost) """
  return os.environ.get('SERVER_SOFTWARE','').startswith('Devel') # 'Goog' for production
    
def main():
  # set logging level
  if is_dev_env():
    logging.getLogger().setLevel(logging.DEBUG)
  
  application = webapp.WSGIApplication([
    (r'/', MainHandler),
    (r'/new', NewHandler),
    (r'/more', MoreHandler),
    (r'/create', CreateHandler),
    (r'/add-comment', CommentHandler),
    (r'/fetch-comments', FetchCommentsHandler),
    (r'/note/([^/]+)', NoteHandler),
    (r'/permlink/([^/]+)', PermLinkHandler),
    (r'/edit/([\d]+)', EditHandler),
    (r'/delete', DeleteHandler),
    (r'/feed', FeedHandler),
    (r'/faq', FaqHandler),
    (r'/.*', NotFoundPageHandler)
    ], debug=is_dev_env())
  
  run_wsgi_app(application)  
  # wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()