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
  
def localize_date(date):
  """ Localize date """
  months = {
    1: 'Января',
    2: 'Февраля',
    3: 'Марта',
    4: 'Апреля',
    5: 'Мая',
    6: 'Июня',
    7: 'Июля',
    8: 'Августа',
    9: 'Сентября',
    10: 'Октября',
    11: 'Ноября',
    12: 'Декабря'
  }
  
  
  return '%i %s %i' % (date.day, months[date.month], date.year)

register.filter(comment_text)
register.filter(localize_date)