function livePageRecv(data) {
  let messages = Array.isArray(data) ? data : [data];
  for(let message of messages) {
    // console.debug(`ot.live.${message.type}`, message);
    otree.page.emitEvent(`ot.live.${message.type}`, message)
  }
}

window.otree_live_utils = {
  livePageRecv
}