import logging, traceback
import os

from google.appengine.api import users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template

from models import NavLink

class EditRequestHandler(webapp.RequestHandler):
  roles = None

  def respond(self, filename, payload):
    is_dev_env = ('Development' in os.getenv('SERVER_SOFTWARE'))
    env = { 'development': is_dev_env,
            'production': not is_dev_env,
          }
    user = users.get_current_user()
    role = { 'admin': self.has_role(user, 'Admin'),
             'manager': self.has_role(user, 'Manager'),
             'editor': self.has_role(user, 'Editor'),
           }
    role['none'] = self.has_no_roles(user)
    payload['env'] = env
    payload['user'] = user
    payload['role'] = role
    payload['logout_url'] = users.create_logout_url(self.request.uri)
    path = os.path.join(os.path.dirname(__file__), 'html', 'edit', filename)
    logging.info(path)
    self.response.out.write(template.render(path, payload))

  def not_found(self):
    self.error(404)
    path = os.path.join(os.path.dirname(__file__), 'html', 'edit', '404.html')
    self.response.out.write(template.render(path, { }))

  def fail(self):
    logging.error(traceback.format_exc())
    self.error(500)
    path = os.path.join(os.path.dirname(__file__), 'html', 'edit', '500.html')
    self.response.out.write(template.render(path, { }))

  def require_login(self):
    user = users.get_current_user()
    if not user:
      payload = { 'login_url': users.create_login_url(self.request.uri), }
      self.respond('unauthenticated.html', payload)
      return False
    return user

  def get_roles(self, user):
    if self.roles is None:
      self.roles = []
      for a in db.GqlQuery("SELECT * FROM RoleAssignment WHERE user = :1", user):
        self.roles.append(a.role)
      if users.is_current_user_admin():
        self.roles.append('Admin')
    return self.roles

  def has_role(self, user, role):
    return role in self.get_roles(user) or users.is_current_user_admin()

  def has_no_roles(self, user):
    return len(self.get_roles(user)) == 0

  def require_role(self, role):
    user = users.get_current_user()
    if not self.has_role(user, role):
      self.respond('unauthorized.html', { })
      return False
    return True

def make_payload(payload):
  payload['user'] = users.get_current_user()
  payload['admin'] = users.is_current_user_admin()
  payload['navlinks'] = NavLink.all().order('order')
  return payload
