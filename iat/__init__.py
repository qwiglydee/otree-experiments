import time
import random
from otree.api import *
from otree import settings
from .STIMULI import DICT
from .blocks import BLOCKS
from .stats import stats

doc = """
Implicit Association Test, draft
"""


class Constants(BaseConstants):
    name_in_url = 'iat'
    players_per_group = None
    num_rounds = 7

    # the keys F and J have tactile marks
    keys = {'left': "f", 'right': "j"}
    trial_delay = 0.250


class Subsession(BaseSubsession):
    practice = models.BooleanField()

    has_primary = models.BooleanField()
    primary_left = models.StringField()
    primary_right = models.StringField()

    has_secondary = models.BooleanField()
    secondary_left = models.StringField()
    secondary_right = models.StringField()


def creating_session(subsession: Subsession):
    # block have structure like
    # {'left': {'primary': 1, 'secondary': 2}, 'right': {'primary': 1, 'secondary': 2}}
    block = BLOCKS[subsession.round_number]
    # conf have structure like
    # {'primary': [category1, category2], 'secondary': [category1, category2]
    conf = subsession.session.config

    def get_cat(cls, side):
        block_side = block[side]
        if cls not in block_side:
            return ""
        idx = block_side[cls] - 1
        cat = conf[cls][idx]
        assert cat in DICT
        return cat

    subsession.practice = block['practice']
    subsession.primary_left = get_cat('primary', 'left')
    subsession.primary_right = get_cat('primary', 'right')
    subsession.secondary_left = get_cat('secondary', 'left')
    subsession.secondary_right = get_cat('secondary', 'right')

    subsession.has_primary = (
        subsession.primary_left != "" and subsession.primary_right != ""
    )
    subsession.has_secondary = (
        subsession.secondary_left != "" and subsession.secondary_right != ""
    )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    iteration = models.IntegerField(initial=1)
    num_trials = models.IntegerField(initial=0)
    num_correct = models.IntegerField(initial=0)
    num_failed = models.IntegerField(initial=0)


class Trial(ExtraModel):
    """A record of single iteration
    Keeps corner categories from round setup to simplify furher analysis.
    The stimulus class is for appropriate styling on page.
    """

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    stimulus_cls = models.StringField(choices=('primary', 'secondary'))
    stimulus_cat = models.StringField()
    stimulus = models.StringField()
    correct = models.StringField(choices=('left', 'right'))

    response = models.StringField(choices=('left', 'right'))
    response_timestamp = models.FloatField()
    reaction_time = models.FloatField()
    is_correct = models.BooleanField()
    retries = models.IntegerField(initial=0)


def generate_question(player: Player) -> Trial:
    """Create new question for a player"""
    subsession = player.subsession
    chosen_side = random.choice(['left', 'right'])
    if subsession.has_primary and subsession.has_secondary:
        chosen_cls = random.choice(['primary', 'secondary'])
    elif subsession.has_primary:
        chosen_cls = 'primary'
    elif subsession.has_secondary:
        chosen_cls = 'secondary'
    else:
        raise RuntimeError("improperly configured session")

    chosen_cat = getattr(subsession, f"{chosen_cls}_{chosen_side}")
    stimuli = DICT[chosen_cat]
    stimulus = random.choice(stimuli)

    return Trial.create(
        player=player,
        stimulus_cls=chosen_cls,
        stimulus_cat=chosen_cat,
        stimulus=stimulus,
        correct=chosen_side,
    )


def get_last_trial(player: Player):
    """Get last (current) question for a player"""
    trials = Trial.filter(player=player, iteration=player.iteration)
    trial = trials[-1] if len(trials) else None
    return trial


def get_progress(player: Player):
    """Return current player progress"""
    return dict(
        num_trials=player.num_trials,
        num_correct=player.num_correct,
        num_incorrect=player.num_failed,
        iteration=player.iteration,
    )


def encode_trial(trial: Trial):
    return {
        'cls': trial.stimulus_cls,
        'cat': trial.stimulus_cat,
        'word': trial.stimulus,
    }


def check_response(trial: Trial, response: str):
    """Check given answer for a question and update its status"""
    if response == "" or response is None:
        raise ValueError("Unexpected empty answer from client")
    trial.response = response
    trial.is_correct = response == trial.correct


# def custom_export(players):
#     """Dumps all the puzzles generated"""
#     yield [
#         "session",
#         "participant_code",
#         "round",
#         "iteration",
#         "timestamp",
#         "left primary",
#         "right primary",
#         "left secondary",
#         "right secondary",
#         "stimulus",
#         "reaction_time",
#         "retries",
#     ]
#     for p in players:
#         participant = p.participant
#         session = p.session
#         for z in Trial.filter(player=p):
#             yield [
#                 session.code,
#                 participant.code,
#                 z.round,
#                 z.iteration,
#                 z.timestamp,
#                 z.left_1,
#                 z.right_1,
#                 z.left_2,
#                 z.right_2,
#                 z.stimulus,
#                 z.reaction_time,
#                 z.retries,
#             ]


def play_game(player: Player, data: dict):
    """Handles iterations of the game on a live page

    Messages:
    - client > server {} -- empty message means page reload
    - server < client {'next': true} -- request for next (or first) question
    - server > client {'question': data, 'class': str, 'progress': data} -- stimulus and it's class 'primary' or 'secondary'
    - server < client {'answer': str, 'rt': float} -- answer to a question and reaction time
    - server > client {'feedback': true|false, 'progress': data} -- feedback on the answer
    - server > client {'gameover': true} -- all iterations played
    """
    conf = player.session.config
    trial_delay = conf.get('trial_delay', Constants.trial_delay)
    max_iter = conf['num_iterations'][player.round_number]

    now = time.time()

    # get last trial, if any
    last = get_last_trial(player)

    if data == {}:
        if last:  # reloaded in middle of round, return current question
            progress = get_progress(player)
            data = encode_trial(last)
            return {player.id_in_group: {"question": data, "progress": progress}}
        else:  # initial load, generate first question
            trial = generate_question(player)
            trial.iteration = 1
            trial.timestamp = now
            player.iteration = 1
            #
            progress = get_progress(player)
            data = encode_trial(trial)
            return {player.id_in_group: {"question": data, "progress": progress}}

    # generate next question and return image
    if "next" in data:
        if not last:
            raise RuntimeError("Missing current question!")
        if now - last.timestamp < trial_delay:
            raise RuntimeError("Client advancing too fast!")
        if max_iter and last.iteration >= max_iter:
            return {player.id_in_group: {"gameover": True}}

        # new trial
        player.iteration = last.iteration + 1
        trial = generate_question(player)
        trial.round = player.round_number
        trial.iteration = player.iteration
        trial.timestamp = now
        trial.retries = 0

        progress = get_progress(player)
        data = encode_trial(trial)
        return {player.id_in_group: {"question": data, "progress": progress}}

    # check given answer and return feedback
    if "answer" in data:
        if not last:
            raise RuntimeError("Missing current question")

        check_response(last, data["answer"])
        last.response_timestamp = now
        last.reaction_time = data['reaction']
        last.retries += 1

        progress = get_progress(player)
        return {player.id_in_group: {'feedback': last.is_correct, 'progress': progress}}

    if data.get('type') == "cheat" and settings.DEBUG:
        # generate remaining data for the round
        m = random.random() + 1.0
        for i in range(player.iteration, max_iter):
            t = generate_question(player)
            t.iteration = i
            t.timestamp = now + i
            t.response = t.correct
            t.is_correct = True
            t.response_timestamp = now + i
            t.reaction_time = random.gauss(m, 0.250)
        return {player.id_in_group: {"gameover": True}}

    # otherwise
    raise ValueError("Invalid message from client!")


# PAGES


class Intro(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class RoundN(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        conf = player.session.config
        return dict(
            keys=Constants.keys,
            trial_delay=conf.get('trial_delay', Constants.trial_delay),
        )

    @staticmethod
    def vars_for_template(player: Player):
        rnd = player.round_number
        conf = player.session.config
        block = BLOCKS[rnd]
        return dict(
            block=block,
            round_length=conf['num_iterations'][rnd],
            keys=Constants.keys,
            DEBUG=settings.DEBUG,
        )

    live_method = play_game


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 7

    @staticmethod
    def vars_for_template(player: Player):
        trials3 = Trial.filter(player=player.in_round(3))
        trials4 = Trial.filter(player=player.in_round(4))
        trials6 = Trial.filter(player=player.in_round(6))
        trials7 = Trial.filter(player=player.in_round(7))

        def aggregate(trials):
            values = [t.reaction_time for t in trials]
            if len(values) == 0:
                return None
            m, s = stats(values)
            return dict(mean=m, std=s)

        return dict(
            data=dict(
                round3=aggregate(trials3),
                round4=aggregate(trials4),
                round6=aggregate(trials6),
                round7=aggregate(trials7),
            )
        )


page_sequence = [Intro, RoundN, Results]
