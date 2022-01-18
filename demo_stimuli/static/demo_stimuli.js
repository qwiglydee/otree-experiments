let config = js_vars.config;
let trials = [];
let results = [];

// make mseconds
config.TRIAL_PAUSE *= 1000;
config.TRIAL_TIMEOUT *= 1000; 

/** loads all images and ata and waits them to complete loading */
async function loadData() {
  trials = js_vars.trials;
  for(let i=0; i<trials.length; i++) {
    // NB: forEach doesn't work with await
    let trial = trials[i];
    trial.target = await otree.dom.loadImage('/static/images/' + trial.target);
  }
}

/** saves results data to page form */
function saveData() {
  page.form.results_data.value = JSON.stringify(results); 
}

async function main() {
  // load all images
  await loadData();

  schedule.setup({
    phases: [
      { time: 0, display: 'aim' },
      { time: 1000, display: 'prime' },
      { time: 1500, display: 'target', input: true },      
    ],
    timeout: config.TRIAL_TIMEOUT
  });

  game.setup(config);

  game.onStart = function() {
    let trial = trials[game.iteration - 1];  // NB: indexing from 0, iterating from 1
    game.updateState(trial);
    console.debug("iter:", game.iteration);
    console.debug("trial:", game.state);
    schedule.start();
  }

  game.onPhase = function(phase) {
    if (phase.input) {
      otree.measurement.begin('reaction');
    }
  }

  game.onInput = function(input) {
    schedule.stop();
    page.freezeInputs();

    let reaction = otree.measurement.end('reaction');
    let response = input.response;
    let success = response == game.state.target_category; 

    game.complete({ response, reaction, success });
  }

  game.onTimeout = function() {
    schedule.stop();
    page.freezeInputs();

    let reaction = otree.measurement.end('reaction');
    let response = null;
    let success = false;

    game.complete({ response, reaction, success, timeout: true });
  }

  game.onComplete = function(result) {
    console.debug("result:", result);

    trial = trials[game.iteration];
    results.push({ i: game.iteration, ...result });
  }

  page.form.onsubmit = function() {
    saveData();
  }

  game.reset();

  await page.waitEvent("ot.ready");

  await game.playIterations(config.NUM_TRIALS, config.TRIAL_PAUSE);

  saveData(); // FIXME
  page.submit();
}

