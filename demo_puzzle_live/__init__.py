import json

from otree.api import *

from common import live_utils, puzzle_utils

doc = """
Demo of puzzle app
"""


class C(BaseConstants):
    NAME_IN_URL = "demo_puzzle_live"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    INSTRUCTIONS = __name__ + "/instructions.html"

    BOARD_SIZE = 3
    INITIAL_DIFFICULTY = 2  # initial number of moves to shuffle
    GAME_TIMEOUT = 60  # seconds
    LIMIT_MOVES = True  # limit number of moves to == difficulty level

    # default values reconfigurable from session config:

    NUM_TRIALS = None  # None for infinite
    TRIAL_TIMEOUT = 10  # seconds
    POSTTRIAL_PAUSE = 1  # seconds


class Subsession(BaseSubsession):
    is_practice = models.BooleanField()


def creating_session(subsession: Subsession):
    subsession.is_practice = True

    session = subsession.session
    defaults = dict(
        num_trials=C.NUM_TRIALS,
        trial_timeout=C.TRIAL_TIMEOUT,
        post_trial_pause=C.POSTTRIAL_PAUSE,
    )
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])

    for player in subsession.get_players():
        player.cur_difficulty = C.INITIAL_DIFFICULTY


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # current iteration (a trial created and sent )
    cur_iteration = models.IntegerField(initial=0)
    cur_difficulty = models.IntegerField()

    # number of completed trials
    num_trials = models.IntegerField(initial=0)
    # number of trials whth correct responses
    num_solved = models.IntegerField(initial=0)
    # number of trials with incorrect responses
    num_failed = models.IntegerField(initial=0)
    # number of trials without response (timeouted)
    num_skipped = models.IntegerField(initial=0)


class Trial(ExtraModel):
    """A record of single puzzle task"""

    timestamp_loaded = models.FloatField()
    timestamp_completed = models.FloatField()

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)

    difficulty = models.IntegerField() # number of moves used to shuffle
    puzzle = models.StringField() # initial board state

    is_completed = models.BooleanField(initial=False) # either solved/failed or skipped

    actions = models.StringField() # sequence of users moves performed
    result = models.StringField() # resulting or current board
    is_correct = models.BooleanField()

    response_time = models.IntegerField()
    is_timeouted = models.BooleanField()


def generate_trial(player: Player) -> Trial:
    """Creates a new trial with random text"""

    difficulty = player.cur_difficulty
    board = puzzle_utils.initBoard(C.BOARD_SIZE)
    puzzle_utils.shuffleBoard(board, C.BOARD_SIZE, num_moves=difficulty)

    return Trial.create(
        round=player.round_number,
        player=player,
        iteration=player.cur_iteration,
        #
        difficulty=difficulty,
        puzzle=json.dumps(board),
        # current state:
        actions="[]",
        result=json.dumps(board)
    )


def get_trial(player: Player):
    """Gets current trial for a player"""
    trials = Trial.filter(player=player, iteration=player.cur_iteration)
    if len(trials) == 0:
        return None
    return trials[0]


def encode_trial(trial):
    # encoding current board state
    return dict(difficulty=trial.difficulty, board=json.loads(trial.result))


def validate_trial(trial):
    """Checks if a trial is correctly answered"""
    board = json.loads(trial.result)
    correct = puzzle_utils.validateBoard(board)

    trial.is_correct = correct


def get_progress(player, trial=None):
    return dict(
        total=C.NUM_TRIALS,
        current=player.cur_iteration,
        completed=player.num_trials,
        solved=player.num_solved,
        failed=player.num_failed,
        moves=trial.actions.count(",") + 1 if trial and trial.actions else 0,
    )


# PAGES


class Intro(Page):
    pass


def on_load(player: Player):
    print("loading new trial")

    current = get_trial(player)
    if current:
        if current.is_correct:
            player.cur_difficulty += 1
        elif player.cur_difficulty > 1:
            player.cur_difficulty -= 1

    player.cur_iteration += 1
    newtrial = generate_trial(player)

    print("puzzle:", newtrial.puzzle)
    return dict(trial=newtrial)


def on_move(player, trial, move, response_time):
    print("move:", move, "time:", response_time)

    board = json.loads(trial.result)
    actions = json.loads(trial.actions)

    dst = puzzle_utils.findFreeCell(board)
    src = move
    valid = puzzle_utils.validateMove(board, C.BOARD_SIZE, dst, src)

    if not valid:
        return dict(feedback=dict(error=dict(code="moveInvalid")))

    puzzle_utils.applyMoves(board, C.BOARD_SIZE, [move])
    actions.append(move)

    trial.result = json.dumps(board)
    trial.actions = json.dumps(actions)

    validate_trial(trial)

    if trial.is_correct or len(actions) == trial.difficulty:
        trial.is_completed = True

    if trial.is_completed:
        player.num_trials += 1

        if trial.is_correct is True:
            player.num_solved += 1
        else:
            player.num_failed += 1

    return dict(
        feedback=dict(
            correct=trial.is_correct, 
            final=trial.is_completed,
        ),
        update=dict(board=board)
    )


def on_timeout(player, trial):
    trial.is_timeouted = True

    validate_trial(trial)

    trial.is_completed = True

    player.num_trials += 1

    if trial.is_correct is True:
        player.num_solved += 1
    else:
        player.num_failed += 1

    return dict(feedback=dict(correct=False))


class Main(Page):
    timeout_seconds = C.GAME_TIMEOUT

    @staticmethod
    def js_vars(player):
        params = player.session.params
        return dict(
            PARAMS=dict(
                board_size=C.BOARD_SIZE,
                num_trials=params["num_trials"],
                trial_timeout=params["trial_timeout"],
                post_trial_pause=params["post_trial_pause"],
            )
        )

    live_method = live_utils.live_puzzles(
        get_trial=get_trial,
        encode_trial=encode_trial,
        on_load=on_load,
        on_move=on_move,
        on_timeout=on_timeout,
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
        "timestamp_loaded",
        "timestamp_responed",
        "iteration",
        "text",
        "response",
        "response_correct",
        "retries",
        "response_time",
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

        # yield a row for players even without trials
        yield player_fields

        for trial in trials:
            yield player_fields + [
                round(trial.timestamp_loaded, 3),
                round(trial.timestamp_completed, 3),
                trial.iteration,
                trial.text,
                trial.response,
                trial.is_correct,
                trial.retries,
                trial.response_time,
                trial.is_timeouted,
            ]
