import random
import json
from pathlib import Path

from otree.api import *

from . import csv_utils

doc = """
Demo of stimulus/response app
"""


class C(BaseConstants):
    NAME_IN_URL = "demo_stimuli"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    INSTRUCTIONS = __name__ + "/instructions.html"

    GAME_TIMEOUT = 120  # seconds

    # default values reconfigurable from session config:

    NUM_TRIALS = 5
    MAX_RETRIES = 3
    TRIAL_TIMEOUT = 3  # seconds
    POSTTRIAL_PAUSE = 0.5  # seconds
    NOGO_RESPONSE = None


DATA = []
csv_utils.load_csv(
    DATA, Path(__file__).parent / "stimuli.csv", ["type", "stimulus", "category"]
)
PRIMES_POOL = csv_utils.filter_by_fields(DATA, type="word")
TARGETS_POOL = csv_utils.filter_by_fields(DATA, type="emoji")


class Subsession(BaseSubsession):
    is_practice = models.BooleanField()


def creating_session(subsession: Subsession):
    subsession.is_practice = True

    session = subsession.session
    defaults = dict(
        num_trials=C.NUM_TRIALS,
        max_retries=C.MAX_RETRIES,
        trial_timeout=C.TRIAL_TIMEOUT,
        nogo_response=C.NOGO_RESPONSE,
        post_trial_pause=C.POSTTRIAL_PAUSE
    )
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])

    for player in subsession.get_players():
        pregenerate_trials(player)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # number of completed trials
    num_trials = models.IntegerField(initial=0)
    # number of trials whth correct responses
    num_solved = models.IntegerField(initial=0)
    # number of trials with incorrect responses
    num_failed = models.IntegerField(initial=0)
    # number of trials without response (timeouted)
    num_skipped = models.IntegerField(initial=0)

    # temporary field to pass data from page
    results_data = models.LongStringField(blank=True)


class Trial(ExtraModel):
    """A record of single stimulus/response iteration"""

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)

    prime = models.StringField()
    prime_category = models.StringField()
    target = models.StringField()
    target_category = models.StringField()
    is_congruent = models.BooleanField()

    # either solved/failed or skipped
    is_completed = models.BooleanField(initial=False)

    response = models.StringField()
    is_correct = models.BooleanField()

    retries = models.IntegerField(initial=0)
    response_time = models.IntegerField()
    is_timeouted = models.BooleanField()


def generate_trial(player: Player, iteration: int) -> Trial:
    """Creates a new trial with random prime and stimuli"""
    prime_row = random.choice(PRIMES_POOL)
    target_row = random.choice(TARGETS_POOL)

    return Trial.create(
        round=player.round_number,
        player=player,
        iteration=iteration,
        #
        prime=prime_row["stimulus"],
        prime_category=prime_row["category"],
        target=target_row["stimulus"],
        target_category=target_row["category"],
        is_congruent=prime_row["category"] == target_row["category"],
    )


def pregenerate_trials(player):
    for i in range(1, C.NUM_TRIALS + 1):
        generate_trial(player, i)


def get_trials(player):
    return Trial.filter(player=player)


def encode_trial(trial):
    return dict(
        iteration=trial.iteration,
        prime=trial.prime,
        prime_category=trial.prime_category,
        target=trial.target,
        target_category=trial.target_category,
    )


def encode_trials(player):
    return list(map(encode_trial, get_trials(player)))


def validate_trial(trial, response):
    """Checks if a trial is correctly answered"""
    trial.response = response
    if response is None:
        trial.is_correct = None
    else:
        trial.is_correct = trial.response == trial.target_category


def validate_trials(player, results):
    player.num_trials = len(results)

    # this relies that trials retrieved in the same order as results
    # unmatched trials remain incomplete
    for trial, result in zip(get_trials(player), results):
        assert trial.iteration == result['i']
        trial.is_completed = True

        trial.retries = result.get('retr')
        trial.is_timeouted = result.get('rt') == None
        validate_trial(trial, result["input"])


def cleanup_trials(player):
    for trial in Trial.filter(player=player, is_completed=False):
        trial.delete()


def calc_stats(player):
    player.num_solved = len(
        Trial.filter(player=player, is_completed=True, is_correct=True)
    )
    player.num_failed = len(
        Trial.filter(player=player, is_completed=True, is_correct=False)
    )
    player.num_skipped = len(
        Trial.filter(player=player, is_completed=True, is_correct=None)
    )


# PAGES


class Intro(Page):
    pass


class Main(Page):
    timeout_seconds = C.GAME_TIMEOUT

    @staticmethod
    def js_vars(player):
        params = player.session.params
        return dict(
            config=dict(
                num_trials=params["num_trials"],
                max_retries=params['max_retries'],
                trial_timeout=params["trial_timeout"] * 1000,
                post_trial_pause=params["post_trial_pause"] * 1000,
                nogo_response=params['nogo_response']
            ),
            trials=encode_trials(player),
        )

    form_model = "player"
    form_fields = ["results_data"]

    def before_next_page(player, timeout_happened):
        results = json.loads(player.results_data)
        player.results_data = ""

        validate_trials(player, results)
        cleanup_trials(player)
        calc_stats(player)


class Results(Page):
    @staticmethod
    def vars_for_template(player):
        return dict(
            num_solved=player.num_solved,
            frac_solved=100 * player.num_solved / player.num_trials,
            num_failed=player.num_failed,
            frac_failed=100 * player.num_failed / player.num_trials,
            num_skipped=player.num_skipped,
            frac_skipped=100 * player.num_skipped / player.num_trials,
        )


page_sequence = [Intro, Main, Results]


def custom_export(players):
    yield [
        # player fields
        "participant_code",
        "is_dropout",
        "session",
        "round",
        "is_practice",
        "player",
        # trial fields
        "iteration",
        "prime",
        "prime_category",
        "target",
        "target_category",
        "is_congruent",
        "response",
        "response_correct",
        "reaction_time",
        "is_timeout",
    ]
    for player in players:
        participant = player.participant
        session = player.session
        subsession = player.subsession

        player_fields = [
            participant.code,
            participant.is_dropout if "is_dropout" in participant.vars else None,
            session.code,
            subsession.round_number,
            subsession.is_practice,
            player.id,
        ]

        trials = Trial.filter(player=player)

        if len(trials) == 0:
            # yield a row for players even without trials
            yield player_fields

        for trial in trials:
            yield player_fields + [
                trial.iteration,
                trial.prime,
                trial.prime_category,
                trial.target,
                trial.target_category,
                trial.is_congruent,
                trial.response,
                trial.is_correct,
                trial.reaction_time,
                trial.is_timeouted,
            ]
