let PARAMS = js_vars.PARAMS;

async function main() {
  let game = otree.game,
    page = otree.page,
    schedule = otree.schedule;

  let trial_time0, trial_time, trial_timer;

  let cur_solution = [];

  schedule.setup({
    timeout: PARAMS.trial_timeout * 1000,
  });

  game.setConfig({
    num_trials: PARAMS.num_trials,
    post_trial_pause: PARAMS.post_trial_pause * 1000,
    trial_timeout: PARAMS.trial_timeout * 1000, // for timer bar
  });

  game.loadTrial = function () {
    console.debug("loading");
    liveSend({ type: "load" });
  };

  game.startTrial = function (trial) {
    console.debug("starting:", trial);

    cur_solution = [];

    game.updateTrial({ freecell: puzzle_utils.findFreeCell(trial.board) });

    schedule.start();
    otree.measurement.begin();
    page.togglePhase({ inputEnabled: true });
    game.updateStatus({ trialStarted: true });
    page.emitUpdate({ "progress.moves": 0 });
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
    console.debug("input:", name, value);

    if (name == 'submit') {
      schedule.stop();
      page.freezeInputs();
  
      let rt = otree.measurement.end();
  
      liveSend({ type: "input", input: { solution: cur_solution }, response_time: rt });  
      return;
    }

    if (PARAMS.limit_moves && cur_solution.length == game.trial.difficulty) {
      game.setFeedback({ final: true, error: { code: 'movesExhausted'}});
      return;
    } 

    let src = Number(value);

    let moveValid = puzzle_utils.validateMove(
      game.trial.board,
      PARAMS.board_size,
      game.trial.freecell,
      src
    );

    if (!moveValid) {
      game.setFeedback({ error: { code: 'moveInvalid'}});
      return;
    }

    cur_solution.push(src);

    page.emitUpdate({ "progress.moves": cur_solution.length });

    let newboard = puzzle_utils.moveCell(game.trial.board, game.trial.freecell, src);
    game.updateTrial({ board: newboard, freecell: src });

    let puzzleCompleted = puzzle_utils.validateBoard(newboard).every((v) => v);
    game.setFeedback({ 
      final: puzzleCompleted || (PARAMS.limit_moves && cur_solution.length == game.trial.difficulty),
      correct: puzzleCompleted
    });
  };

  page.onTimeout = function () {
    console.debug("timeout");
    page.freezeInputs();
    liveSend({ type: "timeout" });
  };

  page.onUpdate = function (changes) {
    // calculate classes for cells when they're updated
    if (changes.affects("trial.board")) {
      let classes = puzzle_utils
        .validateBoard(game.trial.board)
        .map((valid) => (valid ? "valid" : "invalid"));
      classes[game.trial.freecell] = "";
      page.emitUpdate({ cellClasses: classes });
    }
  };

  await page.waitForEvent("ot.ready");

  await game.playIterations();

  document.querySelector("#form").submit();
}
