import time
import random
from otree.api import *

from .images import generate_image, encode_image


doc = """
Experimental matrix counting game
"""


class Constants(BaseConstants):
    name_in_url = 'matrices'
    players_per_group = None
    num_rounds = 1

    characters = "01"
    counted_char = "0"
    default_matrix_size = 5
    game_duration = 1


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
    size = session.config.get('matrix_size', Constants.default_matrix_size)
    length = size * size
    if session.config.get('testing'):
        count = player.total_puzzles
        string = (Constants.counted_char * count) + ('x' * (length - 1))
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

    answer = models.IntegerField()
    is_correct = models.BooleanField()
    is_skipped = models.BooleanField()


def play_game(player: Player, data: dict):
    """Handles iteration of the game"""
    if 'start' in data:
        iteration = 0
    elif 'answer' in data:
        answer = data['answer']
        is_skipped = (answer == "")
        if not is_skipped:
            answer = int(answer)

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
        raise ValueError("invalid data from client!")

    # update player stats
    player.total_puzzles += 1

    # new task
    size, content, solution = generate_puzzle(player)
    task = Trial.create(
        player=player,
        timestamp=time.time(),
        iteration=iteration,
        size=size,
        content=content,
        solution=solution
    )

    # send the puzzle as image
    image = generate_image(size, content)
    data = encode_image(image)
    return {player.id_in_group: {'image': data}}


def custom_export(players):
    """Dumps all the puzzles generated"""
    yield ['session', 'participant_code',
           'time', 'iteration', 'size', 'content', 'solution', 'answer', 'is_correct', 'is_skipped']
    for p in players:
        participant = p.participant
        session = p.session
        for z in Trial.filter(player=p):
            yield [session.code, participant.code,
                   z.timestamp, z.iteration, z.size, z.content, z.solution, z.answer, z.is_correct, z.is_skipped]


# PAGES

class Intro(Page):
    pass


class Game(Page):
    timeout_seconds = Constants.game_duration * 60

    live_method = play_game


class Results(Page):
    pass


page_sequence = [Intro, Game, Results]