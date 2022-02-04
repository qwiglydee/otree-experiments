liveRecv = otree.live_utils.livePageRecv;


async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule

  let progress = {
    total: js_vars.num_trials,
    current: 0,
    completed: 0 
  };

  schedule.setup([
    { at: 0, phase: "aim" },
    { at: 1000, phase: "prime" },
    { at: 1500, phase: "target" },
  ]);
  schedule.setTimeout(js_vars.trial_timeout * 1000);

  // TODO: game.config = ...
  game.setConfig({
    num_trials: js_vars.num_trials,
    post_trial_pause: js_vars.post_trial_pause * 1000,
  });

  game.loadTrial = function () {
    console.debug("loading...");
    progress.current += 1;
    game.setTrial(otree.live_utils.getPreloadedTrial(progress.current));
    game.setProgress(progress);
  };

  game.startTrial = function (trial) {
    console.debug("starting.. ", trial);

    schedule.start();
    otree.utils.measurement.begin();
    // TODO: game.status.trialStarted = true
    game.updateStatus({ trialStarted: true });
  };

  // eventually called from utils.loadTrial
  game.onStatus = function (changed) {
    if (changed.trialCompleted) {
      progress.completed += 1
      game.setProgress(progress);

      if (progress.current == js_vars.num_trials) {
        game.updateStatus({ gameOver: true });
      }
    }
  };

  page.onInput = function (name, value) {
    console.debug("input:", name, value);
    page.freezeInputs();
    let rt = otree.utils.measurement.end();
    otree.live_utils.sendResponse(game.trial.iteration, value, rt);

    game.setFeedback({
      responseCorrect: value == game.trial.target_category,
      responseFinal: true
    });
    game.updateStatus({ trialCompleted: true });
  };

  page.onUpdate = function (changes) {
    console.debug("update:", changes);
    if (changes.get("phase") == "target") {
      otree.utils.measurement.begin();
    }
  };

  page.onTimeout = function () {
    console.debug("timeout");
    otree.live_utils.sendResponseTimeout(game.trial.iteration);
    game.setFeedback({
      responseCorrect: false,
      responseFinal: true
    });
    game.updateStatus({ trialCompleted: true, trialSkipped: true });
  };

  await otree.live_utils.preloadTrials(js_vars.media_fields);

  page.update({ stage: "instructing" });
  await page.waitForEvent("user_ready");
  page.update({ stage: "playing" });
 
  await game.playIterations();

  page.submit();
}
