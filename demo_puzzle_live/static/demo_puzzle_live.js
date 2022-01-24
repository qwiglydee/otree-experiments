let PARAMS = js_vars.PARAMS;

async function main() {
  let game = otree.game,
    page = otree.page,
    schedule = otree.schedule;

  let trial_time0, trial_time, trial_timer;

  schedule.setup({
    timeout: PARAMS.trial_timeout * 1000,
  });

  game.setConfig({
    num_trials: PARAMS.num_trials,
    post_trial_pause: PARAMS.post_trial_pause * 1000,
    trial_timeout: PARAMS.trial_timeout * 1000 // for timer bar 
  });

  game.loadTrial = function () {
    console.debug("loading");
    liveSend({ type: "load" });
  };

  game.startTrial = function (trial) {
    console.debug("starting:", trial);

    game.updateTrial({ freecell: puzzle_utils.findFreeCell(trial.board) });

    schedule.start();
    otree.measurement.begin();
    page.togglePhase({ inputEnabled: true });
    game.updateStatus({ trialStarted: true });
  };

  game.onStatus = function (status, changed) {
    console.debug("status", status);

    if (changed.trialStarted) {
      trial_time0 = Date.now();
      trial_timer = setInterval(function () {
        trial_time = Date.now();
        page.emitUpdate({ trial_timer: trial_time - trial_time0 });
      }, 100);
    }

    if (changed.trialCompleted) {
      clearInterval(trial_timer);
      trial_timer = null;
    }
  };

  page.onInput = function (name, value) {
    console.debug("input:", value);

    let src = Number(value);

    liveSend({ type: 'input', input: {move: src} });
  };

  page.onTimeout = function () {
    console.debug("timeout");
    page.freezeInputs();
    liveSend({ type: "timeout" });
  };

  page.onUpdate = function (changes) {
    // calculate classes for cells when they're updated
    if (changes.affects("trial.board")) {
      let emptycell = puzzle_utils.findFreeCell(game.trial.board)
      let classes = puzzle_utils
        .validateBoard(game.trial.board)
        .map((valid) => (valid ? "valid" : "invalid"));
      classes[emptycell] = "";
      page.emitUpdate({ cellClasses: classes });
    }
  };
  
  await page.waitForEvent("ot.ready");

  await game.playIterations();

  document.querySelector("#form").submit();
}
