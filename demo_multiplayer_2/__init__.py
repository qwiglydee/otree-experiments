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


WINNING_PATTERNS = (
    "+++------",
    "---+++---",
    "------+++",
    "+--+--+--",
    "-+--+--+-",
    "--+--+--+",
    "+---+---+",
    "--+-+-+--",
)


def validate_game(game: Trial):
    pattern = game.board.replace(C.CHAR_EMPTY, '-')
    full = pattern.count('-') == 9

    x_pattern = pattern.replace(C.PLAYER_X_ROLE, "+").replace(C.PLAYER_O_ROLE, "-")
    if x_pattern in WINNING_PATTERNS:
        return C.PLAYER_X_ROLE, x_pattern, full

    o_pattern = pattern.replace(C.PLAYER_O_ROLE, "+").replace(C.PLAYER_X_ROLE, "-")
    if o_pattern in WINNING_PATTERNS:
        return C.PLAYER_O_ROLE, o_pattern, full

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
                trialSuccessful=(player.role == game.winner),
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
                update={"board": list(game.board), "winpattern": list(winpattern)}
            )

        game.group.active_player = NEXT_PLAYER[game.group.active_player]

        return dict(
            feedback=dict(responseCorrect=True), 
            update={f"board.{pos}": mark}
            )


page_sequence = [Game]
