import time
import random
from otree.api import *

from .images import generate_image, encode_image


doc = """
Experimental colors game
"""


class Constants(BaseConstants):
    name_in_url = 'colors'
    players_per_group = None
    num_rounds = 1
    game_duration = 1
    colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan']
    color_values = {  # RRGGBB hexcodes
        'red': "#FF0000",
        'green': "#00FF00",
        'blue': "#0000FF",
        'yellow': "#FFFF00",
        'magenta': "#FF00FF",
        'cyan': "#00FFFF"
    }
    color_keys = {
        'r': 'red',
        'g': 'green',
        'b': 'blue',
        'y': 'yellow',
        'm': 'magenta',
        'c': 'cyan'
    }


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    total_puzzles = models.IntegerField(initial=0)
    total_solved = models.IntegerField(initial=0)


# puzzle-specific stuff

def generate_puzzle(player: Player):
    color = random.choice(Constants.colors)
    text = random.choice(Constants.colors)
    return color, text


class PuzzleRecord(ExtraModel):
    """A model to keep record of all generated puzzles"""
    player = models.Link(Player)

    timestamp = models.FloatField(initial=0)
    iteration = models.IntegerField(initial=0)

    color = models.StringField()
    text = models.StringField()
    congruent = models.BooleanField()

    answer = models.StringField()
    is_correct = models.BooleanField()
    is_skipped = models.BooleanField()


def play_colors(player: Player, data: dict):
    """Handles iteration of the game"""
    if 'start' in data:
        iteration = 0
    elif 'answer' in data:
        answer = data['answer']
        is_skipped = (answer == "")
        # get last unanswered task
        task = PuzzleRecord.filter(player=player, answer=None)[-1]
        # check answer
        is_correct = not is_skipped and answer == task.color
        # update task
        task.answer = answer
        task.is_correct = is_correct
        task.is_skipped = is_skipped

        if is_correct:
            # update player stats
            player.total_solved += 1

        iteration = task.iteration + 1
    else:
        raise ValueError("invalid data from client!")

    # update player stats
    player.total_puzzles += 1

    # new task
    text, color = generate_puzzle(player)
    PuzzleRecord.create(
        player=player,
        timestamp=time.time(),
        iteration=iteration,
        color=color,
        text=text,
        congruent=(text == color)
    )

    # send the puzzle as image
    image = generate_image(text, color)
    data = images.encode_image(image)
    return {player.id_in_group: {'image': data}}


def custom_export(players):
    """Dumps all the puzzles generated"""
    yield ['session', 'participant_code',
           'time', 'iteration', 'text', 'color', 'congruent', 'answer', 'is_correct', 'is_skipped']
    for p in players:
        participant = p.participant
        session = p.session
        for z in PuzzleRecord.filter(player=p):
            yield [session.code, participant.code,
                   z.timestamp, z.iteration, z.text, z.color, z.congruent, z.answer, z.is_correct, z.is_skipped]


# PAGES

class Intro(Page):
    pass


class Game(Page):
    timeout_seconds = Constants.game_duration * 60
    live_method = play_colors

    @staticmethod
    def js_vars(player: Player):
        return dict(color_keys=Constants.color_keys)


class Results(Page):
    pass


page_sequence = [Intro, Game, Results]
