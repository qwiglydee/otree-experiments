from time import time as now

def make_response(player, data):
  messages = []
  for type, datum in data.items():
    message = dict(type=type)
    message.update(datum)
    messages.append(message)

  if len(messages) == 1 :
    messages = messages[0]

  if player:
    return { player.id_in_group: messages }
  else:
    return { 0: messages }


def live_method(*, on_load, on_input, on_timeout, on_reload=None):

  def method(player, message):
    if not isinstance(message, dict) or 'type' not in message:
        raise ValueError("Invalid message")

    if message['type'] not in ('load', 'reload', 'input', 'timeout'):
        raise ValueError("Invalid message type")

    msg_type = message.get('type')

    if msg_type == 'load':
      data = on_load(player)
      return make_response(player, data)

    if msg_type == 'input':
      data = on_input(player, message.get('input'), message.get('response_time'))
      return make_response(player, data)

    if msg_type == 'timeout':
      data = on_timeout(player)
      return make_response(player, data)

    if msg_type == 'reload':
      data = on_reload(player)
      return make_response(player, data)

    raise NotImplementedError(f"No handler for {msg_type}")

  return staticmethod(method)


def live_trials(*, get_trial, encode_trial, get_progress, on_load, on_input, on_timeout, on_reload=None):
  """Creates a live_method for live trials.

  Checks various errors such as max_retries, max iterations.
  Automatically adds proper status and progress to responses, serializes trial.
  """

  def trials_on_load(player):
    params = player.session.params
    num_trials = params['num_trials']

    if num_trials and player.cur_iteration >= num_trials:
      raise RuntimeError("Maximum iterations exhausted")

    curtrial = get_trial(player)
    if curtrial is not None and not curtrial.is_completed:
        raise RuntimeError("Overstepping uncompleted trial")

    resp = on_load(player)
    trial = resp['trial']
    trial.timestamp_loaded = now()
    resp['trial'] = encode_trial(trial)
    resp['progress'] = get_progress(player, trial)
    
    return resp

  def trials_on_input(player, input, time):
    params = player.session.params
    num_trials = params.get('num_trials')

    trial = get_trial(player)
    if trial is None:
        raise RuntimeError("Responding witout trial")

    if trial.is_completed:
        raise RuntimeError("Trial is already completed")

    resp = on_input(player, trial, input, time)

    if trial.is_completed:
      trial.timestamp_completed = now()
      resp['status'] = dict(
          trialCompleted=True,
          trialSuccessful=trial.is_correct,
          gameOver=player.cur_iteration == num_trials,
      )

    resp['progress'] = get_progress(player, trial)
      
    return resp 

  def trials_on_timeout(player):
    params = player.session.params
    num_trials = params['num_trials']

    trial = get_trial(player)

    if trial is None:
        raise RuntimeError("Responding witout trial")

    resp = on_timeout(player, trial)

    if trial.is_completed:
      trial.timestamp_completed = now()
      resp['status'] = dict(
          trialCompleted=True,
          trialSuccessful=trial.is_correct,
          gameOver=player.cur_iteration == num_trials,
      )

    resp['progress'] = get_progress(player, trial)
      
    return resp 


  return live_method(
    on_load=trials_on_load,
    on_input=trials_on_input,
    on_timeout=trials_on_timeout,
    on_reload=on_reload
  )


def live_puzzles(*, get_trial, encode_trial, get_progress, on_load, on_move=None, on_solution=None, on_timeout, on_reload=None):
  """Creates a live_method for live trials.

  Checks various errors such as max_retries, max iterations.
  Automatically adds proper status and progress to responses, serializes trial.

  the on_load is called (player, current_trial, input, response_time, timeout)
  """

  if (on_move is None and on_solution is None) or (on_move is not None and on_solution is not None):
    raise ValueError("Either on_move or on_solution should be defined")

  def puzzle_on_load(player):
    params = player.session.params
    num_trials = params['num_trials']

    if num_trials and player.cur_iteration >= num_trials:
      raise RuntimeError("Maximum iterations exhausted")

    curtrial = get_trial(player)
    if curtrial is not None and not curtrial.is_completed:
        raise RuntimeError("Overstepping uncompleted trial")

    resp = on_load(player)
    trial = resp['trial']
    trial.timestamp_loaded = now()
    resp['trial'] = encode_trial(trial)
    resp['progress'] = get_progress(player, trial)
    
    return resp

  def puzzle_on_input(player, input, time):
    params = player.session.params
    num_trials = params.get('num_trials')

    trial = get_trial(player)

    if trial is None:
        raise RuntimeError("Responding witout trial")

    if trial.is_completed:
        raise RuntimeError("Trial is already completed")

    if 'solution' in input: 
      resp = on_solution(player, trial, input['solution'], time)
    elif 'move' in input:
      resp = on_move(player, trial, input['move'], time)
    else:
      raise ValueError("Expected either 'move' or 'solution' in input")

    if trial.is_completed:
      trial.timestamp_completed = now()
      resp['status'] = dict(
          trialCompleted=True,
          trialSuccessful=trial.is_correct,
          gameOver=player.cur_iteration == num_trials,
      )

    resp['progress'] = get_progress(player, trial)
      
    return resp 

  def puzzle_on_timeout(player):
    params = player.session.params
    num_trials = params['num_trials']

    trial = get_trial(player)

    if trial is None:
        raise RuntimeError("Responding witout trial")

    resp = on_timeout(player, trial)

    if trial.is_completed:
      trial.timestamp_completed = now()
      resp['status'] = dict(
          trialCompleted=True,
          trialSuccessful=trial.is_correct,
          gameOver=player.cur_iteration == num_trials,
      )

    resp['progress'] = get_progress(player, trial)
      
    return resp 

  return live_method(
    on_load=puzzle_on_load,
    on_input=puzzle_on_input,
    on_timeout=puzzle_on_timeout,
    on_reload=on_reload
  )