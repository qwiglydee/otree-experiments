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

function sendResponse(input, response_time) {
  liveSend({ type: 'response', input, response_time });
}

function sendResponseTimeout() {
  liveSend({ type: 'response', timeout_happened: true });
}

window.otree_live_utils = {
  livePageRecv,
  liveTrialsRecv,
  loadTrial,
  sendResponse,
  sendResponseTimeout,
}
