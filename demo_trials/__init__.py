import random
import json
from pathlib import Path

from otree.api import *

from common import image_utils, live_utils

doc = """
Demo of question/answer app
"""


class C(BaseConstants):
    NAME_IN_URL = "demo_trials"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    INSTRUCTIONS = __name__ + "/instructions.html"

    CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    LENGTH = 3
    TEXT_SIZE = 32
    TEXT_PADDING = 32
    TEXT_FONT = Path(__file__).parent / "assets" / "FreeSansBold.otf"

    GAME_TIMEOUT = 300  # seconds
    TRIAL_PAUSE = 1  # seconds

    # default values reconfigurable from session config:

    NUM_ITERATIONS = None  # infinite
    MAX_RETRIES = 3
    TRIAL_TIMEOUT = 10  # seconds
    NOGO_ANSWER = None


class Subsession(BaseSubsession):
    is_practice = models.BooleanField()


def creating_session(subsession: Subsession):
    subsession.is_practice = True

    session = subsession.session
    defaults = dict(
        num_iterations=C.NUM_ITERATIONS,
        max_retries=C.MAX_RETRIES,
        trial_timeout=C.TRIAL_TIMEOUT,
        nogo_answer=C.NOGO_ANSWER,
    )
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # current iteration (a trial created and sent )
    cur_iteration = models.IntegerField(initial=0)

    # number of completed trials
    num_trials = models.IntegerField(initial=0)
    # number of trials whth correct responses
    num_solved = models.IntegerField(initial=0)
    # number of trials with incorrect responses
    num_failed = models.IntegerField(initial=0)
    # number of trials without response (timeouted)
    num_skipped = models.IntegerField(initial=0)

    # field to pass data from page
    results_data = models.LongStringField(blank=True)


class Trial(ExtraModel):
    """A record of single question/answer iteration"""

    timestamp_loaded = models.FloatField()
    timestamp_responded = models.FloatField()

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)

    text = models.StringField()
    solution = models.StringField()

    # either solved/failed or skipped  
    is_completed = models.BooleanField(initial=False)

    response = models.StringField()
    is_correct = models.BooleanField()

    retries = models.IntegerField(initial=0)
    reaction_time = models.IntegerField()
    is_timeouted = models.BooleanField()


def generate_trial(player: Player) -> Trial:
    """Creates a new trial with random text"""

    text = "".join((random.choice(C.CHARSET) for _ in range(C.LENGTH)))

    return Trial.create(
        round=player.round_number,
        player=player,
        iteration=player.cur_iteration,
        #
        text=text,
        solution=text.lower(),
    )


def get_trial(player: Player):
    """Gets current trial for a player"""
    trials = Trial.filter(player=player, iteration=player.cur_iteration)
    if len(trials) == 0:
        return None
    return trials[0]


def encode_trial(trial):
    image = image_utils.render_text(C, trial.text)
    data = image_utils.encode_image(image)
    return dict(image=data)


def validate_trial(trial, response: str):
    """Checks if a trial is correctly answered"""
    if response is None:
        trial.response = None
        trial.is_correct = None
    else:
        trial.response = response.strip().lower()
        trial.is_correct = trial.response == trial.solution


def get_progress(player, trial=None):
    return dict(
        total=C.NUM_ITERATIONS,
        current=player.cur_iteration,
        completed=player.num_trials,
        solved=player.num_solved,
        failed=player.num_failed,
        retries=trial.retries if trial else None,
    )


# PAGES


class Intro(Page):
    pass


def on_load(player):
    print("loading new trial")
    player.cur_iteration += 1
    # newtrial = get_trial(player)  # for pregenerated trials
    newtrial = generate_trial(player)

    return dict(trial=newtrial)


def on_input(player, trial, input, response_time, timeout):
    print("handing input:", input, "timeout:", timeout)
    params = player.session.params
    max_retries = params["max_retries"]
    nogo_answer = params["nogo_answer"] 

    trial.reaction_time = response_time

    if timeout:
        trial.is_timeouted = True
        input = nogo_answer

    if input is not None:
        validate_trial(trial, input)
        trial.retries += 1
        trial.is_completed = trial.is_correct or timeout or trial.retries == max_retries
    else: # skipping trial when null input or vain timeout
        trial.response = None
        trial.is_correct = None
        trial.is_completed = True

    if trial.is_completed:
        player.num_trials += 1

        if trial.is_correct is True:
            player.num_solved += 1
        elif trial.is_correct is False:
            player.num_failed += 1
        else: # None
            player.num_skipped += 1

    return dict(
        feedback=dict(
            input=trial.response, correct=trial.is_correct, final=trial.is_completed
        )
    )


class Main(Page):
    timeout_seconds = C.GAME_TIMEOUT

    @staticmethod
    def js_vars(player):
        params = player.session.params
        return dict(
            config=dict(
                num_iterations=params["num_iterations"],
                max_retries=params["max_retries"],
                trial_timeout=C.TRIAL_TIMEOUT * 1000,
                trial_pause=C.TRIAL_PAUSE * 1000,
            )
        )

    live_method = live_utils.live_trials(
        get_trial=get_trial,
        encode_trial=encode_trial,
        on_load=on_load,
        on_input=on_input,
        get_progress=get_progress,
    )


class Results(Page):
    @staticmethod
    def vars_for_template(player):
        if player.num_trials == 0:
            return dict(
                num_solved=0,
                frac_solved=0,
                num_failed=0,
                frac_failed=0,
                num_skipped=0,
                frac_skipped=0,
            )

        return dict(
            num_solved=player.num_solved,
            frac_solved=100 * player.num_solved / player.num_trials,
            num_failed=player.num_failed,
            frac_failed=100 * player.num_failed / player.num_trials,
            num_skipped=player.num_skipped,
            frac_skipped=100 * player.num_skipped / player.num_trials,
        )


page_sequence = [Intro, Main, Results]


# def custom_export(players):
#     yield [
#         # player fields
#         "participant_code",
#         "is_dropout",
#         "session",
#         "round",
#         "is_practice",
#         "player",
#         # trial fields
#         "iteration",
#         "prime",
#         "prime_category",
#         "target",
#         "target_category",
#         "is_congruent",
#         "response",
#         "response_correct",
#         "reaction_time",
#         "is_timeout",
#     ]
#     for player in players:
#         participant = player.participant
#         session = player.session
#         subsession = player.subsession

#         player_fields = [
#             participant.code,
#             participant.is_dropout if 'is_dropout' in participant.vars else None,
#             session.code,
#             subsession.round_number,
#             subsession.is_practice,
#             player.id,
#         ]

#         trials = Trial.filter(player=player)

#         if len(trials) == 0:
#             # yield a row for players even without trials
#             yield player_fields

#         for trial in trials:
#             yield player_fields + [
#                 trial.iteration,
#                 trial.prime,
#                 trial.prime_category,
#                 trial.target,
#                 trial.target_category,
#                 trial.is_congruent,
#                 trial.response,
#                 trial.is_correct,
#                 trial.reaction_time,
#                 trial.is_timeouted
#             ]
