liveRecv = otree_live_utils.liveTrialsRecv;

async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule

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
    preload_media: js_vars.media_fields
  });

  game.loadTrial = function () {
    console.debug("loading...");
    otree_live_utils.loadTrial();
  };

  game.startTrial = function (trial) {
    console.debug("starting.. ", trial);
    schedule.start();
    otree.measurement.begin();
    // TODO: game.status.trialStarted = true
    game.updateStatus({ trialStarted: true });
  };

  game.onStatus = function (changed) {
    // ???
  };

  page.onInput = function (name, value) {
    console.debug("input:", name, value);
    page.freezeInputs();
    let rt = otree.measurement.end();
    otree_live_utils.sendResponse(value, rt);
  };

  page.onUpdate = function (changes) {
    console.debug("update:", changes);
    if (changes.get("phase") == "target") {
      otree.measurement.begin();
    }
  };

  page.onTimeout = function () {
    console.debug("timeout");
    otree_live_utils.sendResponseTimeout();
  };

  page.update({ stage: "instructing" });
  await page.waitForEvent("user_ready");
  page.update({ stage: "playing" });

  await game.playIterations();

  page.submit();
}
