from email import iterators
from pathlib import Path
import random

from otree.api import *

from common.live_utils import live_puzzles

doc = """
Your app description
"""

WORKDIR = Path(__file__).parent


class C(BaseConstants):
    NAME_IN_URL = "demo_puzzles_local"
    PLAYERS_PER_GROUP = None
    INSTRUCTIONS = __name__ + "/instructions.html"
    NUM_ROUNDS = 1

    MATRIX_SIZE = 4
    MATRIX_LENGTH = MATRIX_SIZE ** 2
    CHAR_EMPTY = "•"
    CHAR_FILL = "●"

    GAME_TIMEOUT = 30

    DEFAULT_DIFFICULTY = 4
    DEFAULT_MAX_MOVES = 4
    DEFAULT_EXPOSURE_TIME = 2
    DEFAULT_POST_TRIAL_PAUSE = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    num_completed = models.IntegerField(initial=0)
    num_solved = models.IntegerField(initial=0)


class Puzzle(ExtraModel):
    player = models.Link(Player)
    iteration = models.IntegerField(initial=0)
    is_completed = models.BooleanField(initial=False)
    is_timeouted = models.BooleanField(initial=False)
    is_skipped = models.BooleanField(initial=False)
    is_successful = models.BooleanField(initial=None)

    target = models.StringField()
    difficulty = models.IntegerField()

    matrix = models.StringField()
    response_time = models.IntegerField()


def generate_puzzle(player, iteration, difficulty):
    empty = [C.CHAR_EMPTY] * C.MATRIX_LENGTH
    target = [C.CHAR_FILL] * difficulty + [C.CHAR_EMPTY] * (C.MATRIX_LENGTH - difficulty)
    random.shuffle(target)

    return Puzzle.create(
        player=player, iteration=iteration, difficulty=difficulty, target="".join(target), matrix="".join(empty)
    )


def fill_cell(puzzle: Puzzle, pos):
    matrix = list(puzzle.matrix)
    matrix[pos] = C.CHAR_FILL
    puzzle.matrix = "".join(matrix)


def validate_cell(puzzle: Puzzle, pos):
    if puzzle.matrix[pos] != C.CHAR_FILL:
        return None
    else:
        return puzzle.matrix[pos] == puzzle.target[pos]


def validate_puzzle(puzzle):
    """Returns bool if its solved and array of bool for each cell"""
    validated = [validate_cell(puzzle, i) for i in range(C.MATRIX_LENGTH)]
    return validated.count(True) == puzzle.difficulty, validated


def creating_session(subsession: Subsession):
    # override constants with session params
    session = subsession.session
    defaults = dict(
        post_trial_pause=C.DEFAULT_POST_TRIAL_PAUSE,
        exposure_time=C.DEFAULT_EXPOSURE_TIME,
        difficulty=C.DEFAULT_DIFFICULTY,
        max_moves=C.DEFAULT_MAX_MOVES,
    )
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])


# PAGES


@live_puzzles
class Game(Page):
    trial_model = Puzzle
    timeout_seconds = C.GAME_TIMEOUT

    @staticmethod
    def js_vars(player):
        params = player.session.params
        return dict(
            char_fill=C.CHAR_FILL,
            matrix_size=C.MATRIX_SIZE,
            matrix_length=C.MATRIX_LENGTH,
            post_trial_pause=params["post_trial_pause"],
            exposure_time=params["exposure_time"],
            max_moves=params["max_moves"],
        )

    @staticmethod
    def new_trial(player, iteration):
        return generate_puzzle(player, iteration, player.session.params["difficulty"])

    @staticmethod
    def encode_trial(puzzle: Puzzle):
        return dict(
            iteration=puzzle.iteration,
            target=list(puzzle.target),
            matrix=list(puzzle.matrix),
            validated=[None] * C.MATRIX_LENGTH,  # a field not stored in model
        )

    @staticmethod
    def validate_response(puzzle: Puzzle, response: dict, timeout_happened: bool):
        print("validating", puzzle, "\nresponse:", response)

        puzzle.matrix = "".join(response["solution"])

        moves_count = puzzle.matrix.count(C.CHAR_FILL)
        solved, validated = validate_puzzle(puzzle)

        puzzle.is_successful = solved
        puzzle.is_completed = True
        puzzle.is_skipped = moves_count == 0

        puzzle.player.num_completed += 1
        if solved:
            puzzle.player.num_solved += 1

        return dict(
            feedback=dict(responseCorrect=puzzle.is_successful, responseFinal=True),
            update=dict(validated=validated),
        )


page_sequence = [Game]
