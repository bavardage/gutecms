import logging

from google.appengine.ext import webapp, db
from google.appengine.ext.db import djangoforms

from models import Picture
from utils import EditRequestHandler, make_payload

class PictureForm(djangoforms.ModelForm):
    class Meta:
        model = Picture

class PictureEditor(EditRequestHandler):
    def get(self, action):
        try:
            if not self.require_login():
                return
            if not self.require_role('Manager'):
                return
            actions = {'list': self.show_list,
                       'add': self.show_add_form,
                       'delete': self.apply_delete_form}
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
                logging.warn('Unrecognised request action: %s' % action)
                self.not_found()
        except:
            self.fail()

    def show_list(self):
        pics = Picture.all().order('-date')
        for p in pics:
            p.id = p.key().id()
        self.respond('pictures_list.html', {'list': pics})
    def show_add_form(self):
        self.respond('pictures_add.html', {'form': PictureForm()})
    def apply_add_form(self):
        p = PictureForm(data=self.request.POST)

        if p.is_valid():
            pic = p.save(commit=False)
            pic.picture = db.Blob(self.request.get('picture'))
            pic.put()
            self.redirect('/edit/pictures/list')
        else:
            self.respond('pictures_add.html', {'form': p})
    def apply_delete_form(self):
        key = self.request.get('key')
        if not key: return self.not_found()
        pic = Picture.get(key)
        if not pic: return self.not_found()
        pic.delete()
        self.redirect('/edit/pictures/list')
        

class PictureRenderer(webapp.RequestHandler):
    def get(self, key):
        
        picture = Picture.get(key)

        if (picture and picture.picture):
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.out.write(picture.picture)
        else:
            print picture
            print picture.picture
            self.redirect('/static/noimage.jpg')

