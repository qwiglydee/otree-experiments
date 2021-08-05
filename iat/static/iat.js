class Model {
    /** hold all current game state */
    constructor() {
        this.stimulus = null;
        this.stimulus_cls = null;
        this.progress = {};

        this._answer = null;
        this._feedback = null;
    }


    set answer(val) {
        this._answer = val;
        this._feedback = null;
    }

    get answer() {
        return this._answer;
    }

    set feedback(val) {
        this._feedback = val;
    }

    get feedback() {
        return this._feedback;
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
        if (this.model.feedback !== null) {
            if (this.model.feedback) {
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
        this.view.showStartInstruction();
    }

    recvMessage(message) {
        console.debug("received:", message);
        switch(message.type) {
            case 'status':
                if (message.trial) {
                    this.recvTrial(message.trial);
                } else if (message.progress.iteration === 0) {   // start of the game
                    liveSend({type: 'next'});
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

    recvTrial(question) {
        this.model.stimulus = question.word;
        this.model.stimulus_cls = question.cls;
        this.model.answer = null;

        this.view.renderStimulus();
        this.view.renderAnswer();

        this.ts_question = performance.now();
        this.ts_answer = 0;
    }

    recvFeedback(message) {
        this.model.feedback = message.is_correct;
        this.view.renderAnswer();

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
            this.view.hideStartInstruction();
            liveSend({type: 'load'});
            this.starting = false;
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
        liveSend({type: 'answer', answer: answer, reaction_time: (this.ts_answer - this.ts_question)/1000});
        this.view.renderAnswer();
    }

    reqNext() {
        this.model.stimulus = null;
        this.model.answer = null;
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
