# (c) alexey pegov (spleaner@gmail.com) 2009-2010

from model import Note

def update_or_create_note(id, text, tags, publish):
  """ will create or update existing (id != -1) note and return this notes id 
  or raise an exception if error occured """
  
  if id != -1:
    raise "Not implemented"
  else:
    title = text
    return Note.create_and_save(title, text, tags, publish)
    