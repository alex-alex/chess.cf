#!/usr/bin/env python
# encoding: utf-8

"""
utilities.py

Created by Alex Studnicka on 2013-05-16.
Copyright (c) 2013 Alex Studnicka. All rights reserved.
"""

import webapp2
from webapp2_extras import auth, security, sessions
import os
import jinja2
import urlparse
from dbmodel import *
from google.appengine.api import memcache

# -------------------------------

import string
ALPHABET = string.ascii_uppercase + string.ascii_lowercase + \
           string.digits + '-_'
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'

def num_encode(n):
    if n < 0:
        return SIGN_CHARACTER + num_encode(-n)
    s = []
    while True:
        n, r = divmod(n, BASE)
        s.append(ALPHABET[r])
        if n == 0: break
    return ''.join(reversed(s)).rstrip('A')

def num_decode(s):
    if s[0] == SIGN_CHARACTER:
        return -num_decode(s[1:])
    n = 0
    for c in s:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n

# -------------------------------

jinja = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

jinja.filters.update({
    'num_encode': num_encode
})

# -------------------------------

class BaseHandler(webapp2.RequestHandler):
  @webapp2.cached_property
  def auth(self):
    """Shortcut to access the auth instance as a property."""
    return auth.get_auth()
 
  @webapp2.cached_property
  def user_info(self):
    """Shortcut to access a subset of the user attributes that are stored
    in the session.
 
    The list of attributes to store in the session is specified in
      config['webapp2_extras.auth']['user_attributes'].
    :returns
      A dictionary with most user information
    """
    return self.auth.get_user_by_session()

  @webapp2.cached_property
  def user(self):
    """Shortcut to access the current logged in user.
 
    Unlike user_info, it fetches information from the persistence layer and
    returns an instance of the underlying model.
 
    :returns
      The instance of the user model associated to the logged in user.
    """
    u = self.user_info
    return self.user_model.get_by_id(u['user_id']) if u else None
 
  @webapp2.cached_property
  def user_model(self):
    """Returns the implementation of the user model.
 
    It is consistent with config['webapp2_extras.auth']['user_model'], if set.
    """   
    return self.auth.store.user_model
 
  @webapp2.cached_property
  def session(self):
      """Shortcut to access the current session."""
      return self.session_store.get_session(backend="datastore")
 
  def render_template(self, view_filename, params={}):
	params['user'] = self.user
	params['user_model'] = self.user_model
	
	if self.user is not None:
		lang = self.user.language
	else:
		lang = detectLocale(self.request.headers.get('accept_language'))
	
	params['user_lang'] = lang
	
	template = jinja.get_template(lang+"/"+view_filename)
	self.response.out.write(template.render(params))
 
  # this is needed for webapp2 sessions to work
  def dispatch(self):
      # Get a session store for this request.
      self.session_store = sessions.get_store(request=self.request)
 
      try:
          # Dispatch the request.
          webapp2.RequestHandler.dispatch(self)
      finally:
          # Save all sessions.
          self.session_store.save_sessions(self.response)

# -------------------------------

def parseAcceptLanguage(acceptLanguage):
	languages = acceptLanguage.split(",")
	locale_q_pairs = []
	
	for language in languages:
		if language.split(";")[0] == language:
			# no q => q = 1
			locale_q_pairs.append((language.strip(), "1"))
		else:
			locale = language.split(";")[0].strip()
			q = language.split(";")[1].split("=")[1]
			locale_q_pairs.append((locale, q))
	
	return locale_q_pairs

def detectLocale(acceptLanguage):
	defaultLocale = 'en_US'
	supportedLocales = ['cs_CZ', 'en_US']
	
	if acceptLanguage is not None:
		locale_q_pairs = parseAcceptLanguage(acceptLanguage)
		for pair in locale_q_pairs:
			for locale in supportedLocales:
				# pair[0] is locale, pair[1] is q value
				if pair[0].replace('-', '_').lower().startswith(locale.lower()):
					return locale
	
	return defaultLocale

# -------------------------------

def userRequired(handler):
	def check_login(self, *args, **kwargs):
		if not auth.get_auth().get_user_by_session():
			self.redirect(self.uri_for('index'))
		else:
			return handler(self, *args, **kwargs)

	return check_login

def reloadIfLogged(handler):
	def check_login(self, *args, **kwargs):
		user_session = auth.get_auth().get_user_by_session()
		if user_session:
			user = auth.get_auth().store.user_model.get_by_auth_token(user_session['user_id'], user_session['token'])[0]
			self.redirect(self.uri_for('games'))
		else:
			return handler(self, *args, **kwargs)

	return check_login

# -------------------------------

def colorAndPlayerForGame(user, game):
	opponent_played = True
	
	if not user:
		if game.whitePlayer == None:
			color = "white"
		
			if len(game.moves) & 0x1:
				opponent_played = False
			
		elif game.blackPlayer == None:
			color = "black"
		
			if not len(game.moves) & 0x1:
				opponent_played = False
			
		else:
			color = "unknown"
	else:		
		if user.key == game.whitePlayer:
			color = "white"
		
			if len(game.moves) & 0x1:
				opponent_played = False
		
		elif user.key == game.blackPlayer:
			color = "black"
		
			if not len(game.moves) & 0x1:
				opponent_played = False
		
		else:
			color = "unknown"
			
	return color, opponent_played

# -------------------------------