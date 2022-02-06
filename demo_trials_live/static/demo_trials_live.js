liveRecv = otree.live_utils.liveGenericRecv;

async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule;

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
    media_fields: js_vars.media_fields,
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
    if (update.get("phase") == "target") {
      otree.utils.measurement.begin();
    }
  };

  page.onInput = function (name, value) {
    console.debug("input:", name, value);
    page.freezeInputs();
    let rt = otree.utils.measurement.end();
    otree.live_utils.sendInput(game.trial, value, rt);
  };

  page.onTimeout = function (time) {
    console.debug("timeout", time);
    otree.live_utils.sendTimeout(game.trial);
  };

  page.update({ stage: "instructing" });
  await page.waitForEvent("user_ready");
  page.update({ stage: "playing" });

  await game.playIterations();

  page.submit();
}
