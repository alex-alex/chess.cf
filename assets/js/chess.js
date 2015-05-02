var CHESS_APP = CHESS_APP || {};

var STRINGS = {
	"en_US": {
		"BLACK_WON": "Black won",
		"WHITE_WON": "White won",
		"DRAW": "Draw",
		"BLACK": "Black",
		"WHITE": "White",
		"TO_BLACK": "to black",
		"TO_WHITE": "to white",
		"CHECK": "check",
		"CHECKMATE": "checkmate",
		"GAME_OVER": "Game over",
		"GAVE": "gave",
		"MOVED": "moved",
		"CASTLED": "castled",
		"TAKEN": "has taken",
		"EN_PASSANT": "has taken en passant",
		"PROMOTED": "promoted to",
		"FROM": "from",
		"TO": "to",
	},
	"cs_CZ": {
		"BLACK_WON": "Vyhrál černý",
		"WHITE_WON": "Vyhrál bílý",
		"DRAW": "Remíza",
		"BLACK": "Černý",
		"WHITE": "Bílý",
		"TO_BLACK": "černému",
		"TO_WHITE": "bílému",
		"CHECK": "šach",
		"CHECKMATE": "šachmat",
		"GAME_OVER": "Konec hry",
		"GAVE": "dal",
		"MOVED": "se přesunul",
		"CASTLED": "provedl rošádu",
		"TAKEN": "sebral",
		"EN_PASSANT": "sebral mimochodem",
		"PROMOTED": "povýšil na",
		"FROM": "z",
		"TO": "na",
	}
}

var SOUND_CLICK = new Audio('/assets/sounds/click.wav');
var SOUND_ILLEGAL = new Audio('/assets/sounds/illegal.wav');
var SOUND_MOVE = new Audio('/assets/sounds/move.wav');
var SOUND_CAPTURE = new Audio('/assets/sounds/capture.wav');
var SOUND_SPECIAL_MOVE = new Audio('/assets/sounds/special.wav');
var SOUND_CHECK = new Audio('/assets/sounds/check.wav');
var SOUND_MOVE_2 = new Audio('/assets/sounds/move2.wav');
var SOUND_CAPTURE_2 = new Audio('/assets/sounds/capture2.wav');
var SOUND_SPECIAL_MOVE_2 = new Audio('/assets/sounds/special2.wav');
var SOUND_CHECK_2 = new Audio('/assets/sounds/check2.wav');
var SOUND_WIN = new Audio('/assets/sounds/win.wav');
var SOUND_DRAW = new Audio('/assets/sounds/draw.wav');
var SOUND_LOSS = new Audio('/assets/sounds/loss.wav');
var SOUND_NEW_GAME = new Audio('/assets/sounds/newgame.wav');

var COLOR = COLOR || {};
COLOR.WHITE = "WHITE";
COLOR.BLACK = "BLACK";

var PIECE = PIECE || {};
PIECE.KING = "KING";
PIECE.QUEEN = "QUEEN";
PIECE.ROOK = "ROOK";
PIECE.BISHOP = "BISHOP";
PIECE.KNIGHT = "KNIGHT";
PIECE.PAWN = "PAWN";

// ------------------------------------
// Piece
// ------------------------------------

function Piece(color, type) {
	this.color = color;
	this.type = type;
}

Piece.fromClass = function(class_str) {
	if (!class_str) return new Piece(null, null);
	
	var color_letter = class_str.charAt(0);
	var piece_letter = class_str.charAt(2);
	var color, piece;
	
	if (color_letter == 'W') { color = COLOR.WHITE; }
	else if (color_letter == 'B') { color = COLOR.BLACK; }
	
	if (piece_letter == 'K') { piece = PIECE.KING; }
	else if (piece_letter == 'Q') { piece = PIECE.QUEEN; }
	else if (piece_letter == 'R') { piece = PIECE.ROOK; }
	else if (piece_letter == 'B') { piece = PIECE.BISHOP; }
	else if (piece_letter == 'N') { piece = PIECE.KNIGHT; }
	else if (piece_letter == 'P') { piece = PIECE.PAWN; }
	
	return new Piece(color, piece);
}

Piece.fromChar = function(char, isBlack) {
	if (!char) return new Piece(null, null);
	if (char == '.') return null;
	
	if (isBlack) {
		if (char == char.toLowerCase()) { color = COLOR.WHITE; }
		else { color = COLOR.BLACK; }
	} else {
		if (char == char.toLowerCase()) { color = COLOR.BLACK; }
		else { color = COLOR.WHITE; }
	}
	
	if (char.toLowerCase() == 'k') { piece = PIECE.KING; }
	else if (char.toLowerCase() == 'q') { piece = PIECE.QUEEN; }
	else if (char.toLowerCase() == 'r') { piece = PIECE.ROOK; }
	else if (char.toLowerCase() == 'b') { piece = PIECE.BISHOP; }
	else if (char.toLowerCase() == 'n') { piece = PIECE.KNIGHT; }
	else if (char.toLowerCase() == 'p') { piece = PIECE.PAWN; }
	
	return new Piece(color, piece);
}

Piece.prototype.toString = function(){
	return this.color+'_'+this.type;
}

Piece.prototype.toClass = function(){
	var tmpType = this.type;
	if (tmpType == PIECE.KNIGHT) tmpType = 'N';
	return this.color.charAt(0)+'_'+tmpType.charAt(0);
}

Piece.prototype.toSymbol = function(){
	if (this.color == COLOR.WHITE) {
		if (this.type == PIECE.KING) { return '♔'; }
		else if (this.type == PIECE.QUEEN) { return '♕'; }
		else if (this.type == PIECE.ROOK) { return '♖'; }
		else if (this.type == PIECE.BISHOP) { return '♗'; }
		else if (this.type == PIECE.KNIGHT) { return '♘'; }
		else if (this.type == PIECE.PAWN) { return '♙'; }
	} else if (this.color == COLOR.BLACK) {
		if (this.type == PIECE.KING) { return '♚'; }
		else if (this.type == PIECE.QUEEN) { return '♛'; }
		else if (this.type == PIECE.ROOK) { return '♜'; }
		else if (this.type == PIECE.BISHOP) { return '♝'; }
		else if (this.type == PIECE.KNIGHT) { return '♞'; }
		else if (this.type == PIECE.PAWN) { return '♟'; }
	}
	return '?';
}

// ------------------------------------
// Board
// ------------------------------------

function Board(board) {
	this.selectedRow = -1;
	this.selectedCol = -1;
	this.isBlack = CHESS_APP.isBlack;
	
	if (board) {
		this.array =[];
		for (var row=0; row<8; row++) {
			var rowArr = [];
			for (var col=0; col<8; col++) {
				rowArr.push(Piece.fromChar(board[row][col], this.isBlack));
			}
			this.array.push(rowArr);
		}
	}
	
	if (!CHESS_APP.data.opponent_played) {
		CHESS_APP.waiting = true;
		$('#board-overlay').show();
		//this.move(-1, -1, true);
	}
}

Board.prototype.getCell = function(row, col) {
	return $('#chess-board tr:nth-child('+(row+2)+') td:nth-child('+(col+2)+')');
}

Board.prototype.redraw = function() {
	
	for (var row = -1; row < 9; row++) {
		for (var col = -1; col < 9; col++) {
			cell = this.getCell(row, col)
			if (row == -1 || col == -1 || row == 8 || col == 8) {
				
				if (row == -1 || row == 8) {
					if (col == -1  || col == 8) {
						cell.text(' ')
					} else {
						if (this.isBlack) {
							cell.text(String.fromCharCode(97 + (7-col)))
						} else {
							cell.text(String.fromCharCode(97 + col))
						}
					}
				} else {
					if (row == -1  || row == 8) {
						cell.text(' ')
					} else {
						if (this.isBlack) {
							cell.text(row+1)
						} else {
							cell.text(7-row+1)
						}
					}
				}
				
			} else {
				cell.removeClass();
				piece = this.array[row][col];
				if (piece) {
					cell.addClass(piece.toClass());
				} else {
					cell.addClass('X');
				}
			}
			
		}
	}
}

Board.prototype.startMove = function(row, col) {
	
	piece = this.array[row][col];
	
	if (!piece || !((this.isBlack && piece.color == COLOR.BLACK) || (!this.isBlack && piece.color == COLOR.WHITE))) return;
	
	var cell = this.getCell(row, col);
	cell.addClass('selected-piece');
	
	this.selectedRow = row;
	this.selectedCol = col;
	
	var canMove = false;
	
	for (i in CHESS_APP.data.hints) {
		move = pareseMove(CHESS_APP.data.hints[i])
		
		if (row == move[0][0] && col == move[0][1]) {
			canMove = true;
			
			var moveRow = move[1][0];
			var moveCol = move[1][1];
			
			var cell = this.getCell(moveRow, moveCol);
			if (this.array[moveRow][moveCol]) {
				cell.addClass('enemy_hint');	
			} else {
				cell.addClass('hint');
			}
		}
	}
	
	if (canMove) {
		playSound(SOUND_CLICK);
	}/* else {
		playSound(SOUND_ILLEGAL);
	}*/
	
}

Board.prototype.move = function(row, col, user) {
	
	var curRow = row;
	var curCol = col;
	
	if (!CHESS_APP.waiting) {
	
		var piece = this.array[this.selectedRow][this.selectedCol];
		
		if (!piece) {
			alert('Chyba: NO_PIECE');
			return;
		}
		
		// Piece being taken
		var orig_piece = this.array[row][col];
		
		// Castling
		var castling = false;
		if (piece.type == PIECE.KING) {
			if (this.isBlack) {
				if (piece.color == COLOR.BLACK && this.selectedRow == 7 && this.selectedCol == 3) {
					if (row == 7 && col == 1) {
						castling = true;
						this.array[7][0] = null;
						this.array[7][2] = new Piece(COLOR.BLACK, PIECE.ROOK);
					} else if (row == 7 && col == 5) {
						castling = true;
						this.array[7][7] = null;
						this.array[7][4] = new Piece(COLOR.BLACK, PIECE.ROOK);
					}
				} else if (piece.color == COLOR.WHITE && this.selectedRow == 0 && this.selectedCol == 3) {
					if (row == 0 && col == 1) {
						castling = true;
						this.array[0][0] = null;
						this.array[0][2] = new Piece(COLOR.WHITE, PIECE.ROOK);
					} else if (row == 0 && col == 5) {
						castling = true;
						this.array[0][7] = null;
						this.array[0][4] = new Piece(COLOR.WHITE, PIECE.ROOK);
					}
				}
			} else {
				if (piece.color == COLOR.WHITE && this.selectedRow == 7 && this.selectedCol == 4) {
					if (row == 7 && col == 2) {
						castling = true;
						this.array[7][0] = null;
						this.array[7][3] = new Piece(COLOR.WHITE, PIECE.ROOK);
					} else if (row == 7 && col == 6) {
						castling = true;
						this.array[7][7] = null;
						this.array[7][5] = new Piece(COLOR.WHITE, PIECE.ROOK);
					}
				} else if (piece.color == COLOR.BLACK && this.selectedRow == 0 && this.selectedCol == 4) {
					if (row == 0 && col == 2) {
						castling = true;
						this.array[0][0] = null;
						this.array[0][3] = new Piece(COLOR.BLACK, PIECE.ROOK);
					} else if (row == 0 && col == 6) {
						castling = true;
						this.array[0][7] = null;
						this.array[0][5] = new Piece(COLOR.BLACK, PIECE.ROOK);
					}
				}
			}
		}
		
		// En passant
		var en_passant = false;
		if (piece.type == PIECE.PAWN && curCol != this.selectedCol && !orig_piece) {
			en_passant = true;
			var en_passant_taken_pos = [this.selectedRow, curCol];
			var en_passant_taken_piece = this.array[this.selectedRow][curCol];
			this.array[this.selectedRow][curCol] = null;
		}
	
		// Promotion
		var before_promotion;
		var promotion = false;
		if (piece.type == PIECE.PAWN) {
			if (this.isBlack) {
				if (piece.color == COLOR.BLACK && curRow == 0) {
					promotion = true;
				} else if (piece.color == COLOR.WHITE && curRow == 7) {
					promotion = true;
				}
			} else {
				if (piece.color == COLOR.WHITE && curRow == 0) {
					promotion = true;
				} else if (piece.color == COLOR.BLACK && curRow == 7) {
					promotion = true;
				}
			}
		}
		if (promotion) {
			before_promotion = new Piece(piece.color, PIECE.PAWN);
			piece.type = PIECE.QUEEN;
		} else {
			before_promotion = piece;
		}
	
		// Actual move
		this.array[this.selectedRow][this.selectedCol] = null;
		this.array[curRow][curCol] = piece;
	
		// Redraw
		this.redraw();
		
		if (this.isBlack) {
			$("#moves-list").prepend('<span class="list-group-item">'+before_promotion.toSymbol()+' '+(castling ? trans('CASTLED') : trans('MOVED'))+' '+trans('FROM')+' '+String.fromCharCode(96 + (8-this.selectedCol))+(this.selectedRow+1)+' '+trans('TO')+' '+String.fromCharCode(96 + (8-curCol))+(curRow+1)+'</span>');
		} else {
			$("#moves-list").prepend('<span class="list-group-item">'+before_promotion.toSymbol()+' '+(castling ? trans('CASTLED') : trans('MOVED'))+' '+trans('FROM')+' '+String.fromCharCode(97 + this.selectedCol)+(8-this.selectedRow)+' '+trans('TO')+' '+String.fromCharCode(97 + curCol)+(8-curRow)+'</span>');
		}
	
		if (orig_piece) {
			$("#moves-list").prepend('<span class="list-group-item action">'+before_promotion.toSymbol()+' '+trans('TAKEN')+' '+orig_piece.toSymbol()+'</span>');
		} else if (en_passant) {
			$("#moves-list").prepend('<span class="list-group-item action">'+before_promotion.toSymbol()+' '+trans('EN_PASSANT')+' '+en_passant_taken_piece.toSymbol()+'</span>');
		}
	
		if (promotion) {
			$("#moves-list").prepend('<span class="list-group-item action">'+before_promotion.toSymbol()+' '+trans('PROMOTED')+' '+piece.toSymbol()+'</span>');
		}
	
		CHESS_APP.waiting = false
	
	}
	
	if (user) {
		if (!CHESS_APP.waiting) {
			if (orig_piece) {
				playSound(SOUND_CAPTURE);
			} else {
				playSound(SOUND_MOVE);
			}
	
			$('#board-overlay').fadeIn();
			
			$.ajax({
				url: "/g/"+CHESS_APP.game_id+"/move",
				type: "POST",
				data: { "move": String.fromCharCode(97 + this.selectedCol)+(8-this.selectedRow)+String.fromCharCode(97 + curCol)+(8-curRow) }
			}).fail(function(jqXHR, textStatus) {
				console.log("move fail");
			});
		}
	} else {
		if (orig_piece) {
			playSound(SOUND_CAPTURE_2);
		} else {
			playSound(SOUND_MOVE_2);
		}
	}
	
}

// ------------------------------------
// Helpers
// ------------------------------------

function pareseMove(moveStr) {			
	row0 = 8-moveStr[1]
	col0 = moveStr[0].charCodeAt()-97
	row1 = 8-moveStr[3]
	col1 = moveStr[2].charCodeAt()-97
	return [[row0, col0], [row1, col1]]
}

function checkGameOver() {
	if (CHESS_APP.data.hints.length <= 0) {
		CHESS_APP.gameover = true;
		
		$('#board-waiting').hide();
		$('#board-gameover').show();
		$('#board-overlay').fadeIn();
		
		if ((!CHESS_APP.isBlack && CHESS_APP.data.w_check) || (CHESS_APP.isBlack && CHESS_APP.data.b_check)) {
			$('#board-gameover-text').text(trans('BLACK_WON'));
		} else if ((!CHESS_APP.isBlack && CHESS_APP.data.b_check) || (CHESS_APP.isBlack && CHESS_APP.data.w_check)) {
			$('#board-gameover-text').text(trans('WHITE_WON'));
		} else {
			$('#board-gameover-text').text(trans('DRAW'));
		}
	}
	
	return CHESS_APP.gameover;
}

function playSound(sound) {
	if (CHESS_APP.sounds) { sound.play(); }
}

function trans(str) {
	return STRINGS[CHESS_APP.lang || 'cs_CZ'][str];
}

// ------------------------------------
// Sockets
// ------------------------------------

function openSocket(token) {
    var channel = new goog.appengine.Channel(token);
    var socket = channel.open();
    socket.onmessage = function(message) {
		var json = $.parseJSON(message.data);
		if (json.hasOwnProperty('type')) {
			processMessage(json);
		} else {
			processMove(json);
		}
    };
    socket.onerror = function(error) {
		console.log("socket onerror: "+JSON.stringify(error));
		if (error.code == 401) {
			$.ajax({
				url: "/g/"+CHESS_APP.game_id+"/resetToken",
				type: "GET"
			})
			.done(function(json) {
				openSocket(json.token);
			})
			.fail(function(jqXHR, textStatus) {
				console.log("resetToken fail");
			});
		} else {
			console.log('socket error: '+error.description);
		}
    };
}

function processMessage(json) {
	if (json.type == 'chat') {
		var date = new Date();
		$('#chat-history-table').append('<tr><td>'+date.getHours()+':'+pad(date.getMinutes(), 2)+'</td><td><span class="player-label player-label-'+(CHESS_APP.isBlack ? 'white' : 'black')+'">'+(CHESS_APP.isBlack ? trans('WHITE') : trans('BLACK'))+'</span>: '+json.content+'</td></tr>');
	} else if (json.type == 'call') {
		if (navigator.getUserMedia) {
			$('#call-btn').hide();
			$('#video video').show();
			
			navigator.getUserMedia({video: true}, function(stream) {			
				$('#userVideo').prop('src', URL.createObjectURL(stream));
				window.localStream = stream;
				var call = peer.call(json.content, window.localStream);
				answerCall(call);
			}, function(error) {
				console.error('GUM Error: ', error);
			});
		}
	}	
}

function processMove(json) {
	if (json) {
		
		CHESS_APP.data.opponent_played = true
		CHESS_APP.waiting = false
		CHESS_APP.data.hints = json.hints
		CHESS_APP.data.w_check = json.w_check
		CHESS_APP.data.b_check = json.b_check
	
		var player1color = CHESS_APP.board.isBlack ? trans('BLACK') : trans('WHITE')
		var player1color2 = CHESS_APP.board.isBlack ? trans('TO_BLACK') : trans('TO_WHITE')
		var player2color = CHESS_APP.board.isBlack ? trans('WHITE') : trans('BLACK')
		var player2color2 = CHESS_APP.board.isBlack ? trans('TO_WHITE') : trans('TO_BLACK')
		
 		if (json.move != null && json.b_check) {
			playSound(SOUND_CHECK);
			$("#moves-list").prepend('<span class="list-group-item important">'+player1color+' '+trans('GAVE')+' '+player2color2+' '+trans('CHECK')+'!</span>');
		}
	
		if (json.move) {
			msg = json.move
			row0 = 8-msg[1]
			col0 = msg[0].charCodeAt()-97
			row1 = 8-msg[3]
			col1 = msg[2].charCodeAt()-97
			CHESS_APP.board.selectedRow = row0;
			CHESS_APP.board.selectedCol = col0;
			CHESS_APP.board.move(row1, col1, false);
		}
	
		if (json.move == null) {
			playSound(SOUND_WIN);
			$("#moves-list").prepend('<span class="list-group-item important">'+player1color+' '+trans('GAVE')+' '+player2color2+' '+trans('CHECKMATE')+'!</span>');
			$("#moves-list").prepend('<span class="list-group-item"><em>'+trans('GAME_OVER')+'</em></span>');
		} else if (CHESS_APP.data.hints.length <= 0) {
			playSound(SOUND_LOSS);
			$("#moves-list").prepend('<span class="list-group-item important">'+player2color+' '+trans('GAVE')+' '+player1color2+' '+trans('CHECKMATE')+'!</span>');
			$("#moves-list").prepend('<span class="list-group-item"><em>'+trans('GAME_OVER')+'</em></span>');
		}
	
 		if (json.move != null && CHESS_APP.data.hints.length > 0 && json.w_check) {
			playSound(SOUND_CHECK_2);
			$("#moves-list").prepend('<span class="list-group-item important">'+player2color+' '+trans('GAVE')+' '+player1color2+' '+trans('CHECK')+'!</span>');
		}
		
		if (!checkGameOver()) {
			$('#board-overlay').fadeOut();
		}
		
	} else {
		console.log("fail");
	}
}

// ------------------------------------
// Handlers
// ------------------------------------

Board.prototype.cellClicked = function(cell) {
    var col = cell.parent().children().index(cell)-1;
    var row = cell.parent().parent().children().index(cell.parent())-1;
	
	$('.selected-piece').removeClass('selected-piece');
	
	if (cell.hasClass('hint') || cell.hasClass('enemy_hint')) {
		CHESS_APP.board.move(row, col, true);
	} else {
		$('.hint').removeClass('hint');
		$('.castling').removeClass('castling');
		$('.enemy_hint').removeClass('enemy_hint');
		
		if (!(row == CHESS_APP.board.selectedRow && col == CHESS_APP.board.selectedCol)) {
			CHESS_APP.board.startMove(row, col);
		} else {
			CHESS_APP.board.selectedRow = -1, CHESS_APP.board.selectedCol = -1;
		}
	}
}

// ------------------------------------
// Board resizing, WebRTC
// ------------------------------------

function resizeBoard() {
	$('#smallOverlay').hide();
	var width = $(window).width() - 520;
	var height = $(window).height() - 70;
	var size = Math.min(width, height);
	if (size < 200) {
		$('#smallOverlay').show();
	} else {
		$('#boardContainer').css('width', size);
		$('#boardContainer').css('height', size);
		$('#boardContainer').css('margin-top', -(size/2)+25);
		$('#boardContainer').css('margin-left', -(size/2));
		$('#boardContainer').css('font-size', size/16);
	}
}

$(window).resize(function() {
	resizeBoard();
});

// ------------------------------------
// Chat
// ------------------------------------

function pad(num, size) {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
}

$('#chat-send-btn').click(function() {
	var text = $('#chat-input').val();
	$('#chat-input').val('');
	var date = new Date();
	$('#chat-history-table').append('<tr><td>'+date.getHours()+':'+pad(date.getMinutes(), 2)+'</td><td><span class="player-label player-label-'+(CHESS_APP.isBlack ? 'black' : 'white')+'">'+(CHESS_APP.isBlack ? trans('BLACK') : trans('WHITE'))+'</span>: '+text+'</td></tr>');
	
	$.ajax({
		url: "/g/"+CHESS_APP.game_id+"/send",
		type: "POST",
		data: { "msgType": "chat", "msgContent": text }
	}).fail(function(jqXHR, textStatus) {
		console.log("send fail");
	});
	
});

// ------------------------------------
// Video
// ------------------------------------

navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia;

var peer = new Peer({ key: 'lwjd5qra8257b9', debug: 3});

peer.on('open', function(){
	console.log('Peer ID: ', peer.id);
});

peer.on('call', function(call) {
	call.answer(window.localStream);
	answerCall(call);
});

peer.on('error', function(err) {
	console.error('Peer Error: ', err);
});

$('#call-btn').click(function(){
	$('#call-btn').hide();
	$('#video video').show();
	makeCall();
});

function setupCall() {
	if (navigator.getUserMedia) {
		$('#video').show();
		$('#video video').hide();
		$('#chat').css('height', '-webkit-calc(100% - 340px)');
	}
}

function makeCall() {
	navigator.getUserMedia({video: true}, function(stream) {			
		$('#userVideo').prop('src', URL.createObjectURL(stream));
		window.localStream = stream;
		
		$.ajax({
			url: "/g/"+CHESS_APP.game_id+"/send",
			type: "POST",
			data: { "msgType": "call", "msgContent": peer.id }
		}).fail(function(jqXHR, textStatus) {
			console.log("send fail");
		});
		
	}, function(error) {
		console.error('GUM Error: ', error);
	});
}

function answerCall(call) {
	if (window.existingCall) {
		window.existingCall.close();
	}
	
	call.on('stream', function(stream){
		$('#userVideo2').prop('src', URL.createObjectURL(stream));
	});
	
	window.existingCall = call;
}

// ------------------------------------
// Initialization
// ------------------------------------

$(function() {
	resizeBoard();
	setupCall();
});
