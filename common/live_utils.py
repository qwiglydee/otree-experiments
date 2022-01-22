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


def live_method(*, on_load, on_input, on_reload=None):

  def method(player, message):
    if not isinstance(message, dict) or 'type' not in message:
        raise ValueError("Invalid message")

    if message['type'] not in ('load', 'reload', 'input'):
        raise ValueError("Invalid message type")

    msg_type = message.get('type')

    if msg_type == 'load':
      data = on_load(player)
      return make_response(player, data)

    if msg_type == 'input':
      data = on_input(player, message.get('input'), message.get('response_time'), message.get('timeout'))
      return make_response(player, data)

    if msg_type == 'reload':
      data = on_reload(player)
      return make_response(player, data)

    raise NotImplementedError(f"No handler for {msg_type}")

  return staticmethod(method)


def live_trials(*, get_trial, encode_trial, get_progress, on_load, on_input, on_reload=None):
  """Creates a live_method for live trials.

  Checks various errors such as max_retries, max iterations.
  Automatically adds proper status and progress to responses, serializes trial.

  the on_load is called (player, current_trial, input, response_time, timeout)
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

  def trials_on_input(player, input, time, timeout):
    params = player.session.params
    max_retries = params['max_retries']
    num_trials = params['num_trials']

    trial = get_trial(player)
    if trial is None:
        raise RuntimeError("Responding witout trial")

    if trial.response is not None and not max_retries:
        raise RuntimeError("retrying not allowed")

    if trial.response is not None and trial.retries >= max_retries:
        raise RuntimeError("max attempts exhausted")

    resp = on_input(player, trial, input, time, timeout)

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
    on_reload=on_reload
  )