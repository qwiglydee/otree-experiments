import time
import random
from otree.api import *
from otree import settings

from .images import generate_image, distort_image, encode_image


doc = """
CAPTCHA-style transcription task
"""


class Constants(BaseConstants):
    name_in_url = "transcription"
    players_per_group = None
    num_rounds = 1

    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    instructions_template = __name__ + "/instructions.html"
    captcha_length = 3


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    captcha_length = models.IntegerField(initial=Constants.captcha_length)

    # current state of the game
    # for multi-round games: increment the round and reset iteration
    game_round = models.IntegerField(initial=0)
    game_iteration = models.IntegerField(initial=0)

    # stats are updated after game round, in before_next_page
    total = models.IntegerField(initial=0)
    correct = models.IntegerField(initial=0)
    incorrect = models.IntegerField(initial=0)


# puzzle-specific stuff


class Trial(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    length = models.FloatField()
    text = models.StringField()
    solution = models.StringField()

    # the following fields remain null for unanswered trials
    answer_timestamp = models.FloatField()
    answer = models.StringField()
    is_correct = models.BooleanField()
    retries = models.IntegerField(initial=0)


def generate_puzzle(player: Player) -> Trial:
    """Create new puzzle for a player"""
    length = player.captcha_length
    text = "".join((random.choice(Constants.characters) for _ in range(length)))
    return Trial.create(player=player, length=length, text=text, solution=text.lower(),)


def encode_puzzle(trial: Trial):
    """Create an image for a puzzle"""
    image = generate_image(trial.text)
    image = distort_image(image)
    data = encode_image(image)
    return data


def get_last_trial(player):
    """Get last (current) puzzle for a player"""
    trials = Trial.filter(
        player=player, round=player.game_round, iteration=player.game_iteration
    )
    if trials:
        return trials[-1]


def check_answer(trial: Trial, answer: str):
    """Check given answer for a puzzle and update its status"""
    if answer == "" or answer is None:
        raise ValueError("Unexpected empty answer from client")
    trial.answer = answer
    trial.is_correct = answer.lower() == trial.solution


def summarize_trials(player: Player):
    """Returns summary stats for a player

    Used to provide info for client, and to update player after a game round
    """
    total = len(Trial.filter(player=player))
    correct = len(Trial.filter(player=player, is_correct=True))
    incorrect = len(Trial.filter(player=player, is_correct=False))
    return {
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
    }


# gameplay logic


def play_game(player: Player, data: dict):
    """Handles iterations of the game on a live page

    Messages:
    - server < client {} -- empty message means page reload
    - server < client {'next': true} -- request for next (or first) puzzle
    - server > client {'image': data, 'stats': ...} -- puzzle image
    - server < client {'answer': data} -- answer to a puzzle
    - server > client {'feedback': true|false, 'stats': ...} -- feedback on the answer
    - server > client {'gameover': true} -- all iterations played
    if DEBUG=1
    - server < client {'cheat': true} -- request solution
    - server > client {'solution': str} -- solution
    """
    config = player.session.config
    trial_delay = config.get('trial_delay', 1.0)
    retry_delay = config.get('retry_delay', 1.0)
    force_solve = config.get('force_solve', False)
    allow_skip = config.get('allow_skip', False)
    allow_retry = config.get('allow_retry', False) or force_solve
    max_iter = config.get('num_iterations', 0)

    now = time.time()

    # get last trial, if any
    trial = get_last_trial(player)

    if data == {}:
        # initial load, generate first puzzle
        if not trial:
            trial = generate_puzzle(player)
            trial.timestamp = now
            trial.iteration = 1
            player.game_iteration = 1
        stats = summarize_trials(player)
        data = encode_puzzle(trial)
        return {player.id_in_group: {"image": data, "stats": stats}}

    # generate next puzzle and return image
    if "next" in data:
        if not trial:
            raise RuntimeError("Missing current puzzle!")
        if now - trial.timestamp < trial_delay:
            raise RuntimeError("Client advancing too fast!")
        if force_solve and trial.is_correct is not True:
            raise RuntimeError("Attempted to skip unsolved puzzle!")
        if not allow_skip and trial.answer is None:
            raise RuntimeError("Attempted to skip unanswered puzzle!")
        if max_iter and trial.iteration >= max_iter:
            return {player.id_in_group: {"gameover": True}}

        # new trial
        trial = generate_puzzle(player)
        trial.timestamp = now
        trial.iteration = trial.iteration + 1 if trial else 1
        player.game_iteration = trial.iteration

        # get total counters
        stats = summarize_trials(player)

        # return image
        data = encode_puzzle(trial)
        return {player.id_in_group: {"image": data, "stats": stats}}

    # check given answer and return feedback
    if "answer" in data:
        if not trial:
            raise RuntimeError("Missing current puzzle")
        if trial.answer is not None:  # retrying
            if not allow_retry:
                raise RuntimeError("Client retries the same puzzle!")
            if now - trial.answer_timestamp < retry_delay:
                raise RuntimeError("Client retrying too fast!")

        check_answer(trial, data["answer"])
        trial.answer_timestamp = now
        trial.retries += 1

        # get total counters
        stats = summarize_trials(player)

        # return feedback
        return {player.id_in_group: {'feedback': trial.is_correct, 'stats': stats}}

    if "cheat" in data and settings.DEBUG:
        if not trial:
            raise RuntimeError("Missing current puzzle")
        return {player.id_in_group: {'solution': trial.solution}}

    # otherwise
    raise ValueError("Invalid message from client!")


def custom_export(players):
    """Dumps all the puzzles generated"""
    yield [
        "session",
        "participant_code",
        "game_round",
        "game_iteration",
        "timestamp",
        "length",
        "text",
        "solution",
        "answer_timestamp",
        "answer",
        "is_correct",
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
                z.length,
                z.text,
                z.solution,
                z.answer_timestamp,
                z.answer,
                z.is_correct,
                z.retries,
            ]


# PAGES


class Intro(Page):
    pass


class Game(Page):
    timeout_seconds = 60

    live_method = play_game

    @staticmethod
    def vars_for_template(player: Player):
        session = player.session

        return dict(DEBUG=settings.DEBUG,)

    @staticmethod
    def js_vars(player: Player):
        conf = player.session.config
        return dict(
            trial_delay=conf.get('trial_delay', 1.0),
            retry_delay=conf.get('retry_delay', 1.0),
            allow_skip=conf.get('allow_skip', False),
            allow_retry=conf.get('allow_retry', False),
            force_solve=conf.get('force_solve', False),
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        stats = summarize_trials(player)
        player.total = stats['total']
        player.correct = stats['correct']
        player.incorrect = stats['incorrect']


class Results(Page):
    pass


page_sequence = [Game, Results]
