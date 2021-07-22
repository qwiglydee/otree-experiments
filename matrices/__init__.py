import time
import random
from otree.api import *

from .images import generate_image, encode_image


doc = """
Experimental matrix counting game
"""


class Constants(BaseConstants):
    name_in_url = "matrices"
    players_per_group = None
    num_rounds = 1

    characters = "01"
    counted_char = "0"
    default_matrix_size = 5


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
    size = session.config.get("matrix_size", Constants.default_matrix_size)
    length = size * size
    if session.config.get("testing"):
        count = player.total_puzzles
        string = (Constants.counted_char * count) + ("x" * (length - 1))
        return size, string, count
    content = "".join((random.choice(Constants.characters) for i in range(length)))
    count = content.count(Constants.counted_char)
    # difficulty, puzzle, solution
    return size, content, count


class Trial(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)

    timestamp = models.FloatField(initial=0)
    iteration = models.IntegerField(initial=0)

    size = models.IntegerField()
    content = models.StringField()
    solution = models.IntegerField()

    # the following fields remain null for unanswered trials
    answer = models.IntegerField()
    is_correct = models.BooleanField()


def play_game(player: Player, data: dict):
    """Handles iterations of the game on a live page

    Messages:
    - server < client {'next': true} -- request for next (or first) puzzle
    - server > client {'image': data} -- puzzle image
    - server < client {'answer': data} -- answer to a puzzle
    - server > client {'feedback': true|false|null} -- feedback on the answer (null for empty answer)
    """

    # get last trial, if any
    trials = Trial.filter(player=player)
    trial = trials[-1] if len(trials) else None
    iteration = trial.iteration if trial else 0

    # generate and return first or next puzzle
    if "next" in data:
        size, content, count = generate_puzzle(player)
        Trial.create(
            player=player,
            timestamp=time.time(),
            iteration=iteration + 1,
            size=size,
            content=content,
            solution=count,
        )

        image = generate_image(size, content)
        data = encode_image(image)
        return {player.id_in_group: {"image": data}}

    # check given answer and return feedback
    if "answer" in data:
        answer = data["answer"]

        if answer != "":
            answer = int(answer)
            trial.answer = answer
            trial.is_correct = answer == trial.solution

        return {player.id_in_group: {'feedback': trial.is_correct}}

    # otherwise
    raise ValueError("Invalid message from client!")


class Game(Page):
    timeout_seconds = 60
    live_method = play_game

    @staticmethod
    def js_vars(player: Player):
        return dict(delay=1000, allow_skip=True)


class Results(Page):
    pass


page_sequence = [Game, Results]
