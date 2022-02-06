liveRecv = otree.live_utils.liveGenericRecv;

async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule;

  // styles to display working or validated matrix
  let styles = [];

  schedule.setup([
    { at: 0, phase: "exposing" },
    { at: js_vars.exposure_time * 1000, phase: "solving" },
  ]);

  // TODO: game.config = ...
  game.setConfig({
    num_trials: js_vars.num_trials,
    post_trial_pause: js_vars.post_trial_pause * 1000,
  });

  game.loadTrial = function () {
    console.debug("loading...");
    otree.live_utils.requestTrial();
  };

  page.onStatus = function (changed) {
    console.debug("status", changed);
    if (changed.trialStarted) {
      schedule.start();
    }
    if (changed.trialCompleted) {
      schedule.stop();
    }
  };

  page.onUpdate = function (update) {
    if (update.affects("trial.*")) {
      // recalculate styles when anything changes
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

  page.onInput = function (name, value) {
    console.debug("input:", name, value);

    let pos = value;
    game.trial.matrix[pos] = js_vars.char_fill;
    page.update({ "trial.matrix": game.trial.matrix }); // manually refresh updated matrix

    otree.live_utils.sendAction(game.trial, pos);
  };

  page.update({ stage: "instructing" });
  await page.waitForEvent("user_ready");
  page.update({ stage: "playing" });

  await game.playIterations();

  page.submit();
}
