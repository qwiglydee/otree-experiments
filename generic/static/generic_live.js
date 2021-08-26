/** the Model
 * holds all current state data
 */
class Model {
    constructor() {
        this.reset();
        this.progress = null;
    }

    reset() {
        this.stimulus = null;
        this.response = null;
        this.feedback = null;
    }

    setTrial(data) {
        this.stimulus = data.stimulus;
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
        this.$response = document.getElementById("response");
        this.$response_txt = document.getElementById("response-txt");
        this.$warning_txt = document.getElementById("warning-txt");
    }

    hide(elem) {
        elem.classList.add("hidden");
    }

    show(elem) {
        elem.classList.remove("hidden");
    }

    reset() {
        /** clean up and hide everything */
        this.$stimulus.replaceChildren();
        this.$response.classList.remove("is-valid", "is-invalid");
        this.hideFocus();
        this.hideStimulus();
        this.hideResponse();
        this.showWarning("");
    }

    showStartHelp() {
        this.show(this.$starthelp);
    }

    hideStartHelp() {
        this.hide(this.$starthelp);
    }

    renderProgress() {
        let progress = this.model.progress;
        this.$progress.max = progress.iterations_total;
        this.$progress.value = progress.num_trials;
    }

    showFocus() {
        this.show(this.$focus);
    }

    hideFocus() {
        this.hide(this.$focus);
    }


    _createStimulusElem(tagname) {
        let elem = document.createElement(tagname);
        this.$stimulus.replaceChildren();
        this.$stimulus.append(elem);
        return elem;
    }

    async _loadImage(elem, url) {
        return new Promise((resolve, reject) => {
            elem.onload = () => resolve();
            elem.onerror = reject;
            elem.src = url;
        });
    }

    async loadStimulus() {
        /** insert stimulus value in an appropriate place
        Returns: a promise resolving when content is loaded and ready to show
        */
        var elem;
        switch(this.model.stimulus.type) {
            case 'text':
                elem = this._createStimulusElem("span");
                elem.textContent = this.model.stimulus.text;
                return Promise.resolve();
            case 'image-url':
                elem = this._createStimulusElem("img");
                return this._loadImage(elem, this.model.stimulus.url);
            case 'image-data':
                elem = this._createStimulusElem("img");
                return this._loadImage(elem, this.model.stimulus.data);
        }
        return Promise.reject("unknown stimulus type");
    }

    showStimulus() {
        this.hide(this.$focus);
        this.show(this.$stimulus);
    }

    hideStimulus() {
        this.hide(this.$stimulus);
    }

    renderResponse() {
        this.$response_txt.textContent = PARAMS.labels[this.model.response];
        // the feedback can be null
        this.$response.classList.toggle("is-valid", this.model.feedback && this.model.feedback.is_correct === true);
        this.$response.classList.toggle("is-invalid", this.model.feedback && this.model.feedback.is_correct === false);
    }

    showResponse() {
        this.show(this.$response);
    }

    hideResponse() {
        this.hide(this.$response);
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

        window.liveRecv = (message) => this.onMessage(message);
        document.querySelector('body').addEventListener('keydown', (e) => this.onKey(e));
        document.querySelectorAll('.touch-spot').forEach((t) => t.addEventListener('touchstart', (e) => this.onTouch(e)));

        this.view.showStartHelp();
    }

    reset() {
        this.frozen = false;
        timers.clear();
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

    async displayTrial() {
        performance.mark("loading");
        await this.view.loadStimulus();
        console.debug("image load:", performance.measure("image_load", "loading"));

        this.freezeInputs();
        this.view.showFocus();
        await timers.sleep(PARAMS.focus_display_time);
        this.view.hideFocus();

        this.view.showStimulus();
        this.unfreezeInputs();
        performance.mark("display");

        if (PARAMS.stimulus_display_time) {
            timers.delay(PARAMS.stimulus_display_time, () => this.view.hideStimulus(), "hiding_stimulus");
        }
    }

    hideTrial() {
        this.view.hideFocus();
        this.view.hideStimulus();
        this.view.hideResponse();
        this.view.showWarning("");
    }

    displayResponse() {
        this.view.renderResponse();
        this.view.showStimulus();
        this.view.showResponse();
        this.freezeInputs();
        timers.delay(PARAMS.input_freezing_time, () => this.unfreezeInputs(), "unfreezing");
    }

    displayFeedback() {
        this.view.renderResponse();
        timers.delay(PARAMS.feedback_display_time, () => this.hideTrial(), "hiding_feedback");
    }

    /**** handling messages from server ****/

    sendMessage(type, data) {
        console.debug("sending:", type, data);
        liveSend(Object.assign({type: type}, data));
    }

    onMessage(message) {
        console.debug("received:", message);

        if (message.progress)
            this.model.progress = message.progress;

        switch(message.type) {
            case 'status':
                if (message.trial) {  // restoring existing state
                    this.onReload(message);
                } else if (message.progress.iteration === 0) {   // start of the game
                    this.starting = true;
                } else if (message.game_over) {  // exhausted max iterations
                    this.endGame();
                }
                break;

            case 'trial':
                this.onTrial(message);
                break;

            case 'feedback':
                this.onFeedback(message);
                break;

            case 'solution':
                this.cheat(message);
                break;
        }
    }

    onReload(message) {
        this.starting = false;
        this.view.hideStartHelp();
        this.onTrial(message);
    }

    onTrial(message) {
        performance.clearMarks();
        performance.clearMeasures();
        timers.clear();

        this.model.reset();
        this.view.reset();
        this.view.renderProgress();
        this.model.setTrial(message.trial);
        this.displayTrial();

        if (PARAMS.auto_response_time) {
            timers.delay(PARAMS.auto_response_time,() => this.onResponse(null), "auto_responding");
        }
    }

    onResponse(response) {
        performance.mark("response");
        timers.clear();

        this.model.setResponse(response);
        this.displayResponse();

        let measure = performance.measure("reaction_time", "display", "response");
        this.sendMessage('response', {response: this.model.response, reaction_time: measure.duration});
    }

    onFeedback(feedback) {
        timers.clear();
        this.model.setFeedback(feedback);
        this.displayFeedback();

        if (feedback.is_final) {
            this.view.renderProgress();
            timers.delay(PARAMS.inter_trial_time, () => this.continueGame(), "advancing");
            return;
        }

        if (PARAMS.auto_response_time) {
            timers.delay(PARAMS.auto_response_time,() => this.onResponse(null), "auto_responding");
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
            this.onResponse(CONF.keymap[event.code]);
        }
    }

    onTouch(event) {
        if (this.checkFrozen()) return;

        if (this.starting) {
            this.startGame();
        } else {
            this.onResponse(event.target.dataset.response);
        }
    }
}
