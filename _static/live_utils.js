function livePageRecv(data) {
  let messages = Array.isArray(data) ? data : [data];
  for(let message of messages) {
    // console.debug(`ot.live.${message.type}`, message);
    otree.page.emitEvent(`ot.live.${message.type}`, message)
  }
}

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

async function preloadTrials(media_fields) {
  if (window.liveRecv === undefined) {
    throw new Error("Preloading requires liveRecv to be defined like `otree.live_utils.livePageRecv` or similarly")
  }

  liveSend({ type: 'load' });
  let event = await otree.page.waitForEvent('ot.live.trials');
  trials_data = event.detail.data;
  if (media_fields) {
    for(let trial of trials_data) {
      otree.utils.trials.preloadMedia(trial, media_fields);
    }
  }
  current_iter = 0;
}

function sendResponse(i, input, response_time) {
  liveSend({ type: 'response', iteration: i, input, response_time });
}

function sendResponseTimeout(i) {
  liveSend({ type: 'response', iteration: i, timeout_happened: true });
}


if (window.otree === undefined) {
  window.otree = {};
}

window.otree.live_utils = {
  livePageRecv,
  liveTrialsRecv,
  loadTrial,
  sendResponse,
  sendResponseTimeout,
  preloadTrials,
  getPreloadedTrial
}
