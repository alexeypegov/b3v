
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