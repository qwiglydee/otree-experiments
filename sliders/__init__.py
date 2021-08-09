import time
import json

from otree import settings
from otree.api import *

from .image_utils import encode_image
from . import task_sliders

doc = """
"""


class Constants(BaseConstants):
    name_in_url = "sliders"
    players_per_group = None
    num_rounds = 1

    instructions_template = __name__ + "/instructions.html"


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    session = subsession.session
    defaults = dict(
        trial_delay=1.0,
        num_sliders=5,
        num_iterations=3,
    )
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

    # slider parameters json encoded
    data = models.LongStringField()
    # solution values json encoded
    solution = models.LongStringField()
    # submited sliders absolute pixel values, json encoded
    response = models.LongStringField()

    response_timestamp = models.FloatField()
    is_correct = models.BooleanField()


def generate_puzzle(player: Player) -> Puzzle:
    """Create new puzzle for a player"""
    fields = task_sliders.generate_puzzle_fields(player.session.ret_params['num_sliders'])
    player.iteration += 1
    solution = fields.pop('solution')
    return Puzzle.create(
        player=player, iteration=player.iteration, timestamp=time.time(),
        data=json.dumps(fields),
        solution=json.dumps(solution),
    )


def get_current_puzzle(player):
    puzzles = Puzzle.filter(player=player, iteration=player.iteration)
    if puzzles:
        [puzzle] = puzzles
        return puzzle


def encode_puzzle(puzzle: Puzzle):
    """Create data describing puzzle to send to client"""
    puzzle_data = json.loads(puzzle.data)
    # generate image for the puzzle
    image = task_sliders.render_image(puzzle)
    return dict(
        image=encode_image(image),
        size=puzzle_data['size'],
        coords=puzzle_data['coords'],
        initial=puzzle_data['initial'],
    )


def get_progress(player: Player):
    """Return current player progress"""
    return dict(
        num_trials=player.num_trials,
        num_correct=player.num_correct,
        num_incorrect=player.num_failed,
        iteration=player.iteration,
    )


def play_game(player: Player, message: dict):
    """Main game workflow
    Implemented as reactive scheme: receive message from vrowser, react, respond.

    Generic game workflow, from server point of view:
    - receive: {'type': 'load'} -- empty message means page loaded
    - check if it's game start or page refresh midgame
    - respond: {'type': 'status', 'progress': ...}
    - respond: {'type': 'status', 'progress': ..., 'puzzle': data} -- in case of midgame page reload

    - receive: {'type': 'next'} -- request for a next/first puzzle
    - generate new puzzle
    - respond: {'type': 'puzzle', 'puzzle': data}

    - receive: {'type': 'values', 'values': ...} -- submitted values of sliders
    - check if the answer is correct
    - respond: {'type': 'feedback', 'is_correct': ...} -- feedback to the values, list of true|false

    When done solving, client should explicitely request next puzzle by sending 'next' message

    Field 'progress' is added to all server responses to indicate it on page.
    """
    session = player.session
    my_id = player.id_in_group
    ret_params = session.ret_params

    now = time.time()
    # the current puzzle or none
    current = get_current_puzzle(player)

    message_type = message['type']

    # page loaded
    if message_type == 'load':
        p = get_progress(player)
        if current:
            return {
                my_id: dict(type='status', progress=p, puzzle=encode_puzzle(current))
            }
        else:
            return {my_id: dict(type='status', progress=p)}

    if message_type == "cheat" and settings.DEBUG:
        return {my_id: dict(type='solution', solution=json.loads(current.solution))}

    # client requested new puzzle
    if message_type == "next":
        if current is not None:
            if current.response is None:
                raise RuntimeError("trying to skip over unsolved puzzle")
            if current.iteration == ret_params['num_iterations']:
                return {
                    my_id: dict(
                        type='status', progress=get_progress(player), iterations_left=0
                    )
                }
        player.num_trials += 1

        # generate new puzzle
        z = generate_puzzle(player)
        p = get_progress(player)

        return {my_id: dict(type='puzzle', puzzle=encode_puzzle(z), progress=p)}

    if message_type == "values":
        if current is None:
            raise RuntimeError("trying to answer no puzzle")

        response = message["values"]

        if response == "" or response is None:
            raise ValueError("bogus response")

        current.response = json.dumps(response)
        is_correct = task_sliders.is_correct(response, current)
        current.response_timestamp = now

        p = get_progress(player)
        return {
            my_id: dict(
                type='feedback',
                is_correct=is_correct,
                progress=p,
            )
        }

    raise RuntimeError("unrecognized message from client")


class Game(Page):
    timeout_seconds = 600

    live_method = play_game

    @staticmethod
    def js_vars(player: Player):
        return dict(
            params=player.session.ret_params,
            slider_step=task_sliders.SLIDER_STEP,
            slider_size=task_sliders.SLIDER_BBOX,
        )

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            params=player.session.ret_params,
            DEBUG=settings.DEBUG
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if not timeout_happened and not player.session.ret_params['num_iterations']:
            raise RuntimeError("malicious page submission")


class Results(Page):
    pass


page_sequence = [Game, Results]
