let config = js_vars.config;

async function main() {
  let $input = document.querySelector('[data-ot-input="answer"]');
  let $skipbtn = document.querySelector("#skip-btn");

  schedule.setup({
    timeout: config.trial_timeout
  });

  game.setup(config);

  game.onStart = function() {
    console.debug("start");
    // FIXME: should be on ot.reset
    // $input.value = "";  

    liveSend({ type: 'load' });
  }

  game.onLiveTrial = async function(trial) {
    console.debug("trial:", trial);
    trial.image = await otree.dom.loadImage(trial.image);
    game.updateState(trial);
    schedule.start();
    page.togglePhase({ input: true });
    otree.measurement.begin();
  }

  game.onInput = function(input) {
    console.debug("input:", input);
 
    page.freezeInputs();
    let reaction_time = otree.measurement.end();

    liveSend({ type: 'input', input: input.answer, reaction_time });
  }

  game.onTimeout = function() {
    console.debug("timeout");
    page.freezeInputs();

    liveSend({ type: 'input', timeout: true });
  }

  game.onLiveFeedback = function(feedback) {
    console.debug("feedback", feedback);
    $input.value = feedback.input; // replace with normalized value

    page.emitUpdate({ feedback }); // display feedback 

    if (!feedback.final) page.unfreezeInputs();
  }
  
  game.onLiveStatus = function(status) {
    console.debug("status", status);
    status.trial_skipped = status.trial_completed && status.trial_succesful === null;
    game.setStatus(status);
    if (status.trial_completed) {
      game.complete();
    }
  }

  game.onLiveProgress = function(progress) {
    page.emitUpdate({ progress });
  }

  $skipbtn.onclick = function() {
    liveSend({ type: 'input', input: null });    
  }

  console.debug("loaded");

  page.emitReset(["game", "status", "error", "result", "feedback"]); // FIXME: should be on page/game initialization somehow

  await page.waitEvent("ot.ready");
  console.debug("ready");

  while(!game.status.game_over) {
    console.debug("playing");
    await game.play();
    await otree.timers.sleep(config.trial_pause);
  }

  page.submit();
}
