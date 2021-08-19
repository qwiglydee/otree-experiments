import time
import random

from otree.api import *
from otree import settings

from . import stimuli

doc = """
Generic atimulus/response app
"""


class Constants(BaseConstants):
    name_in_url = "generic"
    players_per_group = None
    num_rounds = 1

    """possible choices 
    both for stimuli categories and responses
    should be associated with actual categories from pool in session config: 
    `categories={'left': something, 'right': something}`
    """
    choices = ["left", "right"]

    """Mapping of keys to choices
    the key names to use to match KeyboardEvent
    possible key names reference and compatibility: 
    https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code/code_values
    """
    keymap = {'KeyF': 'left', 'KeyJ': 'right'}


C = Constants


class Subsession(BaseSubsession):
    is_practice = models.BooleanField(initial=False)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)
    num_trials = models.IntegerField(initial=0)
    num_solved = models.IntegerField(initial=0)
    num_failed = models.IntegerField(initial=0)


class Trial(ExtraModel):
    """A record of single iteration"""

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    stimulus = models.StringField()
    category = models.StringField()
    solution = models.StringField()

    response_timestamp = models.FloatField()
    response = models.StringField()
    reaction_time = models.FloatField()
    is_correct = models.BooleanField()


def creating_session(subsession: Subsession):
    session = subsession.session
    defaults = dict(retry_delay=0.5, trial_delay=0.5, num_iterations=100)
    required = ["categories"]
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])
    for param in required:
        session.params[param] = session.config[param]

    subsession.is_practice = True

    # TODO: load/initialize stimuli sequence


def get_progress(player: Player) -> dict:
    """Return whatever progress data to show on page"""
    params = player.session.params
    return dict(
        iteration=player.iteration,
        iterations_total=params["num_iterations"],
        # num_trials=player.num_trials,
        # num_solved=player.num_solved,
        # num_failed=player.num_failed,
    )


def update_stats(player: Player, is_correct: bool, inc=1):
    """Update player stats

    if inc==-1 then it's about to undo stats, used for retries
    """
    player.num_trials += inc
    if is_correct:
        player.num_solved += inc
    else:
        player.num_failed += inc


def generate_trial(player: Player) -> Trial:
    """Create new trial with random stimuli"""
    params = player.session.params
    target_side = random.choice(C.choices)
    target_cat = params['categories'][target_side]
    targets = stimuli.filter_by_category(target_cat)
    target = random.choice(targets)

    return Trial.create(
        round=player.round_number,
        player=player,
        iteration=player.iteration,
        timestamp=time.time(),
        #
        stimulus=target['stimulus'],
        category=target['category'],
        solution=target_side,
    )


def generate_trials_batch(player: Player, count):
    """Create `count` trials with non-repeating random stimuli"""
    # TODO
    pass


def get_current_trial(player: Player) -> Trial:
    """Get trial for current iteration, or None"""
    trials = Trial.filter(player=player, iteration=player.iteration)
    if trials:
        [trial] = trials
        return trial


def encode_trial(trial: Trial) -> dict:
    """Get trial data to pass to live page"""
    return dict(stimulus=trial.stimulus)


def check_response(trial: Trial, response: str) -> bool:
    """Check if the response is correct"""
    return trial.solution == response


def play_game(player: Player, message: dict):
    """Main task workflow on the live page
    Implemented as reactive scheme: receive message from browser, react, respond.

    Generic task workflow, from server point of view:

    - receive: {'type': 'load'} -- the page has been loaded
    - check if it's game start or page refresh midgame
    - respond: {'type': 'status', 'progress': status}
    - respond: {'type': 'status', 'progress': status, 'trial': data} -- in case of midgame page reload

    - receive: {'type': 'new'} -- request for a new (or first) trial
    - generate new trial
    - respond: {'type': 'trial', 'trial': data}
    - respond: {'type': 'status', 'game_over': True} -- if num_iterations exhausted

    - receive: {'type': 'response', 'response': ..., 'reaction_time': ...} -- user responded
    - check and record response
    - respond: {'type': 'feedback', 'is_correct': true|false} -- feedback to the answe r

    Field 'progress' is added to all server responses.
    """
    params = player.session.params
    now = time.time()
    current = get_current_trial(player)

    message_type = message["type"]

    # print("iteration:", player.iteration, "trial:", current)
    # print("received:", message)

    def respond(msgtype, **fields):
        """Prepare message to send to current player, add progress"""
        msgdata = {"type": msgtype, "progress": get_progress(player)}
        msgdata.update(fields)
        # print("response:", msgdata)
        return {player.id_in_group: msgdata}

    if message_type == "load":  # client loaded page
        if current:
            return respond("status", trial=encode_trial(current))
        else:
            return respond("status")

    if message_type == "new":  # client requests new trial
        if current is not None:
            if current.response is None:
                raise RuntimeError("trying to skip unanswered trial")
            if now < current.timestamp + params["trial_delay"]:
                raise RuntimeError("retrying too fast")
            if current.iteration == params["num_iterations"]:
                return respond("status", game_over=True)

        player.iteration += 1
        t = generate_trial(player)
        return respond("trial", trial=encode_trial(t))

    if message_type == "response":  # client responded current trial
        if current is None:
            raise RuntimeError("response without trial")

        if current.response is not None:  # it's a retry
            if now < current.response_timestamp + params["retry_delay"]:
                raise RuntimeError("retrying too fast")

            # undo last update
            update_stats(player, current.is_correct, -1)

        response = message["response"]

        if response == "" or response is None:
            raise ValueError("bogus response")

        current.response = response
        current.reaction_time = message["reaction_time"]
        current.is_correct = check_response(current, response)
        current.response_timestamp = now

        update_stats(player, current.is_correct)

        return respond("feedback", is_correct=current.is_correct)

    if message_type == "cheat" and settings.DEBUG:  # debugging
        if current:
            current.delete()  # noqa
        cheat_responses(player, message)
        return respond('status', game_over=True)

    raise RuntimeError("unrecognized message from client")


def cheat_responses(player, message):
    """generate random responses for all remaining iterations in round"""
    params = player.session.params
    now = time.time()
    rt_mean = float(message['rt'])
    rt_std = min(rt_mean, 1.0 - rt_mean)
    responses = [params['left_category'], params['right_category']]
    for i in range(player.iteration, params['num_iterations']):
        ts = now + i
        rt = max(0.001, random.gauss(rt_mean, rt_std))

        t = generate_trial(player)
        t.iteration = i
        t.timestamp = ts
        t.response_timestamp = ts + rt
        t.reaction_time = rt
        t.response = random.choice(responses)
        t.is_correct = check_response(t, t.response)


class Main(Page):
    @staticmethod
    def js_vars(player: Player):
        params = player.session.params
        return dict(params=params, keymap=C.keymap)

    @staticmethod
    def vars_for_template(player: Player):
        params = player.session.params
        return dict(params=params, keymap=C.keymap, DEBUG=settings.DEBUG)

    live_method = play_game


page_sequence = [Main]


def custom_export(players):
    yield [
        "participant_code",
        "is_bot",
        "is_dropout",
        "session",
        "round",
        "is_practice",
        "player",
        "iteration",
        "timestamp",
        "stimulus",
        "category",
        "response_timestamp",
        "response",
        "response_correct",
        "reaction_time",
    ]
    for player in players:
        participant = player.participant
        session = player.session
        subsession = player.subsession

        player_fields = [
            participant.code,
            participant._is_bot,  # noqa
            participant.is_dropout if 'is_dropout' in participant.vars else None,
            session.code,
            subsession.round_number,
            subsession.is_practice,
            player.id,
        ]

        # yield a line for players even without trials
        yield player_fields

        for trial in Trial.filter(player=player):
            yield player_fields + [
                trial.iteration,
                trial.timestamp,
                trial.stimulus,
                trial.category,
                trial.response_timestamp,
                trial.response,
                trial.is_correct,
                trial.reaction_time,
            ]
