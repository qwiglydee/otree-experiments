/** default liveRecv is to emit corresponding 'ot.live.*' events */
function liveDefaultRecv(data) {
  let messages = Array.isArray(data) ? data : [data];
  for(let message of messages) {
    otree.page.emitEvent(`ot.live.${message.type}`, message)
  }
}

/* for live_trials, call appropriate game methods */
function liveTrialsRecv(data) {
  let messages = Array.isArray(data) ? data : [data];
  for(let message of messages) {
    let type = message.type;
    let payload = Object.assign({}, message);
    delete payload.type;
    switch (type) {
      case "trial":
        otree.game.setTrial(payload);
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

function loadTrial() {
  liveSend({ type: 'load' });
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
  current_iter = 0;
}

function sendResponse(i, value, response_time) {
  liveSend({ type: 'response', iteration: i, input: value, response_time });
}

function sendResponseAction(i, value, response_time) {
  liveSend({ type: 'response', iteration: i, action: value, response_time });
}

function sendResponseSolution(i, value, response_time) {
  liveSend({ type: 'response', iteration: i, solution: value, response_time });
}

function sendTimeout(i) {
  liveSend({ type: 'timeout', iteration: i });
}


if (window.otree === undefined) {
  window.otree = {};
}

window.otree.live_utils = {
  liveDefaultRecv,
  liveTrialsRecv,
  loadTrial,
  sendResponse,
  sendResponseAction,
  sendResponseSolution,
  sendTimeout,
  preloadTrials,
  getPreloadedTrial
}
