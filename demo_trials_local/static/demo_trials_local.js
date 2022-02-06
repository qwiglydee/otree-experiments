liveRecv = otree.live_utils.liveDefaultRecv;

async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule;

  // TODO: move to game.progress
  let progress = {
    total: js_vars.num_trials,
    current: 0,
    completed: 0,
  };

  // TODO: schedule.phases =
  schedule.setup([
    { at: 0, phase: "aim" },
    { at: 1000, phase: "prime" },
    { at: 1500, phase: "target" },
  ]);
  // TODO shedule.timeout =
  schedule.setTimeout(js_vars.trial_timeout * 1000);

  // TODO: game.config = ...
  game.setConfig({
    num_trials: js_vars.num_trials,
    post_trial_pause: js_vars.post_trial_pause * 1000,
  });

  game.loadTrial = function () {
    console.debug("loading...");
    if (progress.current == js_vars.num_trials) {
      game.updateStatus({ gameOver: true });
      return;
    }

    progress.current += 1;
    game.setProgress(progress);
    game.startTrial(otree.live_utils.getPreloadedTrial(progress.current));
  };

  page.onStatus = function (changed) {
    if (changed.trialStarted) {
      console.debug("started");
      schedule.start();
    }
    if (changed.trialCompleted) {
      console.debug("completed");
      schedule.stop();

      progress.completed += 1;
      game.setProgress(progress);
    }
  };

  page.onUpdate = function (update) {
    if (update.get("phase") == "target") {
      otree.utils.measurement.begin();
    }
  };

  page.onInput = function (name, value) {
    console.debug("input:", name, value);
    page.freezeInputs();
    let rt = otree.utils.measurement.end();
    otree.live_utils.sendInput(game.trial.iteration, value, rt);

    game.setFeedback({ responseCorrect: value == game.trial.target_category });
    game.updateStatus({ trialCompleted: true });
  };

  page.onTimeout = function (time) {
    console.debug("timeout", time);
    otree.live_utils.sendTimeout(game.trial);

    game.setFeedback({ responseCorrect: null });
    game.updateStatus({ trialCompleted: true, trialSkipped: true });
  };

  await otree.live_utils.preloadTrials({ media_fields: js_vars.media_fields });

  page.update({ stage: "instructing" });
  await page.waitForEvent("user_ready");
  page.update({ stage: "playing" });

  await game.playIterations();

  page.submit();
}
