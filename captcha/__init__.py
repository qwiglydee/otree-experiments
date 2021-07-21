import time
import random
from otree.api import *

from .images import generate_image, distort_image, encode_image


doc = """
Experimental captcha game
"""


class Constants(BaseConstants):
    name_in_url = 'captcha'
    players_per_group = None
    num_rounds = 1

    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    default_captcha_length = 5
    instructions_template = __name__ + '/instructions.html'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    total_puzzles = models.IntegerField(initial=0)
    total_solved = models.IntegerField(initial=0)


# puzzle-specific stuff


def generate_puzzle(player: Player):
    session = player.session
    if session.config.get('testing'):
        text = f"{player.total_puzzles:03}"
        return 0, text, text
    length = session.config.get('captcha_length', Constants.default_captcha_length)
    text = "".join((random.choice(Constants.characters) for _ in range(length)))
    return length, text, text.lower()


class Trial(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)

    timestamp = models.FloatField(initial=0)
    iteration = models.IntegerField(initial=0)

    length = models.FloatField()
    text = models.StringField()
    solution = models.StringField()

    answer = models.StringField()
    is_correct = models.BooleanField()
    is_skipped = models.BooleanField()


def play_game(player: Player, data: dict):
    """Handles iteration of the game"""
    if 'start' in data:
        iteration = 0
    elif 'answer' in data:
        answer = data['answer']
        is_skipped = answer == ""
        if not is_skipped:
            answer = answer.lower()
        # get last unanswered task
        task = Trial.filter(player=player, answer=None)[-1]
        # check answer
        is_correct = not is_skipped and answer == task.solution
        # update task
        task.answer = answer
        task.is_correct = is_correct
        task.is_skipped = is_skipped
        if is_correct:
            # update player stats
            player.total_solved += 1

        iteration = task.iteration + 1
    else:
        raise ValueError("Invalid data from client")

    # update player stats
    player.total_puzzles += 1

    # new task
    length, text, solution = generate_puzzle(player)
    Trial.create(
        player=player,
        timestamp=time.time(),
        iteration=iteration,
        length=length,
        text=text,
        solution=solution,
    )

    # send the puzzle as image
    image = generate_image(text)
    image = images.distort_image(image)
    data = encode_image(image)
    return {player.id_in_group: {'image': data}}


class Game(Page):
    timeout_seconds = 60

    live_method = play_game


class Results(Page):
    pass


page_sequence = [Game, Results]
