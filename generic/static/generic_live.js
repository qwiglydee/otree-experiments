/** the Model
 * holds all current state data
 */
class Model {
    constructor() {
        this.reset();
    }

    reset() {
        this.stimulus = null;
        this.response = null;
        this.feedback = null;
    }

    setTrial(data) {
        this.stimulus = {type: data.datatype}
        switch(data.datatype) {
            case 'text':
              this.stimulus.value = data.stimulus;
              break;
            case 'image-url':
              this.stimulus.url = data.image_url;
              break;
            case 'image-data':
              this.stimulus.data = data.image_data;
              break;
        }
    }

    setResponse(value) {
        this.response = value;
        this.feedback = null;
    }

    setFeedback(data) {
        this.feedback = {
            is_correct: data.is_correct,
            is_final: data.is_final
        };
        if ('response' in data) {
            this.response = data.response;
        }
    }
}

/** the View
 * renders everything in html
 */
class View {
    constructor(model) {
        this.model = model;

        this.$progress = document.getElementById("progress-bar");
        this.$starthelp = document.getElementById("start-help");
        this.$focus = document.getElementById("focus");
        this.$stimulus = document.getElementById("stimulus");
        this.$stimulus_img = document.getElementById("stimulus-img");
        this.$stimulus_txt = document.getElementById("stimulus-txt");
        this.$response = document.getElementById("response");
        this.$response_txt = document.getElementById("response-txt");
        this.$warning_txt = document.getElementById("warning-txt");
    }

    _hide(elem) {
        elem.classList.add("hidden");
    }

    _show(elem) {
        elem.classList.remove("hidden");
    }

    reset() {
        /** clean up and hide everything */
        this.$stimulus_txt.textContent = null;
        this.$stimulus_img.src = null;
        this.$response_txt.textContent = null;
        this.$response.classList.remove("is-valid", "is-invalid");
        this.hideFocus();
        this.hideStimulus();
        this.hideResponse();
        this.showWarning("");
    }

    showStartHelp() {
        this._show(this.$starthelp);
    }

    hideStartHelp() {
        this._hide(this.$starthelp);
    }

    renderProgress(progress) {
        this.$progress.max = progress.iterations_total;
        this.$progress.value = progress.num_trials;
    }

    showFocus() {
        this._show(this.$focus);
    }

    hideFocus() {
        this._hide(this.$focus);
    }

    renderStimulus() {
        /** insert stimulus value in an appropriate place */
        this._hide(this.$stimulus_txt);
        this._hide(this.$stimulus_img);

        switch(this.model.stimulus.type) {
            case 'text':
                this.$stimulus_txt.textContent = this.model.stimulus.value;
                this._show(this.$stimulus_txt);
                break;
            case 'image-url':
                this.$stimulus_img.src = this.model.stimulus.url;
                this._show(this.$stimulus_img);
                break;
            case 'image-data':
                this.$stimulus_img.src = this.model.stimulus.data;
                this._show(this.$stimulus_img);
                break;
        }
    }

    showStimulus() {
        this._hide(this.$focus);
        this._show(this.$stimulus);
    }

    hideStimulus() {
        this._hide(this.$stimulus);
    }

    renderResponse() {
        this.$response_txt.textContent = PARAMS.labels[this.model.response];
        // the feedback can be null
        this.$response.classList.toggle("is-valid", this.model.feedback && this.model.feedback.is_correct === true);
        this.$response.classList.toggle("is-invalid", this.model.feedback && this.model.feedback.is_correct === false);
    }

    showResponse() {
        this._show(this.$response);
    }

    hideResponse() {
        this._show(this.$response);
    }

    showWarning(text) {
        if (text) {
            this.$warning_txt.textContent = text;
        } else {
            this.$warning_txt.textContent = "";
        }
    }
}

/** the Controller
 * implements main workflow
 * handles messages from server and user interactions
 */
class Controller {
    constructor(model, view) {
        this.model = model;
        this.view = view;

        this.starting = true;
        this.frozen = false;

        this.timers = new Timers();

        window.liveRecv = (message) => this.onMessage(message);
        document.querySelector('body').addEventListener('keydown', (e) => this.onKey(e));
        document.querySelectorAll('.touch-spot').forEach((t) => t.addEventListener('touchstart', (e) => this.onTouch(e)));

        this.view.showStartHelp();
    }

    reset() {
        this.frozen = false;
        this.timers.clear();
    }

    /**** game workflow actions ****/

    startGame() {
        this.starting = false;
        this.view.hideStartHelp();
        this.continueGame();
    }

    endGame() {
        document.getElementById("form").submit();
    }

    continueGame() {
        this.model.reset();
        this.view.reset();

        this.sendMessage('new');
    }

    displayStimulus() {
        // show focus cross
        this.freezeInputs();
        this.view.showFocus();

        // show stimulus
        this.timers.delay('showstimulus', PARAMS.focus_time, () => {
            this.unfreezeInputs();
            this.view.showStimulus();
            this.stimulus_ts = performance.now();
        });

        // hide stimulus
        if (PARAMS.stimulus_time) {
            this.timers.delay('hidestimulus', PARAMS.focus_time + PARAMS.stimulus_time,() => {
                this.view.hideStimulus();
            });
        }

        // auto response
        if (PARAMS.trial_timeout) {
            this.timers.delay('autoresponse', PARAMS.trial_timeout,() => {
                this.giveResponse( )
            });
        }
    }

    giveResponse(resp) {
        this.timers.cancel('hidestimulus');
        this.timers.cancel('resetinputs');

        this.model.setResponse(resp);
        this.view.renderResponse();

        this.view.showStimulus();
        this.view.showResponse();

        this.response_ts = performance.now();

        this.sendMessage('response', {response:resp, reaction: this.response_ts - this.stimulus_ts});

        this.freezeInputs();
        this.timers.delay('freezing', PARAMS.freeze_seconds * 1000, () => this.unfreezeInputs());
    }

    /**** handling messages from server ****/

    sendMessage(type, data) {
        console.debug("sending:", type, data);
        liveSend(Object.assign({type: type}, data));
    }

    onMessage(message) {
        console.debug("received:", message);

        switch(message.type) {
            case 'status':
                this.view.renderProgress(message.progress);
                if (message.trial) {  // restoring existing state
                    this.starting = false;
                    this.view.hideStartHelp();
                    this.onTrial(message.trial);
                } else if (message.progress.iteration === 0) {   // start of the game
                    this.starting = true;
                } else if (message.game_over) {  // exhausted max iterations
                    this.endGame();
                }
                break;

            case 'trial':
                this.onTrial(message.trial);
                break;

            case 'feedback':
                this.onFeedback(message);
                break;

            case 'solution':
                this.cheat(message);
                break;
        }
    }

    onTrial(trial) {
        this.model.reset();
        this.view.reset();

        this.model.setTrial(trial);
        this.view.renderStimulus();

        this.displayStimulus();
    }

    onFeedback(feedback) {
        this.model.setFeedback(feedback);
        this.view.renderResponse();

        if (feedback.is_final) {
            // advance to next trial
            this.view.renderProgress(feedback.progress);
            this.timers.delay('continue', PARAMS.trial_pause, () => this.continueGame());
        } else {
            // let more responses
            // TODO: perhaps, should better be PARAMS.feedback_time
            this.timers.delay('resetinputs', PARAMS.freeze_seconds, () => this.resetInputs());
        }
    }

    /**** handling interactions ****/

    freezeInputs() {
        /** block inputs to prevent fast retries */
        this.frozen = true;
    }

    unfreezeInputs() {
        /** unblock inputs */
        this.frozen = false;
        this.view.showWarning("");
    }

    resetInputs() {
        this.unfreezeInputs();
        this.model.setResponse(null);
        this.view.renderResponse();
    }

    checkFrozen() {
        if (this.frozen) {
            this.view.showWarning("Wait a bit...");
        }
        return this.frozen;
    }

    onKey(event) {
        if (this.checkFrozen()) return;

        if (this.starting) {
            if (event.code == 'Space') {
                event.preventDefault();
                this.startGame();
            }
            return;
        }

        if (event.code in CONF.keymap) {
            event.preventDefault();
            this.giveResponse(CONF.keymap[event.code]);
        }
    }

    onTouch(event) {
        if (this.checkFrozen()) return;

        if (this.starting) {
            this.startGame();
        } else {
            this.giveResponse(event.target.dataset.response);
        }
    }
}


/** timers utility
 * wraps setTimeout and clearTimeout
 * stores all timers by names
 */
class Timers {
    constructor() {
        this.timers = {};
    }

    delay(name, time, fn) {
        if (this.timers[name]) {
            clearTimeout(this.timers[name]);
        }

        this.timers[name] = setTimeout(() => {
            fn();
            delete this.timers[name];
        }, time * 1000);
    }

    cancel(name) {
        if (this.timers[name]) {
            clearTimeout(this.timers[name]);
            delete this.timers[name];
        }
    }

    clear() {
        for(let name in this.timers) {
            this.cancel(name);
        }
    }
}
