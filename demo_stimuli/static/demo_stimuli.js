let config = js_vars.config;
let trials = [];
let results = [];
 

/** loads all images and ata and waits them to complete loading */
async function loadData() {
  trials = js_vars.trials;
  for(let i=0; i<trials.length; i++) { // NB: forEach doesn't work with await
    let trial = trials[i];
    trial.target = await otree.dom.loadImage('/static/images/' + trial.target);
  }
}

/** saves results data to page form */
function saveData() {
  formInputs.results_data.value = JSON.stringify(results); 
}


async function main() {
  let game = otree.game, page = otree.page, schedule = otree.schedule;

  // load all images
  await loadData();
  saveData(); // save empty  

  let progress = {
    total: config.num_trials,
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
    timeout: config.trial_timeout
  });

  game.setConfig(config);
  

  game.loadTrial = function() {
    progress.current ++;
    progress.retries =0;
    game.setProgress(progress);

    let trial = trials[progress.current - 1];
    game.setTrial(trial);
  }

  game.startTrial = function(trial) {
    schedule.start();
    game.updateStatus({ trialStarted: true });
  }

  game.onPhase = function(phase) {
    if (phase.inputEnabled) {
      otree.measurement.begin();
    }
  }

  game.onInput = function(name, value) {
    page.freezeInputs();
    progress.retries ++;

    let rt = otree.measurement.begin();

    validateInput(value);

    if (config.max_retries && progress.retries < config.max_retries && !game.feedback.correct) {
      // continue
      page.unfreezeInputs();
      return;
    } else {
      schedule.stop();
      completeTrial(value, rt, progress.retries);
    }
  }

  game.onTimeout = function() {
    page.freezeInputs();

    let value = null;
    if (config.nogo_response) {
      value = config.nogo_response;
    }

    validateInput(value);

    schedule.stop();
    completeTrial(value, null, progress.retries);
  }

  function validateInput(input) {
    let correct;
    if (input !== null) {
      correct = input == game.trial.target_category; 
    } // else undefined

    game.setFeedback({ input, correct });
  }

  function completeTrial(input, rt, retr) {
    // rt=null means timeout
    results.push({ i: progress.current, input, rt, retr }); 
    saveData();

    progress.completed ++;
    game.setProgress(progress);

    game.updateStatus({ 
      trialCompleted: true, 
      trialSuccessful: game.feedback.correct,
      gameOver: progress.current == progress.total 
    });
  }

  await page.waitForEvent("ot.ready");

  await game.playIterations();

  document.querySelector("#form").submit();
}

