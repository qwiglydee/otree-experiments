from lib2to3.pytree import Base
from otree.api import BasePlayer


def live_page(pagecls):
    """Decorator to add generic live_method to a Page class

    The live page receives messages in format: `{ type: sometype, fields: ... }`
    Both incoming and outgoing messages can be batched together into lists.

    Each message is delegated to class methods `handle_sometype(player, message)` that should be defined in a page class.

    Return value from handlers should be:
    ```
    { 
        destination: {        # destination player, or 0 for broadcast
            type: {           # type of message to send back
                field: value  # data for the messages
            }
        }
    } 

    The messages send back according to return value.
    """

    def generic_live_method(player, message):
        assert isinstance(message, dict) and "type" in message

        msgtype = message["type"]
        hndname = f"handle_{msgtype}"

        if not hasattr(pagecls, hndname):
            raise NotImplementedError(f"missing method {hndname}")

        handler = getattr(pagecls, hndname)

        response = handler(player, message)

        senddata = {}

        for rcpt, msgdict in response.items():
            if isinstance(rcpt, BasePlayer):
                rcpt = rcpt.id_in_group
            senddata[rcpt] = []
            
            for type, data in msgdict.items():
                msg = { 'type': type }
                msg.update(data)
                senddata[rcpt].append(msg)
            
        return senddata

    pagecls.live_method = staticmethod(generic_live_method)

    return pagecls


def live_trials(pagecls):
    """Decorator to setup a page class to handle generic live trials

    Expected class attributes:
    
    - trial_model: a class of trial model, should have fields `player`, `iteration`, `is_completed`
    - trial_fields: (optional) a list of fields of model to send to browser

    Expected class static methods:

    def validate_trial(trial, response):
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

    if not hasattr(pagecls, 'get_trial'):
        def get_trial(player, iteration):
            trials = pagecls.trial_model.filter(player=player, iteration=iteration)
            if len(trials) == 0:
                return None
            if len(trials) > 1:
                raise ValueError("trials messed up")
            return trials[0]

        pagecls.get_trial = staticmethod(get_trial)

    if not hasattr(pagecls, 'new_trial'):
        def new_trial(player, iteration):
            return get_trial(player, iteration)
        pagecls.new_trial = staticmethod(new_trial)

    if not hasattr(pagecls, 'encode_trial'):
        def encode_trial(trial):
            return { f: getattr(trial, f) for f in pagecls.trial_fields }
        
        pagecls.encode_trial = staticmethod(encode_trial)

    if not hasattr(pagecls, 'get_progress'):
        def get_progress(player):
            return dict(current=player.participant.iteration)
    else:
        orig_progress = pagecls.get_progress
        def get_progress(player):
            progress = orig_progress(player)
            progress['current'] = player.participant.iteration
            return progress

    pagecls.get_progress = staticmethod(get_progress)

    if not hasattr(pagecls, 'validate_trial'):
        raise TypeError("@live_trials class require validate_trial static method")

    #### live methods of the trials logic 

    def handle_load(player, message):
        trial = pagecls.get_trial(player, player.participant.iteration)
        progress=pagecls.get_progress(player)

        # current trial
        if trial is not None and not trial.is_completed:
            return {player: dict(
                trial=pagecls.encode_trial(trial),
                progress=progress
            )}

        # next trial            
        player.participant.iteration += 1

        trial = pagecls.new_trial(player, player.participant.iteration)
        
        if trial is None:
            return {player: dict(
                status=dict(gameOver=True),
                progress=progress  # last step progress
            )}

        progress['current'] = player.participant.iteration        
        return {player: dict(
            trial=pagecls.encode_trial(trial),
            progress=progress
        )}

    pagecls.handle_load = staticmethod(handle_load) 

    def handle_response(player, message):
        trial = pagecls.get_trial(player, player.participant.iteration)

        if trial is None:
            raise RuntimeError("Responding to missing trial")
        if trial.is_completed:
            raise RuntimeError("Responsing to already completed trial")

        progress=pagecls.get_progress(player)

        feedback = pagecls.validate_trial(trial, message)
        
        if trial.is_completed:
            return {player: dict(
                feedback=feedback,
                status=dict(
                    trialCompleted=True, 
                    trialSuccessful=trial.is_successful, 
                    trialSkipped=trial.response is None),
                progress=progress
            )}
        else: 
            return {player: dict(
                feedback=feedback,
                progress=progress
            )}

    pagecls.handle_response = staticmethod(handle_response)

    ####

    orig_js_vars = pagecls.js_vars
    def wrapped_js_vars(player):
        player.participant.iteration = 0
        return orig_js_vars(player)
    pagecls.js_vars = staticmethod(wrapped_js_vars)

    return live_page(pagecls)