class Model {
    /** hold all current game state */
    constructor() {
        this.progress = {};
        this.stimulus = null;
        this.stimulus_cls = null;
        this.stimulus_cat = null;
        this.answer = null;
        this.is_correct = null;
    }

    resetStimulus() {
        this.stimulus = null;
        this.stimulus_cls = null;
        this.stimulus_cat = null;
    }

    resetAnswer() {
        this.answer = null;
        this.is_correct = null;
    }

    resetFeedback() {
        this.is_correct = null;
    }
}

class View {
    /** renders everything */
    constructor(model) {
        this.model = model;
        this.$progress = document.getElementById("progress-bar");
        this.$stimulus_txt = document.getElementById("stimulus");
        this.$stimulus_img = document.getElementById("stimulus-img");
        this.$answer = document.getElementById("answer-inp");
        this.$starthelp = document.getElementById("start-help");
        this.$warn = document.getElementById("warning-txt");
    }

    renderStimulus() {
        this.$stimulus_txt.classList.remove("primary", "secondary");
        this.$stimulus_img.classList.remove("primary", "secondary");

        if (this.model.stimulus !== null) {
            let is_image = js_vars.params[`${this.model.stimulus_cls}_images`];
            let is_prim = this.model.stimulus_cls == 'primary',
                is_sec = this.model.stimulus_cls == 'secondary';

            this.$stimulus_txt.classList.toggle("hidden", is_image);
            this.$stimulus_img.classList.toggle("hidden", !is_image);
            if (is_image) {
                this.$stimulus_img.src = images_url + this.model.stimulus;
                this.$stimulus_img.classList.add(this.model.stimulus_cls);
            } else {
                this.$stimulus_txt.textContent = this.model.stimulus;
                this.$stimulus_txt.classList.add(this.model.stimulus_cls);
            }
        } else {
            this.$stimulus_txt.textContent = "";
            this.$stimulus_img.src = "";
        }
    }

    answer_symbols = {'left': "⇦", 'right': "⇨"}

    renderAnswer() {
        if (this.model.answer !== null) {
            this.$answer.value = this.answer_symbols[this.model.answer];
        } else {
            this.$answer.value = "";
        }

        this.$answer.classList.remove("is-valid", "is-invalid");
        if (this.model.is_correct !== null) {
            if (this.model.is_correct) {
                this.$answer.classList.add("is-valid");
            } else {
                this.$answer.classList.add("is-invalid");
            }
        }
    }

    renderProgress() {
        if (this.model.progress.total !== null) {
            this.$progress.value = this.model.progress.iteration;
        } else {
            this.$progress.value = 0;
        }
    }

    showStartInstruction() {
        this.$starthelp.classList.remove("hidden");
    }

    hideStartInstruction() {
        this.$starthelp.classList.add("hidden");
    }

    showWarning(text) {
        this.$answer.classList.add("is-invalid");
        this.$warn.textContent = text;
    }

    resetWarning() {
        this.$warn.textContent = "";
    }
}

class Controller {
    /** handles everything */
    constructor(model, view) {
        this.model = model;
        this.view = view;

        this.input_disabled = false;
        this.starting = true;
        this.ts_question = 0;
        this.ts_answer = 0;

        window.liveRecv = (message) => this.recvMessage(message);
        document.querySelector('body').addEventListener('keydown', (e) => this.onKeypress(e));
        document.querySelector('.stimulus-container').addEventListener('touchstart', (e) => this.onTouchMiddle(e));
        document.querySelector('.corners-container').addEventListener('touchstart', (e) => this.onTouchCorner(e));

        liveSend({type: 'load'});
    }

    recvMessage(message) {
        // console.debug("received:", message);
        switch(message.type) {
            case 'status':
                if (message.trial) {  // restoring existing state
                    this.recvTrial(message.trial);
                    this.view.hideStartInstruction();
                } else if (message.progress.iteration === 0) {   // start of the game
                    this.starting = true;
                    this.view.showStartInstruction();
                } else if (message.iterations_left === 0) {  // exhausted max iterations
                    document.getElementById("form").submit();
                }
                break;

            case 'trial':
                this.recvTrial(message.trial);
                break;

            case 'feedback':
                this.recvFeedback(message);
                break;
        }

        if ('progress' in message) { // can be added to message of any type
            this.recvProgress(message.progress);
        }
    }

    recvTrial(data) {
        this.ts_question = performance.now();
        this.ts_answer = 0;

        this.model.stimulus = data.stimulus;
        this.model.stimulus_cls = data.cls;
        this.model.stimulus_cat = data.cat;
        this.model.resetAnswer();

        this.view.renderStimulus();
        this.view.renderAnswer();

    }

    recvFeedback(message) {
        this.model.is_correct = message.is_correct;
        this.view.renderAnswer();

        if (message.is_correct) {
            // auto advance to next after correct answer
            window.setTimeout(() => this.reqNext(), js_vars.params.trial_delay * 1000);
        }
    }

    recvProgress(data) {
        this.model.progress = data;
        this.view.renderProgress();
    }

    onKeypress(event) {
        if (event.code == 'Space' && this.starting) {
            event.preventDefault();
            this.startGame();
        }

        if (this.model.stimulus === null) return;
        if (!(event.key in js_vars.keys)) return;

        if (this.input_disabled) {
            this.view.showWarning("Wait a bit...");
            return;
        }
        this.input_disabled = true;
        window.setTimeout(() => this.enableInput(), js_vars.params.retry_delay * 1000);

        let answer = js_vars.keys[event.key];
        this.setAnswer(answer);
        this.submitAnswer();
    }

    onTouchMiddle(event) {
//        console.debug("touch", event);
        if (this.starting) {
            this.startGame();
        }
    }

    onTouchCorner(event) {
//        console.debug("touch", event);
        if (this.model.stimulus !== null) {
            if (event.target.classList.contains('left')) {
                this.setAnswer('left');
                this.submitAnswer();
            }
            if (event.target.classList.contains('right')) {
                this.setAnswer('right');
                this.submitAnswer();
            }
        }
    }

    startGame() {
        this.starting = false;
        this.view.hideStartInstruction();
        this.reqNext();
    }

    disableInput() {

        // NB: do not show warning until actual preliminary keypress inducing "invalid" state
    }

    enableInput() {
        this.input_disabled = false;
        this.model.resetAnswer();
        this.view.resetWarning();
        this.view.renderAnswer();
    }

    setAnswer(answer) {
        this.model.answer = answer;
        this.model.resetFeedback();
        this.view.renderAnswer();
    }

    submitAnswer() {
        this.ts_answer = performance.now();
        liveSend({type: 'answer', answer: this.model.answer, reaction_time: (this.ts_answer - this.ts_question)/1000});
    }

    reqNext() {
        this.model.resetStimulus();
        this.model.resetAnswer();
        this.view.renderStimulus();
        this.view.renderAnswer();

        liveSend({type: 'next'});
   }
}

window.onload = (event) => {
    const model = new Model();
    const view = new View(model);
    const ctrl = new Controller(model, view);
};
