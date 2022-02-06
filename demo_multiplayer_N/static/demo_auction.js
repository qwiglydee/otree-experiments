liveRecv = otree.live_utils.liveGenericRecv;

function main() {
  let page = otree.page, game=otree.game;

  page.onStatus = function(changed) {
    console.debug("status", changed);
  };

  page.onUpdate = function(update) {
    console.debug("udpate", update);
  };

  page.onInput = function(name, value) {
    console.debug("input", name, value);
    let bid = parseInt(value);
    otree.live_utils.sendInput(game.trial, bid)
  };

  page.onEvent('btn.bid', function() {
    page.submitInputs('bid');
  });

  game.playTrial();
}
