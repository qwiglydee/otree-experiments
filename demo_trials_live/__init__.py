from pathlib import Path
import random

from otree.api import *

from common.live_utils import live_trials
from common.csv_utils import load_csv

doc = """
Your app description
"""

WORKDIR = Path(__file__).parent


class C(BaseConstants):
    NAME_IN_URL = "demo_trials_live"
    PLAYERS_PER_GROUP = None
    INSTRUCTIONS = __name__ + "/instructions.html"
    NUM_ROUNDS = 1
    NUM_TRIALS = 10

    DEFAULT_TRIAL_TIMEOUT = 5
    DEFAULT_POST_TRIAL_PAUSE = 1


PRIMES = []
load_csv(PRIMES, WORKDIR / "stimuli_primes.csv")
TARGETS = []
load_csv(TARGETS, WORKDIR / "stimuli_targets.csv")


def image_url(filename):
    return f"/static/images/{filename}"


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    num_completed = models.IntegerField(initial=0)


class Trial(ExtraModel):
    player = models.Link(Player)
    iteration = models.IntegerField(initial=0)
    is_completed = models.BooleanField(initial=False)
    is_timeouted = models.BooleanField(initial=False)
    is_skipped = models.BooleanField(initial=False)
    is_successful = models.BooleanField(initial=None)

    prime = models.StringField()
    prime_category = models.StringField()
    target = models.StringField()
    target_category = models.StringField()
    congruent = models.BooleanField()

    response = models.StringField()
    response_time = models.IntegerField()


def pregenerate_trials(player):
    for iter in range(1, C.NUM_TRIALS + 1):
        prime_row = random.choice(PRIMES)
        target_row = random.choice(TARGETS)

        Trial.create(
            player=player,
            iteration=iter,
            prime=prime_row["stimulus"],
            prime_category=prime_row["category"],
            target=image_url(target_row["stimulus"]),
            target_category=target_row["category"],
            congruent=prime_row["category"] == target_row["category"],
        )


def creating_session(subsession: Subsession):
    # override constants with session params
    session = subsession.session
    defaults = dict(
        trial_timeout=C.DEFAULT_TRIAL_TIMEOUT,
        post_trial_pause=C.DEFAULT_POST_TRIAL_PAUSE,
    )
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])

    for player in subsession.get_players():
        pregenerate_trials(player)


# PAGES


@live_trials
class Main(Page):
    trial_model = Trial
    trial_fields = ["iteration", "prime", "target"]

    @staticmethod
    def js_vars(player):
        params = player.session.params
        return dict(
            num_trials=C.NUM_TRIALS,
            media_fields={"target": "image"},
            trial_timeout=params["trial_timeout"],
            post_trial_pause=params["post_trial_pause"],
        )

    @staticmethod
    def get_progress(player: Player, iteration):
        return dict(total=C.NUM_TRIALS, current=iteration, completed=player.num_completed)


    @staticmethod
    def validate_response(trial: Trial, response: dict, timeout_happened: bool):
        print("validating", trial, "\nresponse:", response, "\ntimeout:", timeout_happened)

        if timeout_happened:
            trial.is_timeouted = True
            trial.is_successful = None
            trial.is_completed = True
        else:
            trial.response_time = response.get("response_time")
            trial.response = response["input"]
            trial.is_successful = trial.response == trial.target_category
            trial.is_completed = True

        trial.player.num_completed += 1

        return dict(
            responseFinal=True,
            responseCorrect=trial.is_successful,
        )


page_sequence = [Main]
