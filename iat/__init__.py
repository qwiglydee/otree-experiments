import time
import random
from otree.api import *
from .STIMULI import WORDS

doc = """
Implicit Association Test, draft
"""


class Constants(BaseConstants):
    name_in_url = 'iat'
    players_per_group = None
    num_rounds = 1

    # the keys F and J have tactile marks
    keys = {'left': "f", 'right': "j"}
    trial_delay = 0.250


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # current state of the game
    game_round = models.IntegerField(initial=1)
    game_iteration = models.IntegerField(initial=1)


# experiment data and utilities


class Trial(ExtraModel):
    """A record of single iteration
    Keeps corner categories from round setup to simplify furher analysis.
    The stimulus class is for appropriate styling on page.
    """

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    practice = models.BooleanField()
    iteration = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    # primary category
    left_1 = models.StringField()
    right_1 = models.StringField()
    # secondary category
    left_2 = models.StringField()
    right_2 = models.StringField()

    stimulus_class = models.StringField(choices=('primary', 'secondary'))
    stimulus = models.StringField()
    correct = models.StringField(choices=('left', 'right'))

    answer = models.StringField(choices=('left', 'right'))
    reaction_time = models.FloatField()
    is_correct = models.BooleanField()
    retries = models.IntegerField(initial=0)


# classic setup of rounds
# 'primary' and 'secondary' are configured in session as pairs of dictionary categories
# numbers refer to positions in the pairs
BLOCKS = {
    1: {
        'title': "Round 1 (practice)",
        'practice': True,
        'left': {'primary': 1},
        'right': {'primary': 2},
    },
    2: {
        'title': "Round 2 (practice)",
        'practice': True,
        'left': {'secondary': 1},
        'right': {'secondary': 2},
    },
    3: {
        'title': "Round 3",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    4: {
        'title': "Round 4",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    5: {
        'title': "Round 5 (practice)",
        'practice': True,
        'left': {'secondary': 2},
        'right': {'secondary': 1},
    },
    6: {
        'title': "Round 6",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
    7: {
        'title': "Round 7",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
}


def setup_round(player: Player):
    """Return current round setup (the corner categories)"""

    block = BLOCKS[player.game_round]
    # conf[*] contains pairs of keys from words dictionary, like ['male', 'female']
    conf = player.session.config
    # mapping of categories from block setup to categories from dictionary
    categories = {
        'left': {'primary': None, 'secondary': None},
        'right': {'primary': None, 'secondary': None},
    }
    for side in ('left', 'right'):
        for cls in ('primary', 'secondary'):
            if cls in block[side]:
                pick = block[side][cls] - 1
                categories[side][cls] = conf[cls][pick]
            else:  # skipped, remove the key
                del categories[side][cls]

    return categories


def generate_question(player: Player) -> Trial:
    """Create new question for a player"""
    block = BLOCKS[player.game_round]
    categories = setup_round(player)
    # expected answer
    chosen_side = random.choice(['left', 'right'])
    # 'primary'|'secondary' whichever present
    chosen_cls = random.choice(list(categories[chosen_side].keys()))
    # real dictionary category
    chosen_cat = categories[chosen_side][chosen_cls]

    words = WORDS[chosen_cat]
    word = random.choice(words)

    return Trial.create(
        player=player,
        practice=block['practice'],
        left_1=categories['left'].get('primary'),
        left_2=categories['left'].get('secondary'),
        right_1=categories['right'].get('primary'),
        right_2=categories['right'].get('secondary'),
        stimulus_class=chosen_cls,
        stimulus=word,
        correct=chosen_side,
    )


def get_last_trial(player):
    """Get last (current) question for a player"""
    trials = Trial.filter(
        player=player, round=player.game_round, iteration=player.game_iteration
    )
    trial = trials[-1] if len(trials) else None
    return trial


def get_progress(player: Player):
    """Returns summary progress progress for a player"""
    conf = player.session.config
    total = conf['num_iterations'][player.game_round]
    answered = len(
        Trial.filter(player=player, round=player.game_round, is_correct=True)
    )
    return {
        'round': player.game_round,
        'iteration': player.game_iteration,
        'total': total,
        'answered': answered,
    }


def encode_question(trial: Trial):
    # not encoding anything superfluous
    return {
        'cls': trial.stimulus_class,
        'word': trial.stimulus,
    }


def check_answer(trial: Trial, answer: str):
    """Check given answer for a question and update its status"""
    if answer == "" or answer is None:
        raise ValueError("Unexpected empty answer from client")
    trial.answer = answer
    trial.is_correct = answer == trial.correct


def custom_export(players):
    """Dumps all the puzzles generated"""
    yield [
        "session",
        "participant_code",
        "round",
        "iteration",
        "timestamp",
        "left primary",
        "right primary",
        "left secondary",
        "right secondary",
        "stimulus",
        "reaction_time",
        "retries",
    ]
    for p in players:
        participant = p.participant
        session = p.session
        for z in Trial.filter(player=p):
            yield [
                session.code,
                participant.code,
                z.round,
                z.iteration,
                z.timestamp,
                z.left_1,
                z.right_1,
                z.left_2,
                z.right_2,
                z.stimulus,
                z.reaction_time,
                z.retries,
            ]


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
    max_iter = conf['num_iterations'][player.game_round]

    now = time.time()

    # get last trial, if any
    last = get_last_trial(player)

    if data == {}:
        if last:  # reloaded in middle of round, return current question
            progress = get_progress(player)
            data = encode_question(last)
            return {player.id_in_group: {"question": data, "progress": progress}}
        else:  # initial load, generate first question
            trial = generate_question(player)
            trial.round = player.game_round
            trial.iteration = 1
            trial.timestamp = now
            player.game_iteration = 1
            #
            progress = get_progress(player)
            data = encode_question(trial)
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
        player.game_iteration = last.iteration + 1
        trial = generate_question(player)
        trial.round = player.game_round
        trial.iteration = player.game_iteration
        trial.timestamp = now
        trial.retries = 0

        progress = get_progress(player)
        data = encode_question(trial)
        return {player.id_in_group: {"question": data, "progress": progress}}

    # check given answer and return feedback
    if "answer" in data:
        if not last:
            raise RuntimeError("Missing current question")

        check_answer(last, data["answer"])
        last.answer_timestamp = now
        last.reaction_time = data['reaction']
        last.retries += 1

        progress = get_progress(player)
        return {player.id_in_group: {'feedback': last.is_correct, 'progress': progress}}

    # otherwise
    raise ValueError("Invalid message from client!")


# PAGES


def vars_for_template(player: Player):
    conf = player.session.config
    block = BLOCKS[player.game_round]
    categories = setup_round(player)
    return dict(
        round=player.game_round,
        length=conf['num_iterations'][player.game_round],
        title=block['title'],
        practice=block['practice'],
        categories=categories,
        left_categories=list(categories['left'].values()),
        right_categories=list(categories['right'].values()),
        keys=Constants.keys,
    )


def js_vars(player: Player):
    conf = player.session.config
    return dict(
        keys=Constants.keys, trial_delay=conf.get('trial_delay', Constants.trial_delay)
    )


class Round1(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        return js_vars(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.game_round = 1
        player.game_iteration = 0
        return vars_for_template(player)

    live_method = play_game


class Round2(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        return js_vars(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.game_round = 2
        player.game_iteration = 0
        return vars_for_template(player)

    live_method = play_game


class Round3(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        return js_vars(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.game_round = 3
        player.game_iteration = 0
        return vars_for_template(player)

    live_method = play_game


class Round4(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        return js_vars(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.game_round = 4
        player.game_iteration = 0
        return vars_for_template(player)

    live_method = play_game


class Round5(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        return js_vars(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.game_round = 5
        player.game_iteration = 0
        return vars_for_template(player)

    live_method = play_game


class Round6(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        return js_vars(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.game_round = 6
        player.game_iteration = 0
        return vars_for_template(player)

    live_method = play_game


class Round7(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def js_vars(player: Player):
        return js_vars(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.game_round = 7
        player.game_iteration = 0
        return vars_for_template(player)

    live_method = play_game


page_sequence = [Round1, Round2, Round3, Round4, Round5, Round6, Round7]
