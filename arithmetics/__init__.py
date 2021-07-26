import time
import random
from otree.api import *

from .images import generate_image, encode_image


doc = """
Experimental arithmetics game
"""


class Constants(BaseConstants):
    name_in_url = "arithmetics"
    players_per_group = None
    num_rounds = 1

    digits = [1, 2, 3, 4, 5, 6, 7, 8, 9]  # excluding 0
    game_duration = 1


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


class Trial(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)

    timestamp = models.FloatField(initial=0)
    iteration = models.IntegerField(initial=0)

    puzzle = models.StringField()
    solution = models.IntegerField()

    # the following fields remain null for unanswered trials
    answer = models.IntegerField()
    is_correct = models.BooleanField()
    retries = models.IntegerField(initial=0)


def generate_puzzle(player: Player) -> Trial:
    """Create new puzzle for a player"""
    a = random.choice(Constants.digits) * 10 + random.choice(Constants.digits)
    b = random.choice(Constants.digits) * 10 + random.choice(Constants.digits)
    return Trial.create(
        player=player,
        puzzle=f"{a} + {b} = ",
        solution=a + b,
    )


def encode_puzzle(trial: Trial):
    """Create an image for a puzzle"""
    image = generate_image(trial.puzzle)
    data = encode_image(image)
    return data


def get_last_trial(player):
    """Get last (current) puzzle for a player"""
    trials = Trial.filter(player=player)
    trial = trials[-1] if len(trials) else None
    return trial


def check_answer(trial: Trial, answer: str):
    """Check given answer for a puzzle and update its status"""
    if answer == "":
        raise ValueError("Unexpected empty answer from client")
    trial.answer = answer
    trial.is_correct = int(answer) == trial.solution


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
    - server > client {'feedback': true|false} -- feedback on the answer
    """
    now = time.time()

    # get last trial, if any
    trial = get_last_trial(player)
    iteration = trial.iteration if trial else 0

    # generate first or next puzzle and return image
    if "next" in data:
        trial_delay = player.session.config.get('trial_delay', 1.0)
        if trial and now - trial.timestamp < trial_delay:
            raise RuntimeError("Client is too fast!")
        force_solve = player.session.config.get('force_solve', False)
        if trial and force_solve and trial.is_correct is not True:
            raise ValueError("Attempted to advance over unsolved puzzle!")

        # new trial
        trial = generate_puzzle(player)
        trial.timestamp = now
        trial.iteration = iteration + 1

        # return image
        data = encode_puzzle(trial)
        return {player.id_in_group: {"image": data}}

    # check given answer and return feedback
    if "answer" in data:
        check_answer(trial, data["answer"])
        trial.retries += 1

        # return feedback
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
        "puzzle",
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
                z.puzzle,
                z.solution,
                z.answer,
                z.is_correct,
            ]


# PAGES


class Intro(Page):
    pass


class Game(Page):
    timeout_seconds = Constants.game_duration * 60

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
