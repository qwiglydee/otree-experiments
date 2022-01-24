let PARAMS = js_vars.params;
let trials = js_vars.trials;
let results = [];
 
/** saves results data to page form */
function saveData() {
  formInputs.results_data.value = JSON.stringify(results); 
}


async function main() {
  let game = otree.game, page = otree.page, schedule = otree.schedule;

  saveData(); // save empty  

  let progress = {
    total: PARAMS.num_trials,
    current: 0,
    retries: 0,
    completed: 0 
  }

  schedule.setup({
    phases: [
      { at: 0, display: 'aim' },
      { at: 1000, display: 'prime' },
      { at: 1500, display: 'target', inputEnabled: true },      
    ],
    timeout: PARAMS.trial_timeout * 1000
  });

  game.setConfig({
      num_trials: PARAMS.num_trials,
      trial_timeout: PARAMS.trial_timeout * 1000,
      post_trial_pause: PARAMS.post_trial_pause * 1000,
      preload_media: PARAMS.media_fields
  });

  game.loadTrial = function() {
    progress.current ++;
    progress.retries =0;
    game.setProgress(progress);

    let trial = trials[progress.current - 1];
    console.debug("trial", trial);
    game.setTrial(trial);
  }

  game.startTrial = function(trial) {
    schedule.start();
    game.updateStatus({ trialStarted: true });
  }

  game.onStatus = function(status, changed) {
    console.debug("iter", progress.current, "status:", status);
    if (changed.trialCompleted) {
      progress.completed ++;
      game.setProgress(progress);

      if (progress.current == progress.total) {
        game.updateStatus({ gameOver: true });
      }
    }
  }

  page.onPhase = function(phase) {
    if (phase.inputEnabled) {
      otree.measurement.begin();
    }
  }

  page.onInput = function(name, value) {
    page.freezeInputs();

    progress.retries ++;
    game.setProgress(progress);

    let rt = otree.measurement.end();

    let correct;
    if (value !== null) {
      correct = value == game.trial.target_category; 
    } // else leave undefined

    game.setFeedback({ input: value, correct: correct });

    if (PARAMS.max_retries && progress.retries < PARAMS.max_retries && !game.feedback.correct) {
      // continue
      page.unfreezeInputs();
      return;
    }

    schedule.stop();

    results.push({ i: progress.current, input: value, rt: rt, retr: progress.retries }); 
    saveData();

    game.updateStatus({ 
      trialCompleted: true, 
      trialSuccessful: correct,
    });
  }

  page.onTimeout = function() {
    if (PARAMS.nogo_response) {
      page.emitInput("response", PARAMS.nogo_response);  
    }
    
    page.freezeInputs();
    schedule.stop();

    results.push({ i: progress.current, to: true }); 
    saveData();
    
    game.updateStatus({ 
      trialCompleted: true, 
      trialSuccessful: false,
    });
  }

  await page.waitForEvent("ot.ready");

  await game.playIterations();

  document.querySelector("#form").submit();
}

