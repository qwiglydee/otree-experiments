class Model {
    /** hold all current game state */
    constructor() {
        this.progress = {};
        this.values = [];
        this.correct = [];
    }

    reset() {
        this.values = [];
        this.correct = [];
    }

    load(values) {
        this.values = values;
        this.correct = values.map(v => false);
    }
}


class View {
    /** renders everything */
    constructor(model, size, step) {
        this.model = model;
        this.slider_step = step;
        this.slider_size = size;
        this.handle_radius = size[1]/2 + 0.5;
        this.$progress = document.getElementById("progress-bar");
        this.$canvas = document.getElementById("canvas");
        this.size = [];
        this.sliders = [];
        this.img = new Image();
        this.canvas = this.$canvas.getContext('2d');
        this.picked_handle = null;
    }

    reset() {
        this.img.src = "";
        this.size = [];
        this.sliders = [];
    }

    clear() {
        this.canvas.clearRect(0, 0, this.$canvas.wodth, this.$canvas.height);
    }

    load(size, sliders, image) {
        this.size = size;
        this.sliders = sliders;
        this.img.src = image;
        this.img.width = size[0];
        this.img.height = size[1];
        this.$canvas.width = this.img.width;
        this.$canvas.height = this.img.height;
    }

    render() {
        if (this.img.src && !this.img.complete) {  // image's still loading
            this.img.onload = () => this.render();
            return;
        }
        this.canvas.drawImage(this.img, 0, 0);
        this.sliders.forEach((coord, i) => {
            this.drawHandle(coord, this.model.values[i], this.model.correct[i]);
        });
    }

    clearHandle(slider) {
        let x0 = slider[0], y0 = slider[1];
        let w = this.slider_size[0] + 4, h = this.slider_size[1] + 4;
        let sx = x0 - w/2, sy = y0 - h/2;
        this.canvas.drawImage(this.img, sx, sy, w, h, sx, sy, w, h);
    }

    drawHandle(slider, value, correct, picked) {
        this.clearHandle(slider);
        let x0 = slider[0], y0 = slider[1];
        this.canvas.beginPath();
        this.canvas.arc(x0 + value, y0, this.handle_radius, 0, 2 * Math.PI);
        this.canvas.lineWidth = 2;
        if (picked) {
            this.canvas.strokeStyle = "rgb(64, 64, 128)";
            this.canvas.fillStyle = "rgba(64, 64, 128, 0.5)";
        } else if (!correct) {
            this.canvas.strokeStyle = "rgb(64, 64, 128)";
            this.canvas.fillStyle = "rgba(64, 64, 128, 1.0)";
        } else {
            this.canvas.strokeStyle = "rgb(64, 128, 64)";
            this.canvas.fillStyle = "rgba(64, 128, 64, 1.0)";
        }
        this.canvas.stroke();
        this.canvas.fill();
    }

    pickHandle(x, y) {
        for(let i=0; i < this.sliders.length; i++) {
            let x0 = this.sliders[i][0], y0 = this.sliders[i][1];
            let dx = x - x0, dy = y - y0;
            if (Math.abs(dx) < this.slider_size[0] && Math.abs(dy) < this.slider_size[1]) {
                let value = this.model.values[i];
                let vdx = x - (x0 + value);
                if (Math.abs(vdx) < this.handle_radius) return i;
                else return i;
            }
        }
        return null;
    }

    snapHandle(i, x, y) {
        let x0 = this.sliders[i][0], y0 = this.sliders[i][1];
        let val = Math.round((x - x0) / this.slider_step) * this.slider_step;
        return val;
    }

    renderProgress() {
        if (this.model.progress.total !== null) {
            this.$progress.value = this.model.progress.num_trials;
        } else {
            this.$progress.value = 0;
        }
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


        this.picked_handle = null;
        this.view.$canvas.onmousedown = (e) => this.pickHandle(e);
        this.view.$canvas.onmousemove = (e) => this.dragHandle(e);
        this.view.$canvas.onmouseup = (e) => this.dropHandle(e);

        liveSend({type: 'load'});
    }

    recvMessage(message) {
        // console.debug("received:", message);
        switch(message.type) {
            case 'status':
                if (message.puzzle) {  // restoring existing state
                    this.starting = false;
                    this.recvPuzzle(message.puzzle);
                } else if (message.progress.iteration === 0) {   // start of the game
                    this.startGame();
                } else if (message.iterations_left === 0) {  // exhausted max iterations
                    document.getElementById("form").submit();
                }
                break;

            case 'puzzle':
                this.recvPuzzle(message.puzzle);
                break;

            case 'feedback':
                this.recvFeedback(message);
                break;

            case 'solution':
                this.model.values = message.solution;
                this.submitValues();
                break;
        }

        if ('progress' in message) { // can be added to message of any type
            this.recvProgress(message.progress);
        }
    }

    recvPuzzle(data) {
        this.model.load(data.initial);
        this.view.load(data.size, data.coords, data.image);
        this.view.render();
    }

    recvFeedback(message) {
        this.model.correct = message.is_correct;
        this.view.render();
        // auto advance to next after correct answer
        if (message.is_correct.every(e=>e)) {
            window.setTimeout(() => this.reqNext(), js_vars.params.trial_delay * 1000);
        }
    }

    recvProgress(data) {
        this.model.progress = data;
        this.view.renderProgress();
    }

    startGame() {
        this.starting = false;
        this.reqNext();
    }

    submitValues() {
        liveSend({type: 'values', values: this.model.values});
    }

    reqNext() {
        this.model.reset();
        this.view.reset();
        this.view.clear();

        liveSend({type: 'next'});
    }

    pickHandle(event) {
        let i = this.view.pickHandle(event.offsetX, event.offsetY);
        this.picked_handle = i;
        if (i !== null) {
            this.view.drawHandle(this.view.sliders[i], this.model.values[i], false, true);
        }
    }

    dragHandle(event) {
        if (this.picked_handle === null) return;
        let i = this.picked_handle;
        let val = this.view.snapHandle(i, event.offsetX, event.offsetY);
        if (val !== null) {
            this.model.values[i] = val;
            this.view.drawHandle(this.view.sliders[i], this.model.values[i], false, true);
        }
    }

    dropHandle(event) {
        if (this.picked_handle === null) return;
        let i = this.picked_handle;
        this.view.drawHandle(this.view.sliders[i], this.model.values[i], this.model.correct[i], false);
        this.picked_handle = null;
        this.submitValues();
    }
}

window.onload = (event) => {
    const model = new Model();
    const view = new View(model, js_vars.slider_size, js_vars.slider_step);
    const ctrl = new Controller(model, view);
};
