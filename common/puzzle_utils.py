"""Module to hadnle N-puzzles

A board is a flat array of length N^2 with integers 1..N and None for empty cell.

"""

import random
import itertools


# def pprintBoard(board):
#     return "\n".join([" ".join(["  " if d is None else f"{d: 2d}" for d in row]) for row in board])


def initBoard(size):
    total = size * size
    board = [i + 1 for i in range(total)]
    board[-1] = None
    return board


def getDirections(board, size, srcpos):
    """Returns coords of possible neighbours"""
    nbours = []

    r = srcpos // size
    c = srcpos % size

    def pos(r, c):
        return r * size + c

    if r > 0:
        nbours.append(pos(r - 1, c))
    if r < size - 1:
        nbours.append(pos(r + 1, c))
    if c > 0:
        nbours.append(pos(r, c - 1))
    if c < size - 1:
        nbours.append(pos(r, c + 1))

    return nbours


def findFreeCell(board):
    return board.index(None)


def moveCell(board, dst, src):
    board[dst] = board[src]
    board[src] = None


def shuffleBoard(board, size, num_moves):
    dst = board.index(None)
    src = None
    for i in range(num_moves):
        # get direction and exclude move previously moved
        nbours = [s for s in getDirections(board, size, dst) if s != src]
        src = random.choice(nbours)
        moveCell(board, dst, src)
        dst = src


def validateMove(board, size, dst, src):
    if board[dst] is not None:
        return False
    return src in getDirections(board, size, dst)


def applyMoves(board, size, moves):
    """Applies list of moves
    Each move is a pos of a cell to move into free
    """
    dst = board.index(None)
    for src in moves:
        if not validateMove(board, size, dst, src):
            raise ValueError("Invalid move")
        moveCell(board, dst, src)
        dst = src


def validateBoard(board):
    """Checks if all digits in order and last one is None"""
    return board[-1] is None and all([d == i + 1 for i, d in enumerate(board[:-1])])
