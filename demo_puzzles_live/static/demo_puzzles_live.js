liveRecv = otree.live_utils.liveTrialsRecv;

async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule;

  // styles to display workign matrix or feedback
  let styles = [];

  schedule.setup([
    { at: 0, phase: "exposing" },
    { at: js_vars.exposure_time * 1000, phase: "solving" },
  ]);
  schedule.setTimeout(js_vars.trial_timeout * 1000);

  // TODO: game.config = ...
  game.setConfig({
    num_trials: js_vars.num_trials,
    post_trial_pause: js_vars.post_trial_pause * 1000,
  });

  game.loadTrial = function () {
    console.debug("loading...");
    otree.live_utils.loadTrial();
  };

  game.startTrial = function (trial) {
    console.debug("starting...", trial);
    schedule.start();
    // TODO: move inside game core
    game.updateStatus({ trialStarted: true });
  };

  game.onStatus = function(changed) {
    if (changed.trialCompleted) {
      page.update({ phase: 'feedback' });
    }
  }

  page.onInput = function (name, value) {
    console.debug("input:", name, value);

    let pos = value;
    game.trial.matrix[pos] = js_vars.char_fill;
    page.update({ "trial.matrix": game.trial.matrix }); // manually refresh updated matrix

    otree.live_utils.sendResponseAction(game.trial.iteration, pos);
  };

  page.onTimeout = function () {
    console.debug("timeout");
    otree.live_utils.sendTimeout(game.trial.iteration);
  };

  page.onUpdate = function (change) { // FIXME??? this is page update, not game state update
    if (change.affects("trial.*")) {
      // recalculate styles for all matrices when they are updated
      console.debug("updating styles");
      styles = game.trial.matrix.map((cell) => (cell == js_vars.char_fill ? "filled" : "empty"));
      if (game.trial.validated) {
        game.trial.validated.forEach((val, i) => {
          if (val !== null) {
            styles[i] = val ? "correct" : "incorrect";
          }
        });
      }
      page.update({ styles: styles });
    }
  };

  page.update({ stage: "instructing" });
  await page.waitForEvent("user_ready");
  page.update({ stage: "playing" });

  await game.playIterations();

  page.submit();
}
