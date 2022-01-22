let config = js_vars.config;

function liveRecv(data) {
  console.debug("liveRecv", data);

  if (!Array.isArray(data)) {
    data = [data];
  }

  data.forEach(async (datum) => {
    let type = datum.type;
    delete datum.type;
    switch (type) {
      case "trial":
        datum.image = await otree.dom.loadImage(datum.image);
        otree.game.setTrial(datum);
        break;
      case "status":
        otree.game.updateStatus(datum);
        break;
      case "update":
        otree.game.updateTrial(datum.changes);
        break;
      case "feedback":
        otree.game.setFeedback(datum);
        break;
      case "progress":
        otree.game.setProgress(datum);
    }
  });
}

async function main() {
  let game = otree.game, page = otree.page, schedule = otree.schedule;
  let $input = document.querySelector('[ot-input]');
  let $skip_btn = document.querySelector("#skip-btn"), $submit_btn=document.querySelector("#submit-btn")
  let trial_time0, trial_time, trial_timer;


  schedule.setup({
    timeout: config.trial_timeout,
  });

  game.setConfig(config);

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

  game.onPhase = function (phase) {
    // postponed
    if (phase.inputEnabled) {
      $input.focus();
    }
  };

  game.onInput = function (name, value) {
    console.debug("input:", value);
    page.freezeInputs();
    let response_time = otree.measurement.end();
    liveSend({ type: "input", input: value, response_time });
  };

  game.onTimeout = function () {
    console.debug("timeout");
    page.freezeInputs();
    liveSend({ type: "input", timeout: true });
  };

  game.onFeedback = function (feedback) {
    console.debug("feedback", feedback);
    if (feedback.input) {
      // replace with normalized value
      $input.value = feedback.input;
    }

    // convert to bootstrap css classes
    if (feedback.correct === true) page.emitUpdate({ "feedback.class": "is-valid" });
    if (feedback.correct === false) page.emitUpdate({ "feedback.class": "is-invalid" });

    // continue inputs
    if (!feedback.final) page.unfreezeInputs();
  };

  game.onStatus = function (status) {
    console.debug("status", status);
    if (status.trialStarted && !trial_timer) {
      trial_time0 = Date.now();
      trial_timer = setInterval(function () {
        trial_time = Date.now();
        page.emitUpdate({ trial_timer: trial_time - trial_time0 });
      }, 100);
    }

    if (status.trialCompleted && trial_timer) {
      clearInterval(trial_timer);
      trial_timer = null;
    }
  };

  $skip_btn.onclick = function () {
    $input.value="";
    game.clearFeedback();
    page.emitInput({ answer: null });
  };

  $submit_btn.onclick = function() {
    page.emitInput({ answer: $input.value });
  }

  await page.waitForEvent("ot.ready");

  await game.playIterations();

  document.querySelector("#form").submit();
}
