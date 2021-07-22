import time
import random
from otree.api import *

from matrices.images import generate_image, encode_image

doc = """
Experimental captcha game
"""


class Constants(BaseConstants):
    name_in_url = "symmatrices"
    players_per_group = None
    num_rounds = 1

    characters = "♠♡♢♣♤♥♦♧"
    counted_char = "♠"
    default_matrix_size = 5


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    total = models.IntegerField(initial=0)
    answered = models.IntegerField(initial=0)
    correct = models.IntegerField(initial=0)
    incorrect = models.IntegerField(initial=0)


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
    retries = models.IntegerField(initial=0)


def summarize_trials(player: Player):
    player.total = len(Trial.filter(player=player))
    # expect at least 1 unanswered because of timeout, more if skipping allowed
    unanswered = len(Trial.filter(player=player, answer=None))
    player.answered = player.total - unanswered
    player.correct = len(Trial.filter(player=player, is_correct=True))
    player.incorrect = len(Trial.filter(player=player, is_correct=False))


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
    now = time.time()

    # generate and return first or next puzzle
    if "next" in data:
        trial_delay = player.session.config.get('trial_delay', 1.0)
        if trial and now - trial.timestamp < trial_delay:
            raise RuntimeError("Client is too fast!")
        force_solve = player.session.config.get('force_solve', False)
        if trial and force_solve and trial.is_correct is not True:
            raise ValueError("Attempted to advance over unsolved puzzle!")

        size, content, count = generate_puzzle(player)
        Trial.create(
            player=player,
            timestamp=now,
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

        try:
            answer = int(answer)
        except ValueError:
            ValueError("Bogus input from client!")

        trial.answer = answer
        trial.is_correct = answer == trial.solution
        trial.retries += 1

        return {player.id_in_group: {'feedback': trial.is_correct}}

    # otherwise
    raise ValueError("Invalid message from client!")


def custom_export(players):
    """Dumps all the puzzles generated"""
    yield [
        "session",
        "participant_code",
        "time",
        "iteration",
        "size",
        "content",
        "solution",
        "answer",
        "retries",
    ]
    for p in players:
        participant = p.participant
        session = p.session
        for z in Trial.filter(player=p):
            yield [
                session.code,
                participant.code,
                z.timestamp,
                z.iteration,
                z.size,
                z.content,
                z.solution,
                z.answer,
                z.retries,
            ]


# PAGES


class Game(Page):
    timeout_seconds = 60
    live_method = play_game

    @staticmethod
    def js_vars(player: Player):
        return dict(
            trial_delay=player.session.config.get('trial_delay', 1.0),
            allow_skip=player.session.config.get('allow_skip', False),
            force_solve=player.session.config.get('force_solve', False),
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        summarize_trials(player)
        player.payoff = player.correct


class Results(Page):
    pass


page_sequence = [Game, Results]
