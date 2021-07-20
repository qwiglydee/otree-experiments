import time
import random
from otree.api import *

from . import images


doc = """
Experimental captcha game
"""


class Constants(BaseConstants):
    name_in_url = 'captcha'
    players_per_group = None
    num_rounds = 1

    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    default_captcha_length = 5
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
    if session.config.get('captcha_testing'):
        text = f"{player.total_puzzles:03}"
        return 0, text, text
    length = session.config.get('captcha_length', Constants.default_captcha_length)
    text = "".join((random.choice(Constants.characters) for i in range(length)))
    # difficulty, puzzle, solution
    return length, text, text.lower()


def generate_image(text):
    image = images.generate_image(text)
    image = images.distort_image(image)
    return image


def check_answer(solution: str, answer: str):
    return answer.lower() == solution


class PuzzleRecord(ExtraModel):
    """A model to keep record of all generated puzzles"""
    player = models.Link(Player)

    timestamp = models.FloatField(initial=0)
    iteration = models.IntegerField(initial=0)

    difficulty = models.FloatField()
    puzzle = models.StringField()
    solution = models.StringField()

    answer = models.StringField()
    is_correct = models.BooleanField()
    is_skipped = models.BooleanField()


def play_captcha(player: Player, data: dict):
    """Handles iteration of the game"""
    if 'start' in data:
        iteration = 0
    elif 'answer' in data:
        answer = data['answer']
        is_skipped = (answer == "")
        # get last unanswered task
        task = PuzzleRecord.filter(player=player, answer=None)[-1]
        # check answer
        is_correct = check_answer(task.solution, answer)
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
    difficulty, puzzle, solution = generate_puzzle(player)
    task = PuzzleRecord.create(
        player=player,
        timestamp=time.time(),
        iteration=iteration,
        difficulty=difficulty,
        puzzle=puzzle,
        solution=solution
    )

    # send the puzzle as image
    image = generate_image(task.puzzle)
    data = images.encode_image(image)
    return {player.id_in_group: {'image': data}}


def custom_export(players):
    """Dumps all the puzzles generated"""
    yield ['session', 'participant_code',
           'time', 'iteration', 'difficulty', 'puzzle', 'solution', 'answer', 'is_correct', 'is_skipped']
    for p in players:
        participant = p.participant
        session = p.session
        for z in PuzzleRecord.filter(player=p):
            yield [session.code, participant.code,
                   z.timestamp, z.iteration, z.difficulty, z.puzzle, z.solution, z.answer, z.is_correct, z.is_skipped]


# PAGES

class Intro(Page):
    pass


class Game(Page):
    timeout_seconds = Constants.game_duration * 60

    live_method = play_captcha


class Results(Page):
    pass


page_sequence = [Intro, Game, Results]
