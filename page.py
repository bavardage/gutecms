import logging, traceback
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from utils import make_payload
from models import Page

class PageRenderer(webapp.RequestHandler):
  def get(self, url):
    try:
      page = Page.all().filter('url', url).get()
      if page:
        path = os.path.join(os.path.dirname(__file__), 'html', 'page.html')
        self.response.out.write(template.render(path, 
                                                make_payload({ 'page': page, })))
      else:
        self.error(404)
        path = os.path.join(os.path.dirname(__file__), 'html', '404.html')
        self.response.out.write(template.render(path, make_payload({})))
    except:
      logging.error(traceback.format_exc())
      self.error(500)
      path = os.path.join(os.path.dirname(__file__), 'html', '500.html')
      self.response.out.write(template.render(path, make_payload({})))
