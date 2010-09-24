import logging, traceback
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms

from utils import EditRequestHandler, make_payload
from models import Entry
from page import PageRenderer

class EntryForm(djangoforms.ModelForm):
    class Meta:
        model = Entry
        exclude = ['published', 'updated', 'author']

class BlogEditor(EditRequestHandler):
    def get(self, action):
        try:
            if not self.require_login():
                return
            if not self.require_role('Manager'):
                return
            actions = {'list': self.show_list,
                       'add': self.show_add_form,
                       'modify': self.show_modify_form,
                       }
            if action in actions:
                actions[action]()
            else:
                logging.warn('Unrecognized request action: %s' % action)
                self.not_found()
        except:
            self.fail()
            
    def post(self, action):
        try:
            if not self.require_login():
                return
            if action == 'add':
                self.apply_add_form()
            elif action == 'modify':
                self.apply_modify_form()
            elif action == 'delete':
                self.apply_delete_form()
            else:
                logging.warn('Unrecognized request action: %s' % action)
                self.not_found()
        except:
            self.fail()

    def show_list(self):
        entries = Entry.all().order('-published')
        for item in entries:
            item.id = item.key().id()
        self.respond('entry_list.html', {'list': entries})

    def show_add_form(self):
        self.respond('entry_add.html', {'form': EntryForm()})

    def apply_add_form(self):
        entry = EntryForm(data=self.request.POST)
        if entry.is_valid():
            e = entry.save(commit=False)
            e.author = users.get_current_user()
            e.put()
            self.redirect('/edit/blog/list')
        else:
            self.respond('entry_add.html', {'form': entry})
       
    def show_modify_form(self):
        key = self.request.get('key')
        if not key: logging.error('No key for modify form'); return self.not_found()
        entry = Entry.get(key)
        if not entry:
            logging.error('Entry not found for modify form, key=%s', key)
            return self.not_found()
        self.respond('entry_modify.html', {'form': EntryForm(instance=entry),
                                           'entry': entry})

    def apply_modify_form(self):
        key = self.request.get('key')
        if not key: return self.not_found()
        entry = Entry.get(key)
        if not entry: return self.not_found()
        data = EntryForm(data=self.request.POST, instance=entry)
        if data.is_valid():
            entity = data.save(commit=False)
            entity.author = users.get_current_user()
            entity.put()
            self.redirect('/edit/blog/list')
        else:
            self.respond('entry_modify.html', {'form': entry, 'entry': entry})

    def apply_delete_form(self):
        key = self.request.get('key')
        if not key: return self.not_found()
        entry = Entry.get(key)
        if not entry: return self.not_found()
        entry.delete()
        self.redirect('/edit/blog/list')

class BlogFrontRenderer(webapp.RequestHandler):
    def get(self):
        try:
            entries = Entry.all().order('-published').fetch(limit=6)
            path = os.path.join(os.path.dirname(__file__), 
                                'html', 'blog_front.html')
            self.response.out.write(
                template.render(path,
                                make_payload({'entries': entries, 'path': '/'})))
        except:
            logging.error(traceback.format_exc())
            self.error(500)
            path = os.path.join(os.path.dirname(__file__), 'html', '500.html')
            self.response.out.write(template.render(path, make_payload({})))

class BlogEntryRenderer(PageRenderer):
    def get(self, slug):
        entry = db.Query(Entry).filter("slug =", slug).get()
        if not entry:
            logging.warn("could not find blog entry with slug '%s',\
trying to find page with this url" % slug)
            PageRenderer.__init__(self)
            PageRenderer.get(self, slug)
        else:
            path = os.path.join(os.path.dirname(__file__), 'html', 'entry.html')
            self.response.out.write(template.render(path, 
                                                    make_payload({'entry': entry, 'path': '/%s' % slug})))
