import logging, os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms

from utils import EditRequestHandler, make_payload
from models import Termcard, TermcardEntry
from page import PageRenderer


class TermcardForm(djangoforms.ModelForm):
    class Meta:
        model = Termcard

class TermcardEntryForm(djangoforms.ModelForm):
    class Meta:
        model = TermcardEntry

class TermcardEditor(EditRequestHandler):
    def get(self, action):
        try:
            if not self.require_login():
                return
            if not self.require_role('Manager'):
                return
            actions = {'list': self.show_list,
                       'add': self.show_add_form,
                       'delete': self.apply_delete_form,
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
            elif action == 'delete':
                self.apply_delete_form()
            else:
                logging.warn('Unrecognized request action: %s' % action)
                self.not_found()
        except:
            self.fail()

    def show_list(self):
        tcs = Termcard.all().order('-year')
        for item in tcs:
            item.id = item.key().id()
        self.respond('termcard_list.html', {'list': tcs})

    def show_add_form(self):
        self.respond('termcard_add.html', {'form': TermcardForm()})

    def apply_add_form(self):
        tc = TermcardForm(data=self.request.POST)
        if tc.is_valid():
            t = tc.save(commit=False)
            t.put()
            self.redirect('/edit/termcard/list')
        else:
            self.respond('termcard_add.html', {'form': tc})

    def apply_delete_form(self):
        key = self.request.get('key')
        if not key: return self.not_found()
        termcard = Termcard.get(key)
        if not termcard: return self.not_found()
        termcard.delete()
        self.redirect('/edit/termcard/list')

class TermcardEntryEditor(EditRequestHandler):
    def get(self, tc, action):
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
                actions[action](tc)
            else:
                logging.warn('Unrecognized request action: %s' % action)
                self.not_found()
        except:
            self.fail()
            
    def post(self, tc, action):
        try:
            if not self.require_login():
                return
            if action == 'add':
                self.apply_add_form(tc)
            elif action == 'delete':
                self.apply_delete_form(tc)
            elif action == 'modify':
                self.apply_modify_form(tc)
            else:
                logging.warn('Unrecognized request action: %s' % action)
                self.not_found()
        except:
            self.fail()

    def show_list(self, tc):
        try:
            termcard = Termcard.get(tc)
            tces = TermcardEntry.all().filter('termcard =', termcard).order('order')
            for item in tces:
                item.id = item.key().id()
        except:
            tces = []
        self.respond('termcard_entry_list.html', {'list': tces, 'tc': tc})

    def show_add_form(self, tc):
        self.respond('termcard_entry_add.html', 
                     {'form': TermcardEntryForm(initial={'termcard':tc}), 'tc': tc})

    def show_modify_form(self, tc):
        key = self.request.get('key')
        if not key: logging.error('No key for modify form'); return self.not_found()
        entry = TermcardEntry.get(key)
        if not entry:
            logging.error('Entry not found for modify form, key=%s', key)
            return self.not_found()
        self.respond('termcard_entry_modify.html', 
                     {'form': TermcardEntryForm(instance=entry),
                      'entry': entry,
                      'tc': tc})

    def apply_add_form(self, tc):
        te = TermcardEntryForm(data=self.request.POST)
        if te.is_valid():
            t = te.save(commit=False)
            t.put()
            self.redirect('/edit/termcard/%s/list' % tc)
        else:
            self.respond('termcard_entry_add.html', {'form': te,
                                                     'tc': tc})

    
    def apply_modify_form(self, tc):
        key = self.request.get('key')
        if not key: return self.not_found()
        entry = TermcardEntry.get(key)
        if not entry: return self.not_found()
        data = TermcardEntryForm(data=self.request.POST, instance=entry)
        if data.is_valid():
            entity = data.save(commit=False)
            entity.put()
            self.redirect('/edit/termcard/%s/list' % tc)
        else:
            self.respond('termcard_entry_modify.html', {'form': entry, 'entry': entry,
                                               'tc': tc})

    def apply_delete_form(self, tc):
        key = self.request.get('key')
        if not key: return self.not_found()
        entry = TermcardEntry.get(key)
        if not entry: return self.not_found()
        entry.delete()
        self.redirect('/edit/termcard/%s/list' % tc)

class TermcardRenderer(webapp.RequestHandler):
    def not_found(self):
        self.error(404)
        path = os.path.join(os.path.dirname(__file__), 'html', '404.html')
        self.response.out.write(template.render(path, make_payload({})))

    def get(self, *args):
        if len(args) == 2:
            self.show_termcard_date(*args)
        else:
            self.show_default_termcard()

    def show_termcard(self, termcard):
        entries = TermcardEntry.all().filter('termcard =', termcard)
        self.response.out.write(
            template.render(
                os.path.join(os.path.dirname(__file__), 'html', 'termcard.html'),
                make_payload({'tc': termcard, 'entries': entries})))

    def show_termcard_date(self, term, year):
        tc = Termcard.all().filter('term =', term).filter('year =', int(year)).get()
        if tc is None: return self.not_found()
        self.show_termcard(tc)

    def show_default_termcard(self): pass
