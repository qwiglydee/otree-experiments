let PARAMS = js_vars.params;

async function main() {
  let game = otree.game, page = otree.page, schedule = otree.schedule;
  let $input = document.getElementById("answer-inp");
  let trial_time0, trial_time, trial_timer;

  schedule.setup({
    timeout: PARAMS.trial_timeout * 1000,
  });

  game.setConfig({
    num_iterations: PARAMS.num_iterations,
    trial_timeout: PARAMS.trial_timeout * 1000,
    post_trial_pause: PARAMS.post_trial_pause * 1000,
    preload_media: PARAMS.media_fields
  });

  game.loadTrial = function () {
    console.debug("loading");
    liveSend({ type: "load" });
  };

  game.startTrial = function (trial) {
    console.debug("starting:", trial);
    schedule.start();
    otree.measurement.begin();
    page.togglePhase({ inputEnabled: true });
    game.updateStatus({ trialStarted: true });
  };

  game.onFeedback = function (feedback) {
    console.debug("feedback", feedback);
    if (feedback.input) { // FIXME: use page.emitUpdate({ input_name })
      // replace with normalized value
      $input.value = feedback.input;
    }

    // convert to bootstrap css classes
    if (feedback.correct === true) page.emitUpdate({ "feedback.class": "is-valid" });
    if (feedback.correct === false) page.emitUpdate({ "feedback.class": "is-invalid" });

    // continue inputs
    if (!feedback.final) page.unfreezeInputs();
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

  page.onPhase = function (phase) {
    if (phase.inputEnabled) {  // FIXME: somehow
      $input.focus();
    }
  };

  page.onInput = function (name, value) {
    console.debug("input:", name, value);
    page.freezeInputs();

    // the buttons
    if (name == 'submit') {
      if (value == 'skip') {
        $input.value="";  // FIXME: use page.emitReset([input_name])
        game.clearFeedback();
        page.emitInput('answer', null);
      }

      if (value == 'submit') {
        page.emitInput('answer', $input.value);
      }

      return;
    }

    let response_time = otree.measurement.end();
    liveSend({ type: "input", input: value, response_time });
  };

  page.onTimeout = function () {
    console.debug("timeout");
    page.freezeInputs();
    liveSend({ type: "timeout" });
  };

  await page.waitForEvent("ot.ready");

  await game.playIterations();

  document.querySelector("#form").submit();
}
