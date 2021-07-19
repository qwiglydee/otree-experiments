import time
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
    game_duration = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    total_puzzles = models.IntegerField(initial=0)
    total_solved = models.IntegerField(initial=0)


# puzzle-specific stuff

class PuzzleGame(ExtraModel):
    """A model to store current game state"""
    player = models.Link(Player)
    start_time = models.FloatField()
    iteration = models.IntegerField()

    difficulty = models.FloatField(initial=0)
    puzzle = models.StringField(initial="")
    solution = models.StringField(initial="")


class PuzzleRecord(ExtraModel):
    """A model to keep record of all solved puzzles"""
    player = models.Link(Player)
    elapsed = models.FloatField(initial=0)
    iteration = models.IntegerField(initial=0)

    difficulty = models.FloatField()
    puzzle = models.StringField()
    solution = models.StringField()
    answer = models.StringField()
    is_correct = models.BooleanField()
    is_skipped = models.BooleanField()


def generate_puzzle(player: Player):
    session = player.session
    if session.config.get('captcha_testing'):
        text = f"{player.total_puzzles:03}"
        return 0, text, text
    difficulty = session.config.get('captcha_length', Constants.default_captcha_length)
    text = utils.generate_text(difficulty)
    # difficulty, puzzle, solution
    return difficulty, text, text.lower()


def generate_image(text):
    image = utils.generate_image(text)
    image = utils.distort_image(image)
    return image


def check_answer(solution: str, answer: str):
    return answer.lower() == solution


# generic game function, independent from above specific

def play_captcha(player: Player, data: dict):
    """Handles iteration of the game"""
    now = time.time()
    # create or retrieve current state
    if 'start' in data:
        # initial= doesn't work
        current = PuzzleGame.create(player=player, start_time=now, iteration=0)
    else:
        current = PuzzleGame.objects_get(player=player)

    # record current answer
    if 'answer' in data:
        answer = data['answer']
        correct = check_answer(current.solution, answer)
        PuzzleRecord.create(
            player=player,
            elapsed=now - current.start_time,
            iteration=current.iteration,
            difficulty=current.difficulty,
            puzzle=current.puzzle,
            solution=current.solution,
            answer=answer,
            is_correct=correct,
            is_skipped=(answer == "")
        )
        if correct:
            player.total_solved += 1

    # generate next puzzle
    difficulty, puzzle, solution = generate_puzzle(player)

    # save current puzzle
    current.iteration += 1
    current.difficulty = difficulty
    current.puzzle = puzzle
    current.solution = solution

    # update player stats
    player.total_puzzles += 1

    # send the puzzle as image
    image = generate_image(puzzle)
    data = utils.encode_image(image)
    return {player.id_in_group: {'image': data}}


def custom_export(players):
    """Dumps all the puzzles displayed"""
    yield ['session', 'participant_code',
           'time', 'iteration', 'difficulty', 'puzzle', 'solution', 'answer', 'is_correct', 'is_skipped']
    for p in players:
        participant = p.participant
        session = p.session
        for z in PuzzleRecord.filter(player=p):
            yield [session.code, participant.code,
                   z.elapsed, z.iteration, z.difficulty, z.puzzle, z.solution, z.answer, z.is_correct, z.is_skipped]

# PAGES

class Intro(Page):
    pass


class Game(Page):
    timeout_seconds = Constants.game_duration * 60

    live_method = play_captcha

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # cleanup
        PuzzleGame.objects_get(player=player).delete()


class Results(Page):
    pass


page_sequence = [Intro, Game, Results]
