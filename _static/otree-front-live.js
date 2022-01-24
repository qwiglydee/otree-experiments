
/** pretty much generic liveRecv */
function liveRecv(data) {
  if (!Array.isArray(data)) {
    messages = [data];
  } else {
    messages = data;
  }

  messages.forEach(async (message) => {
    let type = message.type;
    let payload = Object.assign({}, message);
    delete payload.type;
    console.debug(`live ${type}:`, payload);
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
  });
}
