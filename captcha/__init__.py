from otree.api import *

from . import utils

doc = """
Experimental catcha game
"""


class Constants(BaseConstants):
    name_in_url = 'captcha'
    players_per_group = None
    num_rounds = 1

    default_captcha_length = 5


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    total_puzzles = models.IntegerField()
    total_solved = models.IntegerField()


# puzzle-specific stuff

class PuzzleGame(ExtraModel):
    """A model to store current game state"""
    player = models.Link(Player)

    elapsed = models.FloatField(initial=0)
    iteration = models.IntegerField(initial=0)
    difficulty = models.FloatField(initial=0)
    puzzle = models.StringField(initial="")
    solution = models.StringField(initial="")


class PuzzleRecord(ExtraModel):
    """A model to keep record of all solved puzzles"""
    player = models.Link(Player)
    elapsed = models.FloatField()
    iteration = models.IntegerField()
    difficulty = models.FloatField()
    puzzle = models.StringField()
    solution = models.StringField()
    answer = models.StringField()
    is_correct = models.BooleanField()


def generate_puzzle(player: Player):
    difficulty = player.session.config.get('captcha_length', Constants.default_captcha_length)
    text = utils.generate_text(difficulty)
    # difficulty, puzzle, solution
    return difficulty, text, text


def generate_image(text):
    image = utils.generate_image(text)
    image = utils.distort_image(image)
    return image


def check_answer(solution: str, answer: str):
    return answer.upper() == solution


# generic game function, independent from above specific

def play_captcha(player: Player, data: dict):
    """Handles iteration of the game"""
    # create or retrieve current state
    if 'start' in data:
        current = PuzzleGame.create(player=player)
    else:
        current = PuzzleGame.objects_get(player=player)

    # record current answer
    if 'answer' in data:
        answer = data['answer']
        PuzzleRecord.create(
            player=player,
            elapsed=current.elapsed,
            iteration=current.iteration,
            difficulty=current.difficulty,
            puzzle=current.puzzle,
            solution=current.solution,
            answer=answer,
            is_correct=check_answer(current.solution, answer)
        )

    # generate next puzzle
    difficulty, puzzle, solution = generate_puzzle(player)

    # save current puzzle
    current.difficulty = difficulty
    current.puzzle = puzzle
    current.solution = solution
    current.iteration += 1
    # current.elapsed = ...

    # send the puzzle as image
    image = generate_image(puzzle)
    data = utils.encode_image(image)
    return {player.id_in_group: {'image': data}}


# PAGES

class MainPage(Page):
    timeout_seconds = 60

    live_method = play_captcha

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        current = PuzzleGame.object_get(player=player)
        # record total player stats
        player.total_puzzles = current.iteration
        player.total_solved = len(PuzzleRecord.filter(player=player, is_correct=True))
        # clean up
        current.delete()


class Results(Page):
    pass


page_sequence = [MainPage, Results]
