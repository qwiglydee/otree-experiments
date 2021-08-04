import time

from otree import settings
from otree.api import *

from .image_utils import encode_image

doc = """
Real-effort tasks. The different tasks are available in task_matrix.py, task_transcription.py, etc.
You can delete the ones you don't need. 
"""


def get_task_module(player):
    """
    This function is only needed for demo mode, to demonstrate all the different versions.
    You can simplify it if you want.
    """
    from . import task_matrix, task_transcription, task_decoding

    session = player.session
    task = session.config.get("task")
    if task == "matrix":
        return task_matrix
    if task == "transcription":
        return task_transcription
    if task == "decoding":
        return task_decoding
    # default
    return task_matrix


class Constants(BaseConstants):
    name_in_url = "transcription"
    players_per_group = None
    num_rounds = 1

    instructions_template = __name__ + "/instructions.html"
    captcha_length = 3


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    session = subsession.session
    defaults = dict(retry_delay=1.0, puzzle_delay=1.0, attempts_per_puzzle=1)
    session.ret_params = {}
    for param in defaults:
        session.ret_params[param] = session.config.get(param, defaults[param])


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)
    num_trials = models.IntegerField(initial=0)
    num_correct = models.IntegerField(initial=0)
    num_failed = models.IntegerField(initial=0)


# puzzle-specific stuff


class Puzzle(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)
    iteration = models.IntegerField(initial=0)
    attempts = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)
    # can be either simple text, or a json-encoded definition of the puzzle, etc.
    text = models.LongStringField()
    # solution may be the same as text, if it's simply a transcription task
    solution = models.LongStringField()
    response = models.LongStringField()
    response_timestamp = models.FloatField()
    is_correct = models.BooleanField()


def generate_puzzle(player: Player) -> Puzzle:
    """Create new puzzle for a player"""
    task_module = get_task_module(player)
    fields = task_module.generate_puzzle_fields()
    player.iteration += 1
    return Puzzle.create(
        player=player, iteration=player.iteration, timestamp=time.time(), **fields
    )


def get_current_puzzle(player):
    puzzles = Puzzle.filter(player=player, iteration=player.iteration)
    if puzzles:
        [puzzle] = puzzles
        return puzzle


def encode_puzzle(puzzle: Puzzle):
    """Create data describing puzzle to send to client"""
    task_module = get_task_module(puzzle.player)  # noqa
    # generate image for the puzzle
    image = task_module.render_image(puzzle)
    data = encode_image(image)
    return dict(image=data)


def get_progress(player: Player):
    """Return current player progress"""
    return dict(
        num_trials=player.num_trials,
        num_correct=player.num_correct,
        num_incorrect=player.num_failed,
        iteration=player.iteration,
    )


def play_game(player: Player, data: dict):
    """Main game workflow
    Implemented as reactive scheme: receive message from vrowser, react, respond.

    Generic game workflow, from server point of view:
    - receive: {} -- empty message means page loaded
    - check if it's game start or page refresh midgame
    - respond: {'puzzle': null, 'progress': ...} -- inidcates no current puzzle and a progress
    - respond: {'puzzle': data, 'progress': ...} -- in case of midgame page reload

    - receive: {'next': true} -- request for a next/first puzzle
    - generate new puzzle
    - respond: {'puzzle': data 'progress': ...}

    - receive: {'answer': ...} -- user answered the puzzle
    - check if the answer is correct
    - respond: {'feedback': true|false, 'progress': ...} -- feedback to the answer

    If allowed by config `attempts_pre_puzzle`, client can send more 'answer' messages
    When done solving, client should explicitely request next puzzle by sending 'next' message
    """
    session = player.session
    my_id = player.id_in_group
    ret_params = session.ret_params
    task_module = get_task_module(player)

    now = time.time()
    # the current puzzle or none
    current = get_current_puzzle(player)

    if "cheat" in data and settings.DEBUG:
        return {my_id: dict(solution=current.solution)}

    # page loaded
    if data == {}:
        p = get_progress(player)
        if current:
            return {my_id: dict(puzzle=encode_puzzle(current), progress=p)}
        else:
            return {my_id: dict(puzzle=None, progress=p)}

    # client requested new puzzle
    if "next" in data:
        if current is not None:
            if current.response is None:
                raise RuntimeError("trying to skip over unsolved puzzle")
            if now < current.timestamp + ret_params["puzzle_delay"]:
                raise RuntimeError("retrying too fast")

        # generate new puzzle
        z = generate_puzzle(player)
        p = get_progress(player)
        return {my_id: dict(puzzle=encode_puzzle(z), progress=p)}

    # client gives an answer to current puzzle
    if "answer" in data:
        if current is None:
            raise RuntimeError("trying to answer no puzzle")

        if current.response is not None:  # it's a retry
            if current.attempts >= ret_params["attempts_per_puzzle"]:
                raise RuntimeError("no more attempts allowed")
            if now < current.response_timestamp + ret_params["retry_delay"]:
                raise RuntimeError("retrying too fast")

            # undo last updation of player progress
            player.num_trials -= 1
            if current.is_correct:
                player.num_correct -= 1
            else:
                player.num_failed -= 1

        # check answer
        answer = data["answer"]

        if answer == "" or answer is None:
            raise ValueError("bogus answer")

        current.response = answer
        current.is_correct = task_module.is_correct(answer, current)
        current.response_timestamp = now
        current.attempts += 1

        # update player progress
        if current.is_correct:
            player.num_correct += 1
        else:
            player.num_failed += 1
        player.num_trials += 1

        retries_left = ret_params["attempts_per_puzzle"] - current.attempts
        p = get_progress(player)
        return {
            my_id: dict(
                feedback=current.is_correct, retries_left=retries_left, progress=p
            )
        }

    raise RuntimeError("unrecognized message from client")


class Game(Page):
    timeout_seconds = 60

    live_method = play_game

    @staticmethod
    def js_vars(player: Player):
        return player.session.ret_params

    @staticmethod
    def vars_for_template(player: Player):
        return dict(DEBUG=settings.DEBUG)

    @staticmethod
    def error_message(player: Player, values):
        # this prevents users from moving forward before a timeout occurs.
        # if your game allows players to advance before a timeout,
        # you should remove this.
        return "Game is not complete"


class Results(Page):
    pass


page_sequence = [Game, Results]
