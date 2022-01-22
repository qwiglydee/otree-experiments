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
      { time: 0, display: 'aim' },
      { time: 1000, display: 'prime' },
      { time: 1500, display: 'target', input: true },      
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
    if (phase.input) {
      otree.measurement.begin();
    }
  }

  game.onInput = function(inp) {
    page.freezeInputs();
    progress.retries ++;

    let input = inp.response;
    let rt = otree.measurement.begin();

    validateInput(input);

    if (config.max_retries && progress.retries < config.max_retries && !game.feedback.correct) {
      // continue
      page.unfreezeInputs();
      return;
    } else {
      schedule.stop();
      completeTrial(input, rt, progress.retries);
    }
  }

  game.onTimeout = function() {
    page.freezeInputs();

    let input = null;
    if (config.nogo_response) {
      input = config.nogo_response;
    }

    validateInput(input);

    schedule.stop();
    completeTrial(input, null, progress.retries);
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

  await page.waitEvent("ot.ready");

  await game.playIterations();

  document.querySelector("#form").submit();
}

