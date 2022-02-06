/** default liveRecv is to emit corresponding 'ot.live.*' events */
function liveDefaultRecv(data) {
  let messages = Array.isArray(data) ? data : [data];
  for(let message of messages) {
    let type = message.type;
    delete message.type;
    otree.page.emitEvent(`ot.live.${type}`, message)
  }
}

/** generic liveRecv calls appropriate game methods */
function liveGenericRecv(data) {
  let messages = Array.isArray(data) ? data : [data];
  for(let message of messages) {
    let type = message.type;
    let payload = Object.assign({}, message);
    delete payload.type;
    switch (type) {
      case "trial":
        otree.game.startTrial(payload);
        break;
      case "status":
        otree.game.updateStatus(payload);
        break;
      case "update":
        otree.game.updateTrial(payload);
        break;
      case "feedback":
        otree.game.setFeedback(payload);
        break;
      case "progress":
        otree.game.setProgress(payload);
    }
  }
}

let trials_data; // iteration from 1, indexing from 0

function getPreloadedTrial(iteration) {
  return trials_data[iteration-1];
}

async function preloadTrials(conf) {
  if (window.liveRecv === undefined) {
    throw new Error("Preloading requires liveRecv to be defined like `otree.live_utils.liveDefaultRecv` or similarly")
  }

  liveSend({ type: 'load' });
  let event = await otree.page.waitForEvent('ot.live.trials');
  trials_data = event.detail.data;
  if (conf.media_fields) {
    for(let trial of trials_data) {
      otree.utils.trials.preloadMedia(trial, conf.media_fields);
    }
  }
}

function requestTrial() {
  liveSend({ type: 'load' });
}

function sendInput(trial, input, response_time) {
  liveSend({ type: 'response', iteration: trial.iteration, input, response_time });
}

function sendAction(trial, action, response_time) {
  liveSend({ type: 'response', iteration: trial.iteration, action, response_time });
}

function sendSolution(trial, solution, response_time) {
  liveSend({ type: 'response', iteration: trial.iteration, solution, response_time });
}

function sendTimeout(trial) {
  liveSend({ type: 'timeout', iteration: trial.iteration });
}

if (window.otree === undefined) {
  window.otree = {};
}

window.otree.live_utils = {
  liveDefaultRecv,
  liveGenericRecv,
  requestTrial,
  preloadTrials,
  getPreloadedTrial,
  sendInput,
  sendAction,
  sendSolution,
  sendTimeout,
}
