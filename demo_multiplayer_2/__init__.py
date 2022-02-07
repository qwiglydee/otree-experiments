import re

from otree.api import *

from common.live_utils import live_multiplayer

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = "demo_tictactoe"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1

    CHAR_EMPTY = "•"
    PLAYER_X_ROLE = "x"
    PLAYER_O_ROLE = "o"

    POST_TRIAL_PAUSE = 5


# players' turns order 
NEXT_PLAYER = {
    C.PLAYER_X_ROLE: C.PLAYER_O_ROLE, 
    C.PLAYER_O_ROLE: C.PLAYER_X_ROLE
}


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    active_player = models.StringField()


class Player(BasePlayer):
    num_moves = models.IntegerField(initial=0)
    is_winner = models.BooleanField(initial=False)


class Trial(ExtraModel):
    group = models.Link(Group)
    is_completed = models.BooleanField()

    board = models.StringField(initial=C.CHAR_EMPTY * 9)
    winner = models.StringField()


def put_mark(game: Trial, pos: int, role: str):
    board = list(game.board)
    board[pos] = role
    game.board = "".join(board)


WINNING_PATTERNS = ( # regexps
    "@@@......",
    "...@@@...",
    "......@@@",
    "@..@..@..",
    ".@..@..@.",
    "..@..@..@",
    "@...@...@",
    "..@.@.@..",
)


def validate_game(game: Trial):
    def check(mark):
        brd = game.board.replace(mark, '@')
        win = list(filter(lambda wp: re.match(wp, brd), WINNING_PATTERNS))
        return win[0] if len(win) else None

    full = game.board.count(C.CHAR_EMPTY) == 0

    winning = check(C.PLAYER_X_ROLE)
    if winning:
        return C.PLAYER_X_ROLE, winning, full
    
    winning = check(C.PLAYER_O_ROLE)
    if winning:
        return C.PLAYER_O_ROLE, winning, full

    return None, None, full


def creating_session(subsession: Subsession):
    # initialize games for groups
    for group in subsession.get_groups():
        Trial.create(group=group, board=C.CHAR_EMPTY * 9)
        group.active_player = C.PLAYER_X_ROLE


# PAGES

@live_multiplayer
class Game(Page):
    trial_model = Trial

    @staticmethod
    def js_vars(player):
        return dict(
            role=player.role,
            post_trial_pause=C.POST_TRIAL_PAUSE
        )

    @staticmethod
    def encode_trial(game: Trial):
        return dict(
            board=list(game.board),
            winpattern=[]
        )

    @staticmethod
    def get_status(game: Trial, player: Player):
        if game.is_completed:
            return dict(
                gameOver=True,
                trialCompleted=True,
                trialSuccessful=(player.role == game.winner) if game.winner else None,
                playerActive=None
            )
        else:
            return dict(
                playerActive=(player.role == game.group.active_player)
            )

    @staticmethod
    def validate_response(game: Trial, player: Player, response, timeout_happened):
        if timeout_happened:
            raise NotImplementedError()

        if player.role != game.group.active_player:
            raise RuntimeError("Wrong turn")

        pos = response["action"]
        mark = player.role

        if game.board[pos] != C.CHAR_EMPTY:
            return dict(feedback=dict(responseCorrect=False))

        player.num_moves += 1

        put_mark(game, pos, mark)
        winner, winpattern, full = validate_game(game)
        game.is_completed = full or winner is not None

        if game.is_completed:
            game.group.active_player = None
            if winner:
                game.winner = winner
                player.is_winner = True
            
            return dict(
                feedback=dict(responseCorrect=True, responseFinal=True), 
                update={"board": list(game.board), "winpattern": list(winpattern) if winpattern else []}
            )

        game.group.active_player = NEXT_PLAYER[game.group.active_player]

        return dict(
            feedback=dict(responseCorrect=True), 
            update={f"board.{pos}": mark}
            )


page_sequence = [Game]
