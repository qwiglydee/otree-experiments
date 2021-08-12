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
        num_sliders=48,
        num_columns=3
    )
    session.task_params = {}
    for param in defaults:
        session.task_params[param] = session.config.get(param, defaults[param])


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # only suported 1 iteration for now
    iteration = models.IntegerField(initial=0)

    num_correct = models.IntegerField(initial=0)
    elapsed_time = models.FloatField(initial=0)


# puzzle-specific stuff


class Puzzle(ExtraModel):
    """A model to keep record of sliders setup"""

    player = models.Link(Player)
    iteration = models.IntegerField()
    timestamp = models.FloatField()

    # slider puzzle parameters json encoded
    data = models.LongStringField()
    # solution values json encoded list
    solution = models.LongStringField()
    # initial or submited values, json encoded list
    values = models.LongStringField()

    # timestamp of last response
    response_timestamp = models.FloatField()
    # number of correct sliders
    correct = models.IntegerField(initial=0)
    # if all sliders solved
    solved = models.BooleanField(initial=False)


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
    )


def handle_response(puzzle, i, value):
    solution = json.loads(puzzle.solution)
    cnt = list(range(len(solution)))

    # snap to slider step
    value = task_sliders.snap_value(value, solution[i])
    # update stored values with submitted value
    values = json.loads(puzzle.values)
    values[i] = value
    is_correct = value == solution[i]

    # check each and every stored slider
    each_correct = [values[i] == solution[i] for i in cnt]
    num_correct = sum(each_correct)
    all_correct = num_correct == len(solution)

    # update puzzle record
    puzzle.values = json.dumps(values)
    puzzle.correct = num_correct
    puzzle.solved = all_correct

    # return feedback and snapped values
    return dict(value=value, is_correct=is_correct)


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
    - generate new sliders
    - respond: {'type': 'puzzle', 'puzzle': data}

    - receive: {'type': 'value', 'slider': ..., 'value': ...} -- submitted value of a slider
      - slider: the index of the slider
      - value: the value of slider in pixels
    - check if the answer is correct
    - respond: {'type': 'feedback', 'slider': ..., 'value': ..., 'is_correct': ..., 'is_completed': ...}
      - slider: the index of slider submitted
      - value: the value aligned to slider steps
      - is_corect: if submitted value is correct
      - is_completed: if all sliders are correct
    """
    session = player.session
    my_id = player.id_in_group
    task_params = session.task_params

    now = time.time()
    # the current puzzle or none
    current = get_current_puzzle(player)

    message_type = message['type']

    if message_type == 'load':
        p = get_progress(player)
        if current:
            return {my_id: dict(type='status', progress=p, puzzle=encode_puzzle(current))}
        else:
            return {my_id: dict(type='status', progress=p)}

    if message_type == "new":
        if current is not None:
            raise RuntimeError("trying to create 2nd puzzle")

        player.iteration += 1
        z = generate_puzzle(player)
        p = get_progress(player)

        return {my_id: dict(type='puzzle', puzzle=encode_puzzle(z), progress=p)}

    if message_type == "value":
        if current is None:
            raise RuntimeError("trying to answer no puzzle")

        slider = int(message["slider"])
        value = int(message["value"])

        feedback = handle_response(current, slider, value)
        current.response_timestamp = now

        p = get_progress(player)
        return {
            my_id: dict(
                type='feedback',
                slider=slider,
                value=feedback['value'],
                is_correct=feedback['is_correct'],
                is_completed=current.solved,
                progress=p,
            )
        }

    if message_type == "cheat" and settings.DEBUG:
        return {my_id: dict(type='solution', solution=json.loads(current.solution))}

    raise RuntimeError("unrecognized message from client")


class Game(Page):
    timeout_seconds = 120

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
        current = get_current_puzzle(player)

        if current and current.response_timestamp:
            player.elapsed_time = current.response_timestamp - current.timestamp
            player.num_correct = current.correct
            player.payoff = player.num_correct


class Results(Page):
    pass


page_sequence = [Game, Results]
