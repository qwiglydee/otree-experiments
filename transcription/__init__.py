import time
import random
from otree.api import *
from otree import settings

from .images import generate_image, distort_image, encode_image


doc = """
CAPTCHA-style transcription task
"""


class Constants(BaseConstants):
    name_in_url = "transcription"
    players_per_group = None
    num_rounds = 1

    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    instructions_template = __name__ + "/instructions.html"
    captcha_length = 3


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    session = subsession.session
    defaults = dict(
        puzzle_delay=1.0,
        retry_delay=1.0,
        attempts_per_puzzle=1,
        max_iterations=-1,
        max_wrong_answers=0,
    )
    session.ret_params = {}
    for param in defaults:
        session.ret_params[param] = session.config.get(param, defaults[param])


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)
    num_correct = models.IntegerField(initial=0)
    # number of incorrect answers, including retries
    num_incorrect = models.IntegerField(initial=0)


# puzzle-specific stuff


class Puzzle(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)
    iteration = models.IntegerField(initial=0)
    attempts = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)
    solution = models.StringField()
    response = models.StringField()
    response_timestamp = models.FloatField()
    is_correct = models.BooleanField()


def generate_puzzle(player: Player) -> Puzzle:
    """Create new puzzle for a player"""
    text = "".join(
        (random.choice(Constants.characters) for _ in range(Constants.captcha_length))
    )
    player.iteration += 1
    return Puzzle.create(
        player=player, solution=text, iteration=player.iteration, timestamp=time.time(),
    )


def get_last_puzzle(player):
    """Get last (current) puzzle for a player"""
    puzzles = Puzzle.filter(player=player, iteration=player.iteration)
    if puzzles:
        [puzzle] = puzzles
        return puzzle


def encode_puzzle(puzzle: Puzzle):
    """Create an image for a puzzle"""
    image = generate_image(puzzle.solution)
    image = distort_image(image)
    data = encode_image(image)
    return data


def play_game(player: Player, data: dict):
    """Handles iterations of the game on a live page

    Messages:
    - server < client {} -- empty message means page reload
    - server > client {'image': data, 'stats': ...} -- puzzle image
    - server < client {'answer': data} -- answer to a puzzle
    - server > client {'feedback': true|false, 'stats': ...} -- feedback on the answer
    - server > client {'gameover': true} -- all iterations played
    if DEBUG=1
    - server < client {'cheat': true} -- request solution
    - server > client {'solution': str} -- solution
    """
    session = player.session
    my_id = player.id_in_group
    ret_params = session.ret_params

    now = time.time()

    # get last puzzle, if any
    z = get_last_puzzle(player)
    if "cheat" in data and settings.DEBUG:
        return {my_id: {'solution': z.solution}}

    payload = {}

    # check given answer and return
    answer = data.get('answer')
    if answer:
        if (
            z.attempts > 0
            and time.time() < z.response_timestamp + ret_params['retry_delay']
        ):
            raise RuntimeError("Client advancing too fast!")
        if 0 < ret_params['max_iterations'] < z.iteration:
            return {my_id: {"gameover": True}}

        z.response = answer
        z.is_correct = answer.lower() == z.solution.lower()
        z.response_timestamp = now
        z.attempts += 1

        payload['is_correct'] = z.is_correct
        player.num_correct += z.is_correct
        player.num_incorrect += not z.is_correct

    if (not z) or z.is_correct or (z.attempts >= ret_params['attempts_per_puzzle']):
        z = generate_puzzle(player)

    payload['stats'] = dict(
        correct=player.num_correct,
        incorrect=player.num_incorrect,
        iteration=player.iteration,
    )

    if z.attempts > 0:
        payload['freeze'] = ret_params['retry_delay']
    payload['image'] = encode_puzzle(z)
    payload['is_retry'] = z.attempts > 0

    return {my_id: payload}


class Game(Page):
    timeout_seconds = 5 * 60

    live_method = play_game

    @staticmethod
    def vars_for_template(player: Player):
        return dict(DEBUG=settings.DEBUG)

    @staticmethod
    def js_vars(player: Player):
        session = player.session
        return session.ret_params


class Results(Page):
    pass


page_sequence = [Game, Results]
