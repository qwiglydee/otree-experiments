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
    NUM_TRIALS = 10
    TRIAL_TIMEOUT = 3 # seconds
    GAME_TIMEOUT = 600 # seconds 
    TRIAL_PAUSE = 1 # seconds


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
    for player in subsession.get_players():
        generate_trials(player)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    num_trials = models.IntegerField(initial=0)
    num_correct = models.IntegerField(initial=0)
    num_incorrect = models.IntegerField(initial=0)
    num_skipped = models.IntegerField(initial=0)

    # field to pass data from page
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

    reaction_time = models.IntegerField()
    is_timeouted = models.BooleanField()

    response = models.StringField()
    is_correct = models.BooleanField()


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
        is_congruent=prime_row["category"] == target_row["category"]
    )


def generate_trials(player):
    for i in range(1, C.NUM_TRIALS+1):
        generate_trial(player, i)


def validate_trial(trial, response, reaction, timeouted):
    """Checks if a trial is correctly answered"""
    trial.response = response
    trial.reaction_time = reaction
    if timeouted:
        trial.is_timeouted = True
        trial.is_correct = False
    else:
        trial.is_correct = trial.response == trial.target_category


def cleanup_trials(player):
    for i in range(player.num_trials+1, C.NUM_TRIALS+1):
        Trial.filter(player=player, iteration=i)[0].delete()


def encode_session(player):
    """Creates data structure to pass to a page"""
    # NB: providing `target_category` allows javascript cheating  
    def encode_trial(t):
        return dict(
            iteration=t.iteration,
            prime=t.prime,
            prime_category=t.prime_category,
            target=t.target,
            target_category=t.target_category,
        )

    return dict(
        config=dict(vars(C)),
        trials=list(map(encode_trial, Trial.filter(player=player))), 
    )


# PAGES


class Intro(Page):
    pass


class Main(Page):
    timeout_seconds = C.GAME_TIMEOUT

    @staticmethod
    def js_vars(player):
        return encode_session(player)

    form_model = 'player'
    form_fields = ['results_data']

    def before_next_page(player, timeout_happened):
        results = json.loads(player.results_data)
        player.num_trials = len(results)

        player.results_data = "" 
        cleanup_trials(player)

        for result in results:
            trial = Trial.filter(player=player, iteration=result['i'])[0]
            validate_trial(trial, result['response'], result['reaction'], result.get('timeout', False))

        player.num_correct = len(Trial.filter(player=player, is_correct=True))
        player.num_incorrect = len(Trial.filter(player=player, is_correct=False))
        player.num_skipped = len(Trial.filter(player=player, is_timeouted=True))


class Results(Page):
    @staticmethod
    def vars_for_template(player):
        return dict(
            num_correct=player.num_correct,
            frac_correct=100 * player.num_correct / player.num_trials,
            num_incorrect=player.num_incorrect,
            frac_incorrect=100 * player.num_incorrect / player.num_trials,
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
            participant.is_dropout if 'is_dropout' in participant.vars else None,
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
                trial.is_timeouted
            ]