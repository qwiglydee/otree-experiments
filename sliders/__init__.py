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
        num_iterations=3,
        num_sliders=48,
        num_columns=3
    )
    session.task_params = {}
    for param in defaults:
        session.task_params[param] = session.config.get(param, defaults[param])


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)
    num_trials = models.IntegerField(initial=0)
    num_solved = models.IntegerField(initial=0)
    num_failed = models.IntegerField(initial=0)


# puzzle-specific stuff


class Puzzle(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)
    iteration = models.IntegerField(initial=0)
    attempts = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    # slider puzzle parameters json encoded
    data = models.LongStringField()
    # solution values json encoded list
    solution = models.LongStringField()
    # initial or submited values, json encoded list
    values = models.LongStringField()

    # timestamp of last response
    response_timestamp = models.FloatField()
    # number of correct sliders
    correct = models.IntegerField()
    # if all sliders solved
    solved = models.BooleanField()


def generate_puzzle(player: Player) -> Puzzle:
    """Create new puzzle for a player"""
    data = task_sliders.generate_puzzle(player.session.task_params)
    solution = data.pop('solution')
    return Puzzle.create(
        player=player, iteration=player.iteration, timestamp=time.time(),
        data=json.dumps(data),
        solution=json.dumps(solution),
        values=json.dumps(data['initial'])
    )


def get_current_puzzle(player):
    puzzles = Puzzle.filter(player=player, iteration=player.iteration)
    if puzzles:
        [puzzle] = puzzles
        return puzzle


def encode_puzzle(puzzle: Puzzle):
    """Create data describing puzzle to send to client"""
    puzzle_data = json.loads(puzzle.data)
    values = json.loads(puzzle.values)
    # generate image for the puzzle
    image = task_sliders.render_image(puzzle)
    return dict(
        image=encode_image(image),
        size=puzzle_data['size'],
        sliders=puzzle_data['sliders'],
        values=values
    )


def get_progress(player: Player):
    """Return current player progress"""
    return dict(
        iteration=player.iteration,
        num_trials=player.num_trials,
        num_solved=player.num_solved,
        num_failed=player.num_failed,
    )


def handle_response(puzzle, response):
    solution = json.loads(puzzle.solution)
    cnt = list(range(len(solution)))

    # response is expected to contain one or more slider values in form of dict
    response = {int(k): v for k, v in response.items()}  # convert keys to ints
    keys = list(response.keys())

    # update stored values with submitted values (with snapping to ticks)
    values = json.loads(puzzle.values)
    for i, v in response.items():
        values[i] = task_sliders.snap_value(v, solution[i])

    # check each and every stored slider
    each_correct = [values[i] == solution[i] for i in cnt]
    num_correct = sum(each_correct)
    all_correct = num_correct == len(solution)

    # update puzzle record
    puzzle.values = json.dumps(values)
    puzzle.correct = num_correct
    puzzle.solved = all_correct

    # return feedback and snapped values
    return dict(is_correct={i: each_correct[i] for i in keys},
                values={i: values[i] for i in keys})


def play_game(player: Player, message: dict):
    """Main game workflow
    Implemented as reactive scheme: receive message from browser, react, respond.

    Generic game workflow, from server point of view:
    - receive: {'type': 'load'} -- empty message means page loaded
    - check if it's game start or page refresh midgame
    - respond: {'type': 'status', 'progress': ...}
    - respond: {'type': 'status', 'progress': ..., 'puzzle': data}
      in case of midgame page reload

    - receive: {'type': 'new'} -- request for a new puzzle
    - generate new puzzle
    - respond: {'type': 'puzzle', 'puzzle': data}

    - receive: {'type': 'values', 'values': {i: val}} -- submitted values of a slider #i
      one or many values accepted
    - check if the answer is correct
    - respond: {'type': 'feedback', 'is_completed': true|false, 'is_correct': ..., 'values': ...}
      - is_completed: if all sliders are correct
      - is_corect: feedback for each submitted slider
      - values: values of sliders corrected to snap to ticks
    """
    session = player.session
    my_id = player.id_in_group
    task_params = session.task_params

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
    if message_type == "new":
        if current is not None:
            if current.correct is None:
                raise RuntimeError("trying to skip over unsolved puzzle")
            if current.iteration == task_params['num_iterations']:
                return {
                    my_id: dict(
                        type='status', progress=get_progress(player), iterations_left=0
                    )
                }

        # generate new puzzle
        player.iteration += 1
        z = generate_puzzle(player)

        # update player progress
        player.num_trials += 1  # FIXME
        p = get_progress(player)

        return {my_id: dict(type='puzzle', puzzle=encode_puzzle(z), progress=p)}

    if message_type == "values":
        if current is None:
            raise RuntimeError("trying to answer no puzzle")

        response = message["values"]

        if response == "" or response is None:
            raise ValueError("bogus response")

        feedback = handle_response(current, response)
        current.response_timestamp = now

        if current.solved:
            player.num_solved += 1

        p = get_progress(player)
        return {
            my_id: dict(
                type='feedback',
                is_correct=feedback['is_correct'],
                values=feedback['values'],
                is_complete=current.solved,
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
            params=player.session.task_params,
            slider_size=task_sliders.SLIDER_BBOX,
        )

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            params=player.session.task_params,
            DEBUG=settings.DEBUG
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if not timeout_happened and not player.session.task_params['num_iterations']:
            raise RuntimeError("malicious page submission")


class Results(Page):
    pass


page_sequence = [Game, Results]
