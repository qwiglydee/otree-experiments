liveRecv = otree.live_utils.liveTrialsRecv;

async function main() {
  let page = otree.page,
    game = otree.game,
    schedule = otree.schedule;

  // styles to display everything
  let styles = {
    target: [],
    matrix: [],
    feedback: [],
  };

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
    otree.live_utils.loadTrial();
  };

  game.startTrial = function (trial) {
    console.debug("starting...", trial);
    schedule.start();
    game.progress.moves = 0;  // augmenting progress
    // TODO: move inside game core
    game.updateStatus({ trialStarted: true });
  };

  game.onStatus = function(changed) {
    if (changed.trialCompleted) {
      schedule.stop();
      page.update({ phase: 'feedback' });
    }
  }

  page.onInput = function (name, value) {
    console.debug("input:", name, value);

    let pos = value;

    // modifying directly
    game.trial.matrix[pos] = js_vars.char_fill;
  
    if (game.progress.moves == js_vars.max_moves) {
      otree.live_utils.sendResponseSolution(game.trial.iteration, game.trial.matrix);
    }

    game.progress.moves++;
    page.update({ "trial.matrix": game.trial.matrix }); // manually refresh updated matrix
  };

  page.onUpdate = function (change) { // FIXME??? this is page update, not game state update
    if (change.affects("trial.*")) {
      // recalculate styles for all matrices when they are updated
      console.debug("updating styles");
      styles.matrix = game.trial.matrix.map((cell) => (cell == js_vars.char_fill ? "filled" : "empty"));
      if (game.trial.validated) {
        game.trial.validated.forEach((val, i) => {
          if (val !== null) {
            styles.matrix[i] = val ? "correct" : "incorrect";
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