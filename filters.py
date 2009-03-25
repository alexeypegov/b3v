# -*- coding: utf-8 -*-
from google.appengine.ext import webapp

register = webapp.template.create_template_register()

def comment_text(body):
  """ Format comments count """
  try:
    count = int(body)
    
    if count == 0:
      return "Нет комментариев"
    elif count in range(10, 20):
      return u"%i комментариев" % count
    else:
      last = count % 10
      if last == 1:
        return "%i комментарий" % count
      elif last in range(2, 5):
        return "%i комментария" % count
      else:
        return "%i комментариев" % count
    
  except ValueError:
    return "Not an INT value!"
  
register.filter(comment_text)