#!/usr/bin/env python
# encoding: utf-8

"""
dbmodel.py

Created by Alex Studnicka on 2013-05-17.
Copyright (c) 2013 Alex Studnicka. All rights reserved.
"""

from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models as auth_models
from webapp2_extras import security
from chess import chess

def enum(**enums):
    return type('Enum', (), enums)
	
class Account(auth_models.User):
	email				= ndb.StringProperty()
	friends				= ndb.KeyProperty(repeated=True)
	requestedFriends	= ndb.KeyProperty(repeated=True)
	requestingFriends	= ndb.KeyProperty(repeated=True)
	
	# Settings
	language			= ndb.StringProperty(default="en_US")
	theme				= ndb.IntegerProperty(default=0)
	difficulty			= ndb.IntegerProperty(default=2)
	sounds				= ndb.BooleanProperty(default=True)
	
	def isAI(self):
		return self.auth_ids == ['__AI__']
	
	def username(self):
		for auth_id in self.auth_ids:
			if auth_id == '__AI__':
				return u'__AI__'
			comps = auth_id.split(':')
			if comps[0] == 'own':
				return comps[1]
		return u'Anonym'
	
	def userID(self):
		return self.key.urlsafe()
		
	def set_password(self, raw_password):
		self.password = security.generate_password_hash(raw_password, length=12)

def localizedName(name, lang):
	if name == "__AI__":
		if lang == "cs_CZ":
			return u"Počítač"
		else:
			return u"Computer"
	elif name == "__ANONYMOUS__":
		if lang == "cs_CZ":
			return u"Anonym"
		else:
			return u"Anonymous"
	else:
		return name

class Game(ndb.Model):
	GameStatus = enum(
		Created		= (1 << 0),
		InProgress	= (1 << 1),
		WhiteWin	= (1 << 2),
		BlackWin	= (1 << 3),
		Draw		= (1 << 4),
	)
	
	dateCreated		= ndb.DateTimeProperty(auto_now_add=True)
	whitePlayer 	= ndb.KeyProperty(Account)
	blackPlayer 	= ndb.KeyProperty(Account)
	whiteChannel	= ndb.StringProperty(indexed=False)
	blackChannel	= ndb.StringProperty(indexed=False)
	board       	= ndb.JsonProperty(default=chess.Position.initialPos())
	moves			= ndb.StringProperty(repeated=True, indexed=False)
	status			= ndb.IntegerProperty(default=GameStatus.Created)
	
	def whitePlayerName(self):
		if self.whitePlayer:
			return self.whitePlayer.get().username()
		else:
			return u'__ANONYMOUS__'
    
	def blackPlayerName(self):
		if self.blackPlayer:
			return self.blackPlayer.get().username()
		else:
			return u'__ANONYMOUS__'
	
	def localizedWhitePlayerName(self, lang):
		return localizedName(self.whitePlayerName(), lang)
	
	def localizedBlackPlayerName(self, lang):
		return localizedName(self.blackPlayerName(), lang)
