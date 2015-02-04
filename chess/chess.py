#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
chess.py

Created by Alex Studnicka on 2014-11-27.
Copyright (c) 2013 Alex Studnicka. All rights reserved.
"""

from __future__ import print_function
import sys
from itertools import count
from collections import Counter, OrderedDict, namedtuple

TABLE_SIZE		= 5e4
NODES_SEARCHED	= 5e2
MATE_VALUE		= 1e99

A1, H1, A8, H8	= 91, 98, 21, 28
initial			= '         \n         \n rnbqkbnr\n pppppppp\n ........\n ........\n ........\n ........\n PPPPPPPP\n RNBQKBNR\n         \n          '

# Move and evaluation tables

N, E, S, W = -10, 1, 10, -1
directions = {
    'P': (N, 2*N, N+W, N+E),
    'N': (2*N+E, N+2*E, S+2*E, 2*S+E, 2*S+W, S+2*W, N+2*W, 2*N+W),
    'B': (N+E, S+E, S+W, N+W),
    'R': (N, E, S, W),
    'Q': (N, E, S, W, N+E, S+E, S+W, N+W),
    'K': (N, E, S, W, N+E, S+E, S+W, N+W)
}

pst = {
    'P': (0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 198, 198, 198, 198, 198, 198, 198, 198, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 178, 198, 208, 218, 218, 208, 198, 178, 0,
        0, 178, 198, 218, 238, 238, 218, 198, 178, 0,
        0, 178, 198, 208, 218, 218, 208, 198, 178, 0,
        0, 178, 198, 198, 198, 198, 198, 198, 178, 0,
        0, 198, 198, 198, 198, 198, 198, 198, 198, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'B': (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 797, 824, 817, 808, 808, 817, 824, 797, 0,
        0, 814, 841, 834, 825, 825, 834, 841, 814, 0,
        0, 818, 845, 838, 829, 829, 838, 845, 818, 0,
        0, 824, 851, 844, 835, 835, 844, 851, 824, 0,
        0, 827, 854, 847, 838, 838, 847, 854, 827, 0,
        0, 826, 853, 846, 837, 837, 846, 853, 826, 0,
        0, 817, 844, 837, 828, 828, 837, 844, 817, 0,
        0, 792, 819, 812, 803, 803, 812, 819, 792, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'N': (0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 627, 762, 786, 798, 798, 786, 762, 627, 0,
        0, 763, 798, 822, 834, 834, 822, 798, 763, 0,
        0, 817, 852, 876, 888, 888, 876, 852, 817, 0,
        0, 797, 832, 856, 868, 868, 856, 832, 797, 0,
        0, 799, 834, 858, 870, 870, 858, 834, 799, 0,
        0, 758, 793, 817, 829, 829, 817, 793, 758, 0,
        0, 739, 774, 798, 810, 810, 798, 774, 739, 0,
        0, 683, 718, 742, 754, 754, 742, 718, 683, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'R': (0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 1258, 1263, 1268, 1272, 1272, 1268, 1263, 1258, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'Q': (0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 2529, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'K': (0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 60098, 60132, 60073, 60025, 60025, 60073, 60132, 60098, 0,
        0, 60119, 60153, 60094, 60046, 60046, 60094, 60153, 60119, 0,
        0, 60146, 60180, 60121, 60073, 60073, 60121, 60180, 60146, 0,
        0, 60173, 60207, 60148, 60100, 60100, 60148, 60207, 60173, 0,
        0, 60196, 60230, 60171, 60123, 60123, 60171, 60230, 60196, 0,
        0, 60224, 60258, 60199, 60151, 60151, 60199, 60258, 60224, 0,
        0, 60287, 60321, 60262, 60214, 60214, 60262, 60321, 60287, 0,
        0, 60298, 60332, 60273, 60225, 60225, 60273, 60332, 60298, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
}

# Chess logic

class Position(namedtuple('Position', 'board score wc bc ep kp')):
    @classmethod
    def initialPos(cls):
        return cls(initial, 0, (True,True), (True,True), 0, 0)
	
    @classmethod
    def fromJSON(cls, json):
        return cls(json[0], json[1], (json[2][0], json[2][1]), (json[3][0], json[3][1]), json[4], json[5])
	
    def genMoves(self):
        for i, p in enumerate(self.board):
            if not p.isupper(): continue
            for d in directions[p]:
                for j in count(i+d, d):
                    q = self.board[j]
					
                    if self.board[j].isspace(): break
					
                    if i == A1 and q == 'K' and self.wc[0]: yield (j, j-2)
                    if i == H1 and q == 'K' and self.wc[1]: yield (j, j+2)
					
                    if q.isupper(): break
					
                    if p == 'P' and d in (N+W, N+E) and q == '.' and j not in (self.ep, self.kp): break
                    if p == 'P' and d in (N, 2*N) and q != '.': break
                    if p == 'P' and d == 2*N and (i < A1+N or self.board[i+N] != '.'): break
					
                    yield (i, j)
					
                    if p in ('P', 'N', 'K'): break
					
                    if q.islower(): break

    def rotate(self):
        return Position(
            self.board[::-1].swapcase(), -self.score,
            self.bc, self.wc, 119-self.ep, 119-self.kp)

    def move(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
        put = lambda board, i, p: board[:i] + p + board[i+1:]
		
        board = self.board
        wc, bc, ep, kp = self.wc, self.bc, 0, 0
        score = self.score + self.value(move)
		
        board = put(board, j, board[i])
        board = put(board, i, '.')
		
        if i == A1: wc = (False, wc[1])
        if i == H1: wc = (wc[0], False)
        if j == A8: bc = (bc[0], False)
        if j == H8: bc = (False, bc[1])
		
        if p == 'K':
            wc = (False, False)
            if abs(j-i) == 2:
                kp = (i+j)//2
                board = put(board, A1 if j < i else H1, '.')
                board = put(board, kp, 'R')
		
        if p == 'P':
            if A8 <= j <= H8:
                board = put(board, j, 'Q')
            if j - i == 2*N:
                ep = i + N
            if j - i in (N+W, N+E) and q == '.':
                board = put(board, j+S, '.')
        return Position(board, score, wc, bc, ep, kp).rotate()

    def value(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
		
        score = pst[p][j] - pst[p][i]
		
        if q.islower():
            score += pst[q.upper()][j]
		
        if abs(j-self.kp) < 2:
            score += pst['K'][j]
		
        if p == 'K' and abs(i-j) == 2:
            score += pst['R'][(i+j)//2]
            score -= pst['R'][A1 if j < i else H1]
		
        if p == 'P':
            if A8 <= j <= H8:
                score += pst['Q'][j] - pst['P'][j]
            if j == self.ep:
                score += pst['P'][j+S]
        return score

    def in_check(self, player):
        for i, p in enumerate(self.board):
            if p ==player:
                for m in ('R','B','N','K'):
                    for d in directions[m]:
                        for j in count(i+d, d):
                            q = self.board[j]
                            if self.board[j].isspace(): break

                            if q!='.':
                                if (q.islower()==player.islower()): break
								
                                if (q.upper()== str(m)) or (q.upper() == 'Q' and m in ('R','B')):
                                    return True
                                if (str(m)=='K') and (d in (S+E, S+W)) and (q.upper()=='P'):
                                    return True
                                
                                else: break
                            
                            if m in ('P', 'N', 'K'): break
                                
                return False

Entry = namedtuple('Entry', 'depth score gamma move')
tp = OrderedDict()

# Search logic

nodes = 0
def bound(pos, gamma, depth):
    global nodes; nodes += 1
	
    entry = tp.get(pos)
    if entry is not None and entry.depth >= depth and (
            entry.score < entry.gamma and entry.score < gamma or
            entry.score >= entry.gamma and entry.score >= gamma):
        return entry.score
	
    if abs(pos.score) >= MATE_VALUE:
        return pos.score
	
    nullscore = -bound(pos.rotate(), 1-gamma, depth-3) if depth > 0 else pos.score
	
    if nullscore >= gamma:
        return nullscore
	
    best, bmove = -3*MATE_VALUE, None
    for move in sorted(pos.genMoves(), key=pos.value, reverse=True):
        if not pos.move(move).in_check('k'):
            if depth <= 0 and pos.value(move) < 150:
                break
            score = -bound(pos.move(move), 1-gamma, depth-1)
            if score > best:
                best = score
                bmove = move
            if score >= gamma:
                break
    
    if depth <= 0 and best < nullscore:
        return nullscore
	
    if depth > 0 and best <= -MATE_VALUE is None and nullscore > -MATE_VALUE:
        best = 0
	
    if entry is None or depth >= entry.depth and best >= gamma:
        tp[pos] = Entry(depth, best, gamma, bmove)
        if len(tp) > TABLE_SIZE:
            tp.popitem()
    return best

def search(pos, maxn=NODES_SEARCHED):
    global nodes; nodes = 0
	
    for depth in range(1, 99):
        lower, upper = -3*MATE_VALUE, 3*MATE_VALUE
        while lower < upper - 3:
            gamma = (lower+upper+1)//2
            score = bound(pos, gamma, depth)
            if score >= gamma:
                lower = score
            if score < gamma:
                upper = score
        
        if nodes >= maxn or abs(score) >= MATE_VALUE:
            break
	
    entry = tp.get(pos)
    if entry is not None:
        return entry.move, score
    return None, score

def parse(c):
    fil, rank = ord(c[0]) - ord('a'), int(c[1]) - 1
    return A1 + fil - 10*rank

def parseMove(c):
    return parse(c[0:2]), parse(c[2:4])

def render(i):
    rank, fil = divmod(i - A1, 10)
    return chr(fil + ord('a')) + str(-rank + 1)

def renderMove(i):
    return render(i[0])+render(i[1])

def rotateMove(i):
    return H8-(i[0]-A1), H8-(i[1]-A1)
