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
    task = session.config.get('task')
    if task == 'matrix':
        return task_matrix
    if task == 'transcription':
        return task_transcription
    if task == 'decoding':
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
    defaults = dict(retry_delay=1.0, attempts_per_puzzle=1)
    session.ret_params = {}
    for param in defaults:
        session.ret_params[param] = session.config.get(param, defaults[param])


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)
    num_correct = models.IntegerField(initial=0)
    num_failed_puzzles = models.IntegerField(initial=0)


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
    """Create an image for a puzzle"""
    task_module = get_task_module(puzzle.player)
    image = task_module.render_image(puzzle)
    data = encode_image(image)
    return data


def get_stats(player: Player):
    return dict(
        num_correct=player.num_correct,
        num_incorrect=player.num_failed_puzzles,
        iteration=player.iteration,
    )


def get_full_state(player: Player, z: Puzzle):
    return dict(stats=get_stats(player), image=encode_puzzle(z))


def play_game(player: Player, data: dict):
    session = player.session
    my_id = player.id_in_group
    ret_params = session.ret_params
    task_module = get_task_module(player)

    now = time.time()

    if "cheat" in data and settings.DEBUG:
        z = get_current_puzzle(player)
        return {my_id: {'solution': z.solution}}

    if data == {}:
        z = get_current_puzzle(player) or generate_puzzle(player)
        return {my_id: get_full_state(player, z)}

    z = get_current_puzzle(player)

    if (
        z.attempts > 0
        and time.time() < z.response_timestamp + ret_params['retry_delay']
    ):
        raise {my_id: dict(msg='Client advancing too fast')}

    answer = data['answer']
    z.response = answer
    z.is_correct = task_module.is_correct(answer, z)
    z.response_timestamp = now
    z.attempts += 1
    player.num_correct += z.is_correct

    payload = dict(is_correct=z.is_correct)

    if z.is_correct:
        z = generate_puzzle(player)
        payload.update(get_full_state(player, z))
    else:
        if z.attempts < ret_params['attempts_per_puzzle']:
            payload.update(freeze=ret_params['retry_delay'], is_retry=True)
        else:
            player.num_failed_puzzles += 1
            z = generate_puzzle(player)
            payload.update(get_full_state(player, z))
    return {my_id: payload}


class Game(Page):
    timeout_seconds = 60

    live_method = play_game

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
