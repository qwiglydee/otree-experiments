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
        this.$stimulus = document.getElementById("stimulus");
        this.$answer = document.getElementById("answer-inp");
        this.$starthelp = document.getElementById("start-help");
    }

    renderStimulus() {
        if (this.model.stimulus !== null) {
            this.$stimulus.textContent = this.model.stimulus;
            this.$stimulus.classList.remove("primary", "secondary");
            this.$stimulus.classList.add(this.model.stimulus_cls);
        } else {
            this.$stimulus.textContent = "";
            this.$stimulus.classList.remove("primary", "secondary");
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
            this.$progress.value = this.model.progress.num_trials / this.model.progress.total;
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
}

class Controller {
    /** handles everything */
    constructor(model, view) {
        this.model = model;
        this.view = view;

        this.starting = true;
        this.ts_question = 0;
        this.ts_answer = 0;

        window.liveRecv = (message) => this.recvMessage(message);
        document.querySelector('body').onkeydown = (ev) => this.onKeypress(event);
    }

    start() {
        this.starting = true;
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

        this.model.stimulus = data.word;
        this.model.stimulus_cls = data.cls;
        this.model.stimulus_cat = data.cat;
        this.model.resetAnswer();

        this.view.renderStimulus();
        this.view.renderAnswer();

    }

    recvFeedback(message) {
        this.model.is_correct = message.is_correct;
        this.view.renderAnswer();

        // auto advance to next after correct answer
        if (message.is_correct) {
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
            this.starting = false;
            this.view.hideStartInstruction();
            this.reqNext();
        }

        if (this.model.stimulus !== null) {
            if (event.key == js_vars.keys.left) {
                this.submitAnswer('left');
            }
            if (event.key == js_vars.keys.right) {
                this.submitAnswer('right');
            }
        }
    }

    submitAnswer(answer) {
        this.ts_answer = performance.now();
        this.model.answer = answer;
        this.model.resetFeedback();
        this.view.renderAnswer();

        liveSend({type: 'answer', answer: answer, reaction_time: (this.ts_answer - this.ts_question)/1000});
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
    ctrl.start();
};
