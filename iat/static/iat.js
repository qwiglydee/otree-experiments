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
            this.$progress.value = (this.model.progress.iteration - 1)/ this.model.progress.total;
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

        window.liveRecv = (data) => {
            if ('question' in data ) {
                this.recvQuestion(data.question);
            }
            if ('feedback' in data) {
                this.recvFeedback(data.feedback);
            }
            if ('gameover' in data) {
                this.recvGameover();
            }
            if ('progress' in data) {
                this.recvProgress(data.progress);
            }
        }

        document.querySelector('body').onkeydown = (ev) => {
            if (ev.code == 'Space' && this.starting) {
                ev.preventDefault();
                this.view.hideStartInstruction();
                liveSend({});
                this.starting = false;
            }

            if (this.model.stimulus !== null) {
                if (ev.key == js_vars.keys.left) {
                    this.giveAnswer('left');
                }

                if (ev.key == js_vars.keys.right) {
                    this.giveAnswer('right');
                }
            }
        }
    }

    start() {
        this.starting = true;
        this.view.showStartInstruction();
    }

    reqNext() {
        this.model.stimulus = null;
        this.model.answer = null;
        this.view.renderStimulus();
        this.view.renderAnswer();
        liveSend({next: true});
    }

    recvQuestion(question) {
        this.model.stimulus = question.word;
        this.model.stimulus_cls = question.cls;
        this.model.answer = null;

        this.view.renderStimulus();
        this.view.renderAnswer();

        this.ts_question = performance.now();
        this.ts_answer = 0;
    }

    giveAnswer(answer) {
        this.ts_answer = performance.now();
        this.model.answer = answer;
        liveSend({answer: answer, reaction: this.ts_answer - this.ts_question});
        this.view.renderAnswer();
    }

    recvFeedback(feedback) {
        this.model.feedback = feedback;
        this.view.renderAnswer();

        if (feedback === true) {
            window.setTimeout(() => this.reqNext(), js_vars.trial_delay * 1000);
        }
    }

    recvProgress(data) {
        this.model.progress = data;
        this.view.renderProgress();
    }

    recvGameover() {
        document.getElementById("form").submit();
    }
}

window.onload = (event) => {
    const model = new Model();
    const view = new View(model);
    const ctrl = new Controller(model, view);
    ctrl.start();
};
