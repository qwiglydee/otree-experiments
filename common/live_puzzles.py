

def live_puzzles(pagecls):
    """Decorator to setup a page class to handle generic live puzzles

    Similar to live_trials with another validation methods:

    def validate_action(trial, response):
        # called when a single move is received
        # the response is dict: { action, rt, timeout_happened }
        # should validate the action, update trial and return feedback

    def validate_solution(trial, response):
        # called when a complete solution is received
        # the response is dict: { solution, rt, timeout_happened }
        # should validate the solution, update trial and return feedback

    The rest is the same as for @live_trials
    """

    @defaultmethod(pagecls)
    def validate_action(trial):
        raise TypeError("@live_puzzles class require validate_action static method")


    @defaultmethod(pagecls)
    def validate_solution(trial):
        raise TypeError("@live_puzzles class require validate_solution static method")


    @defaultmethod(pagecls)
    def handle_response(player, message):
        iteration = player.participant.iteration
        trial = pagecls.get_trial(player, iteration)

        if trial is None:
            raise RuntimeError("Responding to missing trial")
        if trial.is_completed:
            raise RuntimeError("Responsing to already completed trial")
        if trial.iteration != message['iteration']:
            raise RuntimeError("Responsing to mismatched iteration")

        progress=pagecls.get_progress(player, iteration)

        if 'action' in message:
            feedback = pagecls.validate_trial(trial, message, message.get('timeout_happened', False))
        elif 'solution' in message:
            feedback = pagecls.validate_trial(trial, message, message.get('timeout_happened', False))
        else:
            raise ValueError("Unrecognized response for live_puzzles")
        
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

    return live_trials(pagecls)