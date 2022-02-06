liveRecv = otree.live_utils.liveTrialsRecv;

async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule

  // TODO: schedule.phases = 
  schedule.setup([
    { at: 0, phase: "aim" },
    { at: 1000, phase: "prime" },
    { at: 1500, phase: "target" },
  ]);
  // TODO: schedule.timeout = 
  schedule.setTimeout(js_vars.trial_timeout * 1000);

  // TODO: game.config = ...
  game.setConfig({
    num_trials: js_vars.num_trials,
    post_trial_pause: js_vars.post_trial_pause * 1000,
    media_fields: js_vars.media_fields
  });

  game.loadTrial = function () {
    console.debug("loading...");
    otree.live_utils.loadTrial();
  };

  game.startTrial = function (trial) { // == onStart
    console.debug("starting.. ", trial);
    schedule.start();
    otree.utils.measurement.begin();
    // TODO: hardcode into core game, not much used anyway
    game.updateStatus({ trialStarted: true });
  };

  game.onStatus = function(changed) {
    if( changed.trialCompleted ) { // == onStop
      console.debug("stopped", trial);
      schedule.stop();
    }
  }

  page.onInput = function (name, value) {
    console.debug("input:", name, value);
    page.freezeInputs();
    let rt = otree.utils.measurement.end();
    otree.live_utils.sendResponse(game.trial.iteration, value, rt);
  };

  page.onUpdate = function (changes) {
    console.debug("update:", changes);
    if (changes.get("phase") == "target") {
      otree.utils.measurement.begin();
    }
  };

  page.onTimeout = function () {
    console.debug("timeout");
    otree.live_utils.sendTimeout(game.trial.iteration);
  };

  page.update({ stage: "instructing" });
  await page.waitForEvent("user_ready");
  page.update({ stage: "playing" });

  await game.playIterations();

  page.submit();
}
