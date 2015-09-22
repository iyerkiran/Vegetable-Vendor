import os
import re
import random
import hashlib
import hmac
import logging
from google.appengine.ext import db
from google.appengine.api import memcache
import json
from datetime import datetime, timedelta  
from string import letters
import webapp2
import jinja2
import time
secret = 'fart'
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())
def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val
        
class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header('Set-Cookie','%s=%s; Path=/' % (name, cookie_val))
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))
    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))
        
def users_key(group = 'default'):
    return db.Key.from_path('users', group)
    
class User(db.Model):
    name = db.StringProperty(required = True)
    pw = db.StringProperty(required = True)
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())
    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u
    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and u.pw==pw:
            return u
            
p=User(parent = users_key(),name = "cc",pw = "cc")
p.put()
            
class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/dashboard')
        else:
            msg = 'Username or Password is invalid'
            self.render('login-form.html', error = msg)
            
class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/')
        
class MainHandler(BlogHandler):
    def get (self):
        c1= vegetable.all().order('-created').get()
        self.render('index.html',c1=c1)
        
class Dashboard(BlogHandler):
    def get(self):
        if self.user:
            c1= vegetable.all().order('-created').get()
            self.render('dashboard.html',c1=c1)
        else:
            self.redirect("/login")
      
class AdminHandler(BlogHandler):
    def post(self):
        onion = self.request.get('onion')
        potato = self.request.get('potato')
        tomato = self.request.get('tomato')
        cabbage = self.request.get('cabbage')
        beans = self.request.get('beans')
        if(onion and potato and tomato and cabbage and beans):
            onion = int(onion)    
            potato = int(potato)
            tomato = int(tomato)
            cabbage = int(cabbage)
            beans = int(beans)
            tdbentry=vegetable(onion = onion, potato = potato, tomato = tomato, cabbage = cabbage, beans = beans)
            tdbentry.put()
            time.sleep(0.2)
            self.redirect("/dashboard")
        else:
            params = dict()
            params['error_form'] = "PLEASE FILL ALL THE ENTRIES BEFORE SUBMITTING"
            c1= vegetable.all().order('-created').get()
            self.render('dashboard.html',c1=c1,**params)
      
class vegetable(db.Model):    
    onion = db.IntegerProperty(required = True)
    potato = db.IntegerProperty(required = True)
    tomato = db.IntegerProperty(required = True)
    cabbage = db.IntegerProperty(required = True)
    beans = db.IntegerProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)   
    
app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/dashboard', Dashboard),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/adminkiran',AdminHandler),]
                               ,debug=True)   