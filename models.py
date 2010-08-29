from google.appengine.ext import db

class Entry(db.Model):
    author = db.UserProperty()
    title = db.StringProperty(required=True)
    slug = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    published = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

class NavLink(db.Model):
  url = db.StringProperty(required=True)
  text = db.StringProperty(required=True)
  attribs = db.StringProperty()
  order = db.IntegerProperty()
  def as_tag(self):
    return '<a href="%s" %s>%s</a>' % (self.url, self.attribs, self.text)

class RoleAssignment(db.Model):
  user = db.UserProperty(required=True)
  role = db.StringProperty(required=True)

class Page(db.Model):
  url = db.StringProperty(required=True)
  title = db.StringProperty()
  content = db.TextProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  author = db.UserProperty()
  def formatted_date(self):
    return self.date.strftime('%d %b %Y %H:%M:%S')

