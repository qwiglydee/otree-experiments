"""Magic utilities to simplify live page development

The decorators: 
- live_page
- live_trials
- live_trials_preloaded
- live_puzzles

They modify page classes and add live_method to handle generic app of specified type.

Usage:

```
@live_trials
class MyPage(Page):
    define some required staticmethods here 
```

See docs for specific decorator for detail.
"""

from lib2to3.pytree import Base
from otree.api import BasePlayer

def defaultmethod(cls):
    """Adds a method to the class, if it's missing"""

    def decorator(fn):
        if not hasattr(cls, fn.__name__):
            setattr(cls, fn.__name__, staticmethod(fn))
        return None  # prevent accident referencing

    return decorator


def wrappedmethod(cls):
    """Adds a method to the class, with reference to original"""

    def decorator(fn):
        orig = getattr(cls, fn.__name__, None)

        def wrapped(*args, **kwargs):
            return fn(orig, *args, **kwargs)

        setattr(cls, fn.__name__, staticmethod(wrapped))
        return None  # prevent accident referencing

    return decorator


def live_page(pagecls):
    """Decorator to make page class a very generic live page.

    The live page receives messages in format: `{ type: sometype, fields: ... }`
    Both incoming and outgoing messages can be batched together into lists.

    Each message is delegated to class methods `handle_sometype(player, message)` that should be defined in a page class.

    Return value from handlers should be:
    ```
    {
        destination: {        # destination player, role, or 0 for all or 'other players' (not directly addressed)
            type: {           # type of message to send back
                field: value  # data for the messages
            }
        }
    }

    The messages send back according to return value.
    """

    def generic_live_method(player: BasePlayer, message: dict):
        assert isinstance(message, dict) and "type" in message

        msgtype = message["type"]
        hndname = f"handle_{msgtype}"

        if not hasattr(pagecls, hndname):
            raise NotImplementedError(f"missing method {hndname}")

        handler = getattr(pagecls, hndname)

        response = handler(player, message)

        sending = {}

        for rcpt, msgdict in response.items():
            sending[rcpt] = []
            for type, data in msgdict.items():
                if data is None:
                    continue
                msg = {"type": type}
                msg.update(data)
                sending[rcpt].append(msg)

        group = player.group


        def expand_roles(sending):
            return {
                (group.get_player_by_role(rcpt) if isinstance(rcpt, str) else rcpt) : data 
                for rcpt, data in sending.items()
            }

        def expand_others(sending):
            if len(sending) == 1 or 0 not in sending:
                return sending

            addressed = list(filter(lambda p: p != 0, sending.keys()))
            others = list(filter(lambda p: p not in addressed, group.get_players()))

            expanded = { p: sending[p] for p in addressed }
            expanded.update({ p: sending[0] for p in others })
            return expanded

        def expand_ids(sending):
            return { 
                (rcpt.id_in_group if isinstance(rcpt, BasePlayer) else rcpt) : data 
                for rcpt, data in sending.items() 
            }

        sending = expand_roles(sending)
        sending = expand_others(sending)
        sending = expand_ids(sending)

        return sending

    pagecls.live_method = staticmethod(generic_live_method)

    return pagecls


def live_trials(pagecls):
    """Decorator to setup a page class to handle generic live trials

    Expected trial model fields:
    - iteration = models.IntegerField(initial=0)
    - is_completed = models.BooleanField(initial=False)
    - is_timeouted = models.BooleanField(initial=False)
    - is_skipped = models.BooleanField(initial=False)
    - is_successful = models.BooleanField(initial=None)

    Expected class attributes:

    - trial_model: a class of trial model, should have fields
    - trial_fields: (optional) a list of fields of model to send to browser

    Expected class static methods:

    def validate_response(trial, response):
        # the response is dict: { input, rt, timeout_happened }
        # updates trial according to response and return feedback

    feedback: {
      responseCorrect: bool,  # indicates if the particular input is correct
      responseFinal: bool,    # indicates no more responses for this trial allowed
      input: any  # fixed/normalized input value, or a no-go option
    }

    # optional
    def get_trial(player, iteration):
        # returns current trial for a player
        # by default, gets a trial according to current iteration

    # optional
    def new_trial(player, iteration):
        # generates new trial for a player or returns None when no more trials and game is over
        # by default no new trials generated, instead using pregenerated

    # optional
    def encode_trial(trial):
        # returns a dict to send to players browser
        # by default, uses trial_fields

    # optional
    def get_progress(player):
        # returns progress for a player
        # suggested fields:
        # - current: current iteration
        # - completed: number of completed trials
        # - succeeded: number of succesfully completed trial s
        # - failed: number of failed trials
        # by default, only current iteration is returned
        # the current iteration is also automatically added to any custom feedback
    """

    @defaultmethod(pagecls)
    def get_trial(player, iteration):
        trials = pagecls.trial_model.filter(player=player, iteration=iteration)
        if len(trials) == 0:
            return None
        if len(trials) > 1:
            raise ValueError("trials messed up")
        return trials[0]

    @defaultmethod(pagecls)
    def new_trial(player, iteration):
        return pagecls.get_trial(player, iteration)

    @defaultmethod(pagecls)
    def encode_trial(trial):
        return {f: getattr(trial, f) for f in pagecls.trial_fields}

    @defaultmethod(pagecls)
    def get_progress(player, iteration):
        return {"current": iteration}

    @defaultmethod(pagecls)
    def validate_response(trial):
        raise TypeError("@live_trials class require validate_response static method")

    #### live methods of the trials logic

    @defaultmethod(pagecls)
    def handle_load(player, message):
        iteration = player.participant.iteration
        progress = pagecls.get_progress(player, iteration)

        curtrial = pagecls.get_trial(player, iteration)

        if curtrial is not None and not curtrial.is_completed:
            return {player: dict(trial=pagecls.encode_trial(curtrial), progress=progress)}

        newtrial = pagecls.new_trial(player, iteration + 1)

        if newtrial is None:
            return {player: dict(status=dict(gameOver=True), progress=progress)}  # prev step progress

        player.participant.iteration += 1
        progress["current"] += 1
        return {player: dict(trial=pagecls.encode_trial(newtrial), progress=progress)}

    @defaultmethod(pagecls)
    def handle_response(player, message):
        iteration = player.participant.iteration

        if message["iteration"] != iteration:
            raise RuntimeError("Trial sequence messsed up")

        curtrial = pagecls.get_trial(player, iteration)

        if curtrial is None:
            raise RuntimeError("Responding to missing trial")
        if curtrial.is_completed:
            raise RuntimeError("Responsing to already completed trial")

        responses = {}
        responses['feedback'] = pagecls.validate_response(curtrial, response=message, timeout_happened=False)
        responses['progress'] = pagecls.get_progress(player, iteration)

        if curtrial.is_completed:
            # FIXME: send only changed status
            responses['status'] = dict(
                trialCompleted=True,
                trialSuccessful=curtrial.is_successful,
                trialSkipped=curtrial.is_skipped,
                trialTimeouted=curtrial.is_timeouted,
            )

        return {player: responses}


    @defaultmethod(pagecls)
    def handle_timeout(player, message):
        iteration = player.participant.iteration

        if message["iteration"] != iteration:
            raise RuntimeError("Trial sequence messsed up")

        curtrial = pagecls.get_trial(player, iteration)

        if curtrial is None:
            raise RuntimeError("Timeouting missing trial")
        if curtrial.is_completed:
            raise RuntimeError("Timeouting already completed trial")

        responses = {}
        responses['feedback'] = pagecls.validate_response(curtrial, response=None, timeout_happened=True)
        responses['progress'] = pagecls.get_progress(player, iteration)

        assert curtrial.is_completed, "timeouted trials should be marked completed"

        # FIXME: send only changed status
        responses['status'] = dict(
            trialCompleted=True,
            trialSuccessful=curtrial.is_successful,
            trialSkipped=curtrial.is_skipped,
            trialTimeouted=curtrial.is_timeouted,
        )

        return {player: responses}

    ####

    @wrappedmethod(pagecls)
    def js_vars(orig_js_vars, player):
        """initialize iteration when age is loaded"""
        player.participant.iteration = 0
        return orig_js_vars(player) if orig_js_vars else None

    return live_page(pagecls)


def live_trials_preloaded(pagecls):
    """Decorator to setup a page class to handle generic preloaded trials

    The same as @live_trials, but the 'load' message is responded with all trials data.
    Other messages don't get any response, so validate_response don't need to return feedback.

    Expected class static methods:

    def get_all_trials(player):
        # returns current trial for a player
        # by default, gets all uncompleted trials for player

    The rest is the same as @live_trials

    """

    @defaultmethod(pagecls)
    def get_all_trials(player):
        return pagecls.trial_model.filter(player=player, is_completed=False)

    ####
    @defaultmethod(pagecls)
    def handle_response(player, message):
        iteration = message["iteration"]

        curtrial = pagecls.get_trial(player, iteration)

        if curtrial is None:
            raise RuntimeError("Responding to missing trial")
        if curtrial.is_completed:
            raise RuntimeError("Responsing to already completed trial")

        pagecls.validate_response(curtrial, response=message, timeout_happened=False)

        return dict()

    @defaultmethod(pagecls)
    def handle_timeout(player, message):
        iteration = message["iteration"]

        curtrial = pagecls.get_trial(player, iteration)

        if curtrial is None:
            raise RuntimeError("Timeouting missing trial")
        if curtrial.is_completed:
            raise RuntimeError("Timeouting already completed trial")

        progress = pagecls.get_progress(player, iteration)

        feedback = pagecls.validate_response(curtrial, response=None, timeout_happened=True)

        assert curtrial.is_completed, "timeouted trials should be marked completed"

        return dict()

    @defaultmethod(pagecls)
    def handle_load(player, message):
        trials = pagecls.get_all_trials(player)
        return {player: dict(trials=dict(data=[pagecls.encode_trial(t) for t in trials]))}

    return live_trials(pagecls)


def live_puzzles(pagecls):
    """Decorator to setup a page class to handle generic live puzzles (multi-step tasks)

    Work basically as live_trials, but in addition to feedback it sends update message.


    Expected class static methods:

    def validate_response(trial, response):
        # the response is dict: { input, rt, timeout_happened }
        # updates trial according to response and return feedback and update
        # like:
        return dict(responseCorrect), {'trial.something': newvalue }
    """

    #### live methods of the puzzle logic

    @defaultmethod(pagecls)
    def handle_response(player, message):
        iteration = player.participant.iteration

        if message["iteration"] != iteration:
            raise RuntimeError("Trial sequence messsed up")

        curtrial = pagecls.get_trial(player, iteration)

        if curtrial is None:
            raise RuntimeError("Responding to missing trial")
        if curtrial.is_completed:
            raise RuntimeError("Responsing to already completed trial")

        responses = pagecls.validate_response(curtrial, response=message, timeout_happened=False)
        responses['progress'] = pagecls.get_progress(player, iteration)

        if curtrial.is_completed:
            # FIXME: send only changed status
            responses['status'] = dict(
                trialCompleted=True,
                trialSuccessful=curtrial.is_successful,
                trialSkipped=curtrial.is_skipped,
                trialTimeouted=curtrial.is_timeouted,
            )
        
        return {player: responses}


    @defaultmethod(pagecls)
    def handle_timeout(player, message):
        iteration = player.participant.iteration

        if message["iteration"] != iteration:
            raise RuntimeError("Trial sequence messsed up")

        curtrial = pagecls.get_trial(player, iteration)

        if curtrial is None:
            raise RuntimeError("Timeouting missing trial")
        if curtrial.is_completed:
            raise RuntimeError("Timeouting already completed trial")


        responses = pagecls.validate_response(curtrial, response=None, timeout_happened=True)
        responses['progress'] = pagecls.get_progress(player, iteration)
        
        assert curtrial.is_completed, "timeouted trials should be marked completed"

        # FIXME: send only changed status
        responses['status'] = dict(
            trialCompleted=True,
            trialSuccessful=curtrial.is_successful,
            trialSkipped=curtrial.is_skipped,
            trialTimeouted=curtrial.is_timeouted,
        )
        
        return {player: responses}

    ####

    return live_trials(pagecls)
