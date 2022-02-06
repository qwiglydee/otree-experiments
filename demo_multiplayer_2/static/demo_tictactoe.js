liveRecv = otree.live_utils.liveGenericRecv;

async function main() {
  let page = otree.page,
    game = otree.game;

  game.setConfig({ 
    post_trial_pause: js_vars.post_trial_pause * 1000
  });

  game.loadTrial = function() {
    otree.live_utils.requestTrial();
  }

  page.onStatus = function (changed) {
    if (changed.playerActive === true) {
      page.update({ phase: "playing" });
    }
    if (changed.playerActive === false) {
      page.update({ phase: "waiting" });
    }
    if (changed.gameOver) {
      page.update({ phase: "feedback" });
    }
  };

  page.onUpdate = function (update) {
    if (update.has("trial.winpattern")) {
      // styles to highligh winning pattern
      let hl_class = game.status.trialSuccessful ? "winning" : "losing";
      page.update({
        highlight: game.trial.winpattern.map((cell) => (cell == "+" ? hl_class : "")),
      });
    }
  };

  page.onInput = function (name, value) {
    console.debug("input:", name, value);
    otree.live_utils.sendAction(game.trial, value);
  };

  await game.playTrial();

  page.submit();
}
