#!/usr/bin/env python
# encoding: utf-8

"""
routes.py

Created by Alex Studnicka on 2013-05-16.
Copyright (c) 2013 Alex Studnicka. All rights reserved.
"""

import webapp2
import urlparse
import utilities
import logging
import json
import random
import time
import config
from dbmodel import *
from google.appengine.api import channel, mail
from webapp2_extras import auth
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
from chess import chess

class IndexHandler(utilities.BaseHandler):
	def get(self):
		self.render_template('index.html')
        
class LoginHandler(utilities.BaseHandler):
	@utilities.reloadIfLogged
	def get(self):
		self.render_template('login.html')
	
	@utilities.reloadIfLogged
	def post(self):
		username = 'lower:'+self.request.get('username').lower()
		password = self.request.get('password')
		remember = True if self.request.POST.get('remember') == 'on' else False
		try:
			authDict = self.auth.get_user_by_password(username, password, remember=remember)
			user = Account.get_by_auth_token(authDict['user_id'], authDict['token'])[0]
			self.redirect(self.uri_for('games'))
		except (InvalidAuthIdError, InvalidPasswordError), e:
			self.render_template('login.html', { 'error': True })

class LogoutHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self):
		self.auth.unset_session()
		self.redirect(self.uri_for('index'))

class RegisterHandler(utilities.BaseHandler):
	@utilities.reloadIfLogged
	def get(self):
		self.render_template('register.html')
    
	@utilities.reloadIfLogged
	def post(self):
		result = auth.get_auth().store.user_model.create_user(auth_id='lower:'+self.request.get("username").lower(), unique_properties=['email'], password_raw=self.request.get("password"), email=self.request.get("email").lower())
		
		if result[0] == True:
			result[1].auth_ids.append('own:'+self.request.get("username"))
			result[1].language = utilities.detectLocale(self.request.headers.get('accept_language'))
			result[1].put()
			self.redirect(self.uri_for('index'))
		else:
			self.render_template('register.html', { 'result': result })

class FriendsHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self):
		self.render_template('friends.html')

class FriendsSearchHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self):
		
		lang = self.user.language
		strings = {
			"en_US": {
				"ADDED": "Added",
				"REQUEST_SENT": "Request Sent",
				"SENDING": "Sending...",
				"NO_USERS_FOUND": "No users found",
				"SEND_REQUEST": "Send request"
			},
			"cs_CZ": {
				"ADDED": "Přidáno",
				"REQUEST_SENT": "Žádost odeslána",
				"SENDING": "Odesílání...",
				"NO_USERS_FOUND": "Nenalezeni žádní uživatelé",
				"SEND_REQUEST": "Odeslat žádost"
			}
		}
		
		queryStr = self.request.get('query').lower()
		users = Account.query(ndb.OR(Account.auth_ids == 'lower:'+queryStr, Account.email == queryStr))
		count = 0
		output = '<table class="table table-striped">'
		for user in users:
			if user != self.user:
				if user.key in self.user.friends:
					output += '<tr><td>'+ user.username() +u'</td><td><button class="btn btn-default" disabled><span class="glyphicon glyphicon-ok"></span> '+strings[lang]['ADDED']+'</button></td></tr>'
				elif user.key in self.user.requestingFriends:
					output += '<tr><td>'+ user.username() +u'</td><td><button class="btn btn-default" disabled><span class="glyphicon glyphicon-ok"></span> '+strings[lang]['REQUEST_SENT']+'</button></td></tr>'
				else:
					output += '<tr data-key="'+str(user.key.id())+'"><td>'+ user.username() +u'</td><td><button class="btn btn-default add-friend-btn" data-loading-text="'+strings[lang]['SENDING']+'"><span class="glyphicon glyphicon-plus"></span> '+strings[lang]['SEND_REQUEST']+'</button></td></tr>'
				count += 1
		if count == 0:
			output += '<tr><td style="color: gray; text-align: center;">'+strings[lang]['NO_USERS_FOUND']+'</td></tr>'
		output += '</table>'
		self.response.out.write(output)

class SendFriendRequestHandler(utilities.BaseHandler):
	@utilities.userRequired
	def post(self):
		keyStr = self.request.get('key')
		key = ndb.Key(Account, int(keyStr))
		
		self.user.requestingFriends.append(key)
		self.user.put()
		
		friend = key.get()
		friend.requestedFriends.append(self.user.key)
		friend.put()
		
		# Send info email
		message = mail.EmailMessage()
		message.sender	= "chess.cf <admin@chess.cf>"
		message.to		= friend.email
		message.subject	= "Žádost o přátelství v chess.cf"
		message.html	= u'<h1>♞ chess.cf</h1><p>Ahoj '+friend.username()+u',</p><h3>Uživatel <b>'+self.user.username()+u'</b> Vás požádal o přátelství</h3><p>Pro přijetí nebo odmítnutí se přihlašte na <a target="_blank" href="http://chess.cf">chess.cf</a>.</p><p>S pozdravem,<br>- Tým chess.cf</p>'
		message.send()

class FriendRequestResponseHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self, friend_id):
		action = self.request.get('action')
		key = ndb.Key(Account, int(friend_id))
		friend = key.get()
		
		self.user.requestedFriends.remove(key)
		friend.requestingFriends.remove(self.user.key)
		
		if action == 'accept':
			self.user.friends.append(key)
			friend.friends.append(self.user.key)
		
		self.user.put()
		friend.put()
		
		time.sleep(1)
		self.redirect(self.uri_for('friends'))

class UnfriendHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self, friend_id):
		key = ndb.Key(Account, int(friend_id))
		friend = key.get()
		self.user.friends.remove(key)
		self.user.put()
		friend.friends.remove(self.user.key)
		friend.put()
		time.sleep(1)
		self.redirect(self.uri_for('friends'))

class SettingsHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self):
		self.render_template('settings.html')
		
	@utilities.userRequired
	def post(self):
		self.user.difficulty = int(self.request.get('difficulty'))
		self.user.sounds = bool(self.request.get('sounds'))
		self.user.language = self.request.get('language')
		self.user.put()
		time.sleep(1)
		self.redirect(self.uri_for('settings'))

class GamesHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self):
		games = Game.query(ndb.OR(Game.whitePlayer == self.user.key, Game.blackPlayer == self.user.key)).order(-Game.dateCreated)
		self.render_template('games.html', { 'games': games })

class NewGameHandler(utilities.BaseHandler):
	@utilities.userRequired
	def post(self):
		color = self.request.get("color")
		if color == 'random':
			color = random.choice(['white', 'black'])
		
		game = Game()
		
		if color == 'white':
			game.whitePlayer = self.user.key
		else:
			game.blackPlayer = self.user.key
		
		opponent = self.request.get("opponent")
		if opponent == 'friend':
			friendKeyStr = self.request.get("opponent-friend")
			if friendKeyStr == 'None':
				self.response.content_type = 'application/json'
				self.response.out.write(json.dumps({"error": "OPPONENT_NOT_SELECTED"}))
				return
			
			friendKey = ndb.Key(Account, int(friendKeyStr))
			
			if color == 'white':
				game.blackPlayer = friendKey
			else:
				game.whitePlayer = friendKey
		elif opponent == 'computer':
			aiUser = Account.query(Account.auth_ids == '__AI__').fetch()[0]
			if color == 'white':
				game.blackPlayer = aiUser.key
			else:
				game.whitePlayer = aiUser.key
				
				# Initial AI move
				pos = chess.Position.initialPos()
				move, score = chess.search(pos)
				if move is not None:
					pos = pos.move(move)
					game.moves.append(chess.renderMove(chess.rotateMove(move)))			
					game.board = pos
		
		gameKey = game.put()
		
		if opponent == 'computer':
			if color == 'white':
				game.whiteChannel = channel.create_channel(str(gameKey.id()) + '-white', duration_minutes=config.TOKEN_TIMEOUT)
			else:
				game.blackChannel = channel.create_channel(str(gameKey.id()) + '-black', duration_minutes=config.TOKEN_TIMEOUT)
		else:
			game.whiteChannel = channel.create_channel(str(gameKey.id()) + '-white', duration_minutes=config.TOKEN_TIMEOUT)
			game.blackChannel = channel.create_channel(str(gameKey.id()) + '-black', duration_minutes=config.TOKEN_TIMEOUT)
		
		game.put()
		
		time.sleep(1)
		self.redirect(self.uri_for('game', game_id=utilities.num_encode(gameKey.id())))

class GameHandler(utilities.BaseHandler):
	def get(self, game_id):
		full_game_id = str(game_id).ljust(9, 'A')
		num_game_id = utilities.num_decode(full_game_id)
		game = ndb.Key(Game, num_game_id).get()
		
		if game is None:
			self.abort(404)
		
		pos = chess.Position.fromJSON(game.board)
		
		hints = []
		for hintmove in pos.genMoves():
			if not pos.move(hintmove).in_check('k'):
				hints.append(chess.render(hintmove[0])+chess.render(hintmove[1]))
		
		color, opponent_played = utilities.colorAndPlayerForGame(self.user, game)
		
		if not opponent_played:
			pos = pos.rotate()
		
		if color == 'white':
			token = game.whiteChannel
		else:
			token = game.blackChannel
		
		params = {
			'channel_token':	token,
			'game':				game,
			'color':			color,
			'board':			pos.board.replace('\n', '\\n'),
			'json':				json.dumps({"hints": hints, "opponent_played": opponent_played, "w_check":	pos.in_check('K'), "b_check": pos.in_check('k')})
		}
		self.render_template('game.html', params)

class GameMoveHandler(utilities.BaseHandler):
	def post(self, game_id):
		game = ndb.Key(Game, int(game_id)).get()
		pos = chess.Position.fromJSON(game.board)
		
		moveStr = self.request.get('move')
		move = chess.parseMove(moveStr)
		if move is not None:
			pos = pos.move(move)
			
			rotate = False
			if self.user is None:
				if game.blackPlayer == None:
					rotate = True
			else:
				if self.user.key == game.blackPlayer:
					rotate = True
			
			if rotate:
				moveStr = chess.renderMove(chess.rotateMove(chess.parseMove(moveStr)))
			game.moves.append(moveStr)
		
		color, opponent_played = utilities.colorAndPlayerForGame(self.user, game)
		
		if self.user and ((game.whitePlayer == self.user.key and game.blackPlayer != None and game.blackPlayer.get().isAI()) or (game.blackPlayer == self.user.key and game.whitePlayer != None and game.whitePlayer.get().isAI())):
			move, score = chess.search(pos)
			if move is not None:
				pos = pos.move(move)
				game.moves.append(chess.renderMove(chess.rotateMove(move)))
		else:
			if color == "white":
				color = "black"
			else:
				color = "white"
		
		hints = []
		for hintmove in pos.genMoves():
			if not pos.move(hintmove).in_check('k'):
				hints.append(chess.render(hintmove[0])+chess.render(hintmove[1]))
			
		jsonObj = {
			"w_check":	pos.in_check('K'),
			"b_check":	pos.in_check('k'),
			"move":		chess.render(119-move[0])+chess.render(119-move[1]) if move is not None else None,
			"hints":	hints
		}
		
		client_id = str(game.key.id()) + '-' + color
		channel.send_message(client_id, json.dumps(jsonObj))
		
		if hints is not None and len(hints) == 0:
			if pos.in_check('K'):
				if color == 'white':
					game.status = Game.GameStatus.BlackWin
				else:
					game.status = Game.GameStatus.WhiteWin
			elif pos.in_check('k'):
				if color == 'white':
					game.status = Game.GameStatus.WhiteWin
				else:
					game.status = Game.GameStatus.BlackWin
			else:
				game.status = Game.GameStatus.Draw
		else:
			game.status = Game.GameStatus.InProgress
		
		game.board = pos
		game.put()

class GameResetTokenHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self, game_id):
		game = ndb.Key(Game, int(game_id)).get()
		color, opponent_played = utilities.colorAndPlayerForGame(self.user, game)
		
		if color == "white":
			token = channel.create_channel(str(game.key.id()) + '-white', duration_minutes=config.TOKEN_TIMEOUT)
			game.whiteChannel = token
		else:
			token = channel.create_channel(str(game.key.id()) + '-black', duration_minutes=config.TOKEN_TIMEOUT)
			game.blackChannel = token
		
		game.put()
		
		self.response.content_type = 'application/json'
		self.response.out.write(json.dumps({"token": token}))

class GameLeaveHandler(utilities.BaseHandler):
	@utilities.userRequired
	def get(self, game_id):
		gameKey = ndb.Key(Game, int(game_id))
		gameKey.delete()
		time.sleep(1)
		self.redirect(self.uri_for('games'))

class WebRtcHandler(utilities.BaseHandler):
	def get(self):
		self.render_template('webrtc.html')

_routes = [
	
	# AI User
	# auth.get_auth().store.user_model.create_user(auth_id='__AI__')
	
    webapp2.Route(r'/', IndexHandler, name='index'),
    webapp2.Route(r'/login', LoginHandler, name='login'),
    webapp2.Route(r'/logout', LogoutHandler, name='logout'),
    webapp2.Route(r'/register', RegisterHandler, name='register'),
    webapp2.Route(r'/friends', FriendsHandler, name='friends'),
    webapp2.Route(r'/friends/search', FriendsSearchHandler, name='friends-search'),
    webapp2.Route(r'/friends/sendRequest', SendFriendRequestHandler, name='friends-sendrequest'),
    webapp2.Route(r'/friends/<friend_id>/requestResponse', FriendRequestResponseHandler, name='friends-requestResponse'),
    webapp2.Route(r'/friends/<friend_id>/remove', UnfriendHandler, name='friends-unfriend'),
    webapp2.Route(r'/settings', SettingsHandler, name='settings'),
    webapp2.Route(r'/games', GamesHandler, name='games'),
    webapp2.Route(r'/newgame', NewGameHandler, name='newgame'),
    webapp2.Route(r'/g/<game_id>', GameHandler, name='game'),
    webapp2.Route(r'/g/<game_id>/move', GameMoveHandler, name='game-move'),
    webapp2.Route(r'/g/<game_id>/resetToken', GameResetTokenHandler, name='game-reset-token'),
    webapp2.Route(r'/g/<game_id>/leave', GameLeaveHandler, name='game-leave'),
	
    webapp2.Route(r'/webrtc-test', WebRtcHandler),
	
]

def HandleError(request, response, exception):    
	if isinstance(exception, webapp2.HTTPException):
		errorCode = exception.code
	else:
		errorCode = 500
	
	lang = utilities.detectLocale(request.headers.get('accept_language'))
	
	template = utilities.jinja.get_template(lang+'/error.html')
	response.out.write(template.render({ 'url': request.url, 'error_code': errorCode }))
	
	response.set_status(errorCode)

def get_routes():
    return _routes

def add_routes(app):
    for r in get_routes():
        app.router.add(r)
	
	app.error_handlers[403] = HandleError
	app.error_handlers[404] = HandleError
	#app.error_handlers[500] = HandleError
