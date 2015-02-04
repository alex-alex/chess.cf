#!/usr/bin/env python
# encoding: utf-8

"""
api.py

Created by Alex Studnicka on 2014-12-21.
Copyright (c) 2013 Alex Studnicka. All rights reserved.
"""

import utilities
import endpoints
import random
import webapp2
import config
import json
from dbmodel import *
from protorpc import messages, message_types, remote
import webapp2_extras.appengine.auth.models as auth_models
from google.appengine.api import channel
from webapp2_extras import auth
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
from chess import chess

package = 'chess'

class LoginResponse(messages.Message):
	token			= messages.StringField(1)
	username		= messages.StringField(2)

class GameInfo(messages.Message):
	uid				= messages.IntegerField(1)
	dateCreated		= messages.IntegerField(2)
	whitePlayer		= messages.StringField(3)
	blackPlayer		= messages.StringField(4)
	color			= messages.StringField(5)
	status			= messages.IntegerField(6)

class GamesCollection(messages.Message):
	items			= messages.MessageField(GameInfo, 1, repeated=True)

class DetailGameInfo(messages.Message):
	#color			= messages.StringField(1)
	board			= messages.StringField(2)
	hints			= messages.StringField(3, repeated=True)
	opponent_played	= messages.BooleanField(4)
	channelToken	= messages.StringField(5)

class NewGameResponse(messages.Message):
	info			= messages.MessageField(GameInfo, 1)
	detailInfo		= messages.MessageField(DetailGameInfo, 2)

class FriendInfo(messages.Message):
	uid				= messages.IntegerField(1)
	username		= messages.StringField(2)
	isFriend		= messages.BooleanField(3)
	requested		= messages.BooleanField(4)

class FriendsCollection(messages.Message):
	requested		= messages.MessageField(FriendInfo, 1, repeated=True)
	friends			= messages.MessageField(FriendInfo, 2, repeated=True)

class TokenResponse(messages.Message):
	channelToken	= messages.StringField(1)

@endpoints.api(name='chess', version='v1')
class ChessApi(remote.Service):
	"""chess.cf API v1."""
	
	@classmethod
	def get_user_from_token(cls, token):
		tokenObj = auth_models.UserToken.get(subject='api', token=token)
		if not tokenObj:
			return None
		userObj = ndb.Key(Account, int(tokenObj.user)).get()
		return userObj
	
	login_request = endpoints.ResourceContainer(
		message_types.VoidMessage,
		username	= messages.StringField(1, required=True),
		password	= messages.StringField(2, required=True)
	)
	
	token_request = endpoints.ResourceContainer(
		message_types.VoidMessage,
		token		= messages.StringField(1, required=True)
	)
	
	token_uid_request = endpoints.ResourceContainer(
		message_types.VoidMessage,
		token		= messages.StringField(1, required=True),
		uid			= messages.IntegerField(2, required=True)
	)
	
	newGame_request = endpoints.ResourceContainer(
		message_types.VoidMessage,
		token		= messages.StringField(1, required=True),
		color		= messages.StringField(2, required=True),
		opponent	= messages.StringField(3, required=True),
		friend		= messages.IntegerField(4)
	)
	
	gameMove_request = endpoints.ResourceContainer(
		message_types.VoidMessage,
		token		= messages.StringField(1, required=True),
		uid			= messages.IntegerField(2, required=True),
		move		= messages.StringField(3, required=True)
	)
	
	friends_search_request = endpoints.ResourceContainer(
		message_types.VoidMessage,
		token		= messages.StringField(1, required=True),
		query		= messages.StringField(2, required=True)
	)
	
	friends_request_response_request = endpoints.ResourceContainer(
		message_types.VoidMessage,
		token		= messages.StringField(1, required=True),
		uid			= messages.IntegerField(2, required=True),
		action		= messages.StringField(3, required=True)
	)

	@endpoints.method(login_request, LoginResponse, path='login', http_method='GET', name='user.login')
	def login(self, request):
		try:
			user = Account.get_by_auth_password('lower:'+request.username.lower(), request.password)
			token = Account.token_model.create(user.key.id(), 'api')
			
			response = LoginResponse(
				token		= token.token,
				username	= user.username()
			)
			return response
			
		except (InvalidAuthIdError, InvalidPasswordError), e:
			raise endpoints.UnauthorizedException('WRONG_LOGIN')
	
	@endpoints.method(token_request, GamesCollection, path='games', http_method='GET', name='games.listGames')
	def listGames(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		gamesCollectionItems = []
		
		games = Game.query(ndb.OR(Game.whitePlayer == user.key, Game.blackPlayer == user.key)).order(-Game.dateCreated)
		for game in games:
			color, opponent_played = utilities.colorAndPlayerForGame(user, game)
			
			gameInfo = GameInfo(
				uid				= game.key.id(),
				dateCreated		= int(game.dateCreated.strftime("%s")),
				whitePlayer		= game.whitePlayerName(),
				blackPlayer		= game.blackPlayerName(),
				color			= color,
				status			= game.status
			)
			gamesCollectionItems.append(gameInfo)
		
		gamesCollection = GamesCollection(items=gamesCollectionItems)
		return gamesCollection
	
	@endpoints.method(newGame_request, NewGameResponse, path='newgame', http_method='GET', name='games.newGame')
	def newGame(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		color = request.color
		if color == 'random':
			color = random.choice(['white', 'black'])
		
		game = Game()
		
		if color == 'white':
			game.whitePlayer = user.key
		else:
			game.blackPlayer = user.key
		
		opponent = request.opponent
		if opponent == 'friend':
			friendUid = request.friend
			if not friendUid or friendUid == 0:
				raise endpoints.NotFoundException('OPPONENT_NOT_SELECTED')
			
			friendKey = ndb.Key(Account, int(friendUid))
			
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
		
		pos = chess.Position.fromJSON(game.board)
		
		hints = []
		for hintmove in pos.genMoves():
			if not pos.move(hintmove).in_check('k'):
				hints.append(chess.render(hintmove[0])+chess.render(hintmove[1]))
		
		color, opponent_played = utilities.colorAndPlayerForGame(user, game)
		
		if not opponent_played:
			pos = pos.rotate()
		
		if color == 'white':
			channelToken = game.whiteChannel
		else:
			channelToken = game.blackChannel
		
		response = NewGameResponse(
			info			= GameInfo(
				uid				= game.key.id(),
				dateCreated		= int(game.dateCreated.strftime("%s")),
				whitePlayer		= game.whitePlayerName(),
				blackPlayer		= game.blackPlayerName(),
				color			= color,
				status			= game.status
			),
			detailInfo		= DetailGameInfo(
				board			= pos.board,
				hints			= hints,
				opponent_played	= opponent_played,
				channelToken	= channelToken
			)
		)
		
		return response
	
	@endpoints.method(token_uid_request, DetailGameInfo, path='game/{uid}', http_method='GET', name='games.gameInfo')
	def gameInfo(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		game = ndb.Key(Game, int(request.uid)).get()
		if game is None:
			raise endpoints.NotFoundException('GAME_NOT_FOUND')
		
		pos = chess.Position.fromJSON(game.board)
		
		hints = []
		for hintmove in pos.genMoves():
			if not pos.move(hintmove).in_check('k'):
				hints.append(chess.render(hintmove[0])+chess.render(hintmove[1]))
		
		color, opponent_played = utilities.colorAndPlayerForGame(user, game)
		
		if not opponent_played:
			pos = pos.rotate()
		
		if color == 'white':
			channelToken = game.whiteChannel
		else:
			channelToken = game.blackChannel
		
		gameInfo = DetailGameInfo(
			board				= pos.board,
			hints				= hints,
			opponent_played		= opponent_played,
			channelToken		= channelToken
		)
		
		return gameInfo
	
	@endpoints.method(gameMove_request, message_types.VoidMessage, path='game/{uid}/move', http_method='GET', name='games.gameMove')
	def gameMove(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		game = ndb.Key(Game, int(request.uid)).get()
		if game is None:
			raise endpoints.NotFoundException('GAME_NOT_FOUND')
		
		pos = chess.Position.fromJSON(game.board)
		
		moveStr = request.move
		move = chess.parseMove(moveStr)
		if move is not None:
			pos = pos.move(move)
			
			rotate = False
			if user is None:
				if game.blackPlayer == None:
					rotate = True
			else:
				if user.key == game.blackPlayer:
					rotate = True
			
			if rotate:
				moveStr = chess.renderMove(chess.rotateMove(chess.parseMove(moveStr)))
			game.moves.append(moveStr)
		
		color, opponent_played = utilities.colorAndPlayerForGame(user, game)
		
		if user and ((game.whitePlayer == user.key and game.blackPlayer != None and game.blackPlayer.get().isAI()) or (game.blackPlayer == user.key and game.whitePlayer != None and game.whitePlayer.get().isAI())):
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
				game.status = Game.GameStatus.BlackWin
			elif pos.in_check('k'):
				game.status = Game.GameStatus.WhiteWin
			else:
				game.status = Game.GameStatus.Draw
		else:
			game.status = Game.GameStatus.InProgress
		
		game.board = pos
		game.put()

		return message_types.VoidMessage()

	@endpoints.method(token_uid_request, TokenResponse, path='game/{uid}/resetChannelToken', http_method='GET', name='games.resetChannelToken')
	def resetChannelToken(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		game = ndb.Key(Game, int(request.uid)).get()
		if game is None:
			raise endpoints.NotFoundException('GAME_NOT_FOUND')
		
		color, opponent_played = utilities.colorAndPlayerForGame(user, game)
		
		if color == "white":
			token = channel.create_channel(str(game.key.id()) + '-white', duration_minutes=config.TOKEN_TIMEOUT)
			game.whiteChannel = token
		else:
			token = channel.create_channel(str(game.key.id()) + '-black', duration_minutes=config.TOKEN_TIMEOUT)
			game.blackChannel = token
		
		game.put()
		
		response = TokenResponse(
			channelToken		= token
		)
		
		return response

	@endpoints.method(token_uid_request, message_types.VoidMessage, path='game/{uid}/leave', http_method='GET', name='games.gameLeave')
	def gameLeave(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		game = ndb.Key(Game, int(request.uid)).get()
		if game is None:
			raise endpoints.NotFoundException('GAME_NOT_FOUND')
		
		game.key.delete()
		
		return message_types.VoidMessage()
	
	@endpoints.method(token_request, FriendsCollection, path='friends', http_method='GET', name='friends.listFriends')
	def listFriends(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		requestedCollectionItems = []
		for friendKey in user.requestedFriends:
			friend = friendKey.get()
			friendInfo = FriendInfo(
				uid			= friendKey.id(),
				username	= friend.username(),
				isFriend	= False,
				requested	= True
			)
			requestedCollectionItems.append(friendInfo)
		
		friendsCollectionItems = []
		for friendKey in user.friends:
			friend = friendKey.get()
			friendInfo = FriendInfo(
				uid			= friendKey.id(),
				username	= friend.username(),
				isFriend	= True,
				requested	= False
			)
			friendsCollectionItems.append(friendInfo)
		
		friendsCollection = FriendsCollection(
			requested		= requestedCollectionItems,
			friends			= friendsCollectionItems
		)
		return friendsCollection
	
	@endpoints.method(friends_search_request, FriendsCollection, path='searchFriends', http_method='GET', name='friends.searchFriends')
	def searchFriends(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		friendsCollectionItems = []
		
		queryStr = request.query.lower()
		users = Account.query(ndb.OR(Account.auth_ids == 'lower:'+queryStr, Account.email == queryStr))
		
		friends = []
		for friend in users:
			#friend = friendKey.get()
			if friend != user:
				friends.append(friend)
		
		for friend in friends:
			friendInfo = FriendInfo(
				uid			= friend.key.id(),
				username	= friend.username(),
				isFriend	= friend.key in user.friends,
				requested	= friend.key in user.requestingFriends,
			)
			friendsCollectionItems.append(friendInfo)
		
		friendsCollection = FriendsCollection(
			friends			= friendsCollectionItems
		)
		return friendsCollection

	@endpoints.method(token_uid_request, message_types.VoidMessage, path='friend/{uid}/sendRequest', http_method='GET', name='friends.sendRequest')
	def sendRequest(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		key = ndb.Key(Account, int(request.uid))
		friend = key.get()
		
		if friend is None:
			raise endpoints.NotFoundException('FRIEND_NOT_FOUND')
		
		user.requestingFriends.append(key)
		user.put()
		
		friend = key.get()
		friend.requestedFriends.append(user.key)
		friend.put()
		
		return message_types.VoidMessage()

	@endpoints.method(friends_request_response_request, message_types.VoidMessage, path='friend/{uid}/requestResponse', http_method='GET', name='friends.requestResponse')
	def requestResponse(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		key = ndb.Key(Account, int(request.uid))
		friend = key.get()
		
		if friend is None:
			raise endpoints.NotFoundException('FRIEND_NOT_FOUND')
		
		user.requestedFriends.remove(key)
		friend.requestingFriends.remove(user.key)
		
		if request.action == 'accept':
			user.friends.append(key)
			friend.friends.append(user.key)
		
		user.put()
		friend.put()
		
		return message_types.VoidMessage()

	@endpoints.method(token_uid_request, message_types.VoidMessage, path='friend/{uid}/unfriend', http_method='GET', name='friends.unfriend')
	def unfriend(self, request):
		user = self.get_user_from_token(request.token)
		if not user:
			raise endpoints.UnauthorizedException('UNAUTHORIZED')
		
		key = ndb.Key(Account, int(request.uid))
		friend = key.get()
		
		if friend is None:
			raise endpoints.NotFoundException('FRIEND_NOT_FOUND')
		
		user.friends.remove(key)
		user.put()
		friend.friends.remove(user.key)
		friend.put()
		
		return message_types.VoidMessage()

APPLICATION = endpoints.api_server([ChessApi])