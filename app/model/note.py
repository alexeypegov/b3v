# (c) alexey pegov (spleaner@gmail.com) 2009-2010
import logging
import re

from google.appengine.ext import db

from string import strip

class Note(db.Model):
  def tags_validator(value):
    if not len(value): raise db.BadValueError, "There should be at least one single tag!"
  
  author      = db.UserProperty(required=True, auto_current_user_add=True)
  title       = db.StringProperty(multiline=False, required=True)
  content     = db.TextProperty(required=True)
  tags        = db.ListProperty(db.Category, validator=tags_validator)
  published   = db.BooleanProperty(required=True, default=False)
  created_at  = db.DateTimeProperty(auto_now_add=True)
  updated_at  = db.DateTimeProperty(auto_now=True)
  
  @classmethod
  def create_and_save(cls, title, content, tags, published=False):
    _tags = map(db.Category, filter(len, map(strip, tags)))
    slug = Note.find_unuque_slug(title)
    note = Note(key_name=slug, title=title, content=content, tags=_tags, published=published)
    note.put()
    return note

  @classmethod
  def find_unuque_slug(cls, title):
    slug = Note.slugify(title)
    _slug, i = slug, 2
    while True:
      existing = Note.get_by_key_name(_slug)
      if existing:
        _slug = "%s-%i" % (slug, i)
        i = i + 1
      else:
        break
    return _slug

  @classmethod
  def slugify(cls, text):
    slug = re.compile(r"[^\w\s-]", re.UNICODE).sub('', text.lower())
    slug = re.compile('\s+').sub('-', slug)
    return re.compile('-+').sub('-', slug)

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
  def get_page(cls, page = 0):
    if Note.count() > page * IPP:
      return db.Query(Note).order('-created_at').fetch(IPP, page * IPP)
    return None
    
  @classmethod
  def get_recent(cls, count = 10):
    return db.Query(Note).order('-created_at').fetch(10)
    
  @classmethod
  def next_page(cls, page = 0):
    if Note.count() >= (page + 1) * IPP + 1:
      return page + 1
    else:
      return None
  
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
      return db.GqlQuery("SELECT * FROM Comment WHERE note = :1 ORDER BY created_at", note)
