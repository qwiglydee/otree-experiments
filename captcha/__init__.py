import time
import random
from otree.api import *

from .images import generate_image, distort_image, encode_image


doc = """
Experimental captcha game
"""


class Constants(BaseConstants):
    name_in_url = "captcha"
    players_per_group = None
    num_rounds = 1

    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    default_captcha_length = 5
    instructions_template = __name__ + "/instructions.html"


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
    length = session.config.get("captcha_length", Constants.default_captcha_length)
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

    # the following fields remain null for unanswered trials
    answer = models.StringField()
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

        length, text, solution = generate_puzzle(player)
        Trial.create(
            player=player,
            timestamp=now,
            iteration=iteration + 1,
            length=length,
            text=text,
            solution=solution,
        )

        image = generate_image(text)
        image = images.distort_image(image)
        data = encode_image(image)
        return {player.id_in_group: {"image": data}}

    # check given answer and return feedback
    if "answer" in data:
        answer = data["answer"]

        if answer == "":
            raise ValueError("Bogus input from client")

        answer = answer.lower()
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
        "length",
        "text",
        "solution",
        "answer",
        "is_correct",
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
                z.length,
                z.text,
                z.solution,
                z.answer,
                z.is_correct,
            ]


# PAGES


class Intro(Page):
    pass


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
        player.payoff = player.correct - player.incorrect


class Results(Page):
    pass


page_sequence = [Game, Results]
