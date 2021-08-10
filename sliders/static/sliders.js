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
    constructor(model, size) {
        this.model = model;
        this.slider_size = size;
        this.$progress = document.getElementById("progress-bar");
        this.$canvas = document.getElementById("canvas");
        this.size = [];
        this.sliders = [];
        this.img = new Image();
        this.canvas = this.$canvas.getContext('2d');
        this.picked_slider = null;
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
            let x = coord[0] + this.model.values[i],
                y = coord[1];
            this.drawHandle(x, y, {correct: this.model.correct[i]});
        });
    }

    drawSlider(i, state) {
        let x0 = this.sliders[i][0], y0 = this.sliders[i][1];
        let w = this.slider_size[0] + 40, h = this.slider_size[1];  // +40 margin
        let sx = x0 - w/2, sy = y0 - h/2;
        // copy slider cell from vackground image
        this.canvas.drawImage(this.img, sx, sy, w, h, sx, sy, w, h);
        // draw handle
        let x = x0 + this.model.values[i];
        state.correct = this.model.correct[i];
        this.drawHandle(x, y0, state);
    }

    drawHandle(x, y, state) {
        // hover area
        if (state.hover) {
            this.canvas.beginPath();
            this.canvas.arc(x, y, 20, 0, 2 * Math.PI);
            this.canvas.fillStyle = "rgba(98, 0, 238, 0.04)";
            this.canvas.fill();
        } else if (state.dragged) {
            this.canvas.beginPath();
            this.canvas.arc(x, y, 20, 0, 2 * Math.PI);
            this.canvas.fillStyle = "rgba(98, 0, 238, 0.24)";
            this.canvas.fill();
        }
        // knob
        if (state.correct) {
            this.canvas.beginPath();
            this.canvas.arc(x, y, 10, 0, 2 * Math.PI);
            this.canvas.fillStyle = "rgb(0, 139, 0)";
            this.canvas.fill();
        } else {
            this.canvas.beginPath();
            this.canvas.arc(x, y, 10, 0, 2 * Math.PI);
            this.canvas.fillStyle = "rgb(98, 0, 238)";
            this.canvas.fill();
        }
    }

    pickHandle(x, y) {
        for(let i=0; i < this.sliders.length; i++) {
            let x0 = this.sliders[i][0] + this.model.values[i], y0 = this.sliders[i][1];
            let dx = x - x0, dy = y - y0;
            if (Math.abs(dx) < 10 && Math.abs(dy) < 10) {
                return i ;
            }
        }
        return null;
    }

    mapHandle(i, x, y) {
        // return a value corresponding to coords
        let dx = x - this.sliders[i][0];
        return Math.abs(dx) < this.slider_size[0]/2 ? dx : null;
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

        this.picked_slider = null;
        this.hover_handle = null;
        this.view.$canvas.onmousedown = (e) => this.pickHandle(e);
        this.view.$canvas.onmousemove = (e) => this.picked_slider !== null ? this.dragHandle(e) : this.hoverHandle(e);
        this.view.$canvas.onmouseup = (e) => this.picked_slider !== null ? this.dropHandle(e) : null;

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
        this.picked_slider = i;
        if (i !== null) {
            this.view.drawSlider(i, {dragged: true});
        }
    }

    hoverHandle(event) {
        let i = this.view.pickHandle(event.offsetX, event.offsetY);
        if (this.hover_handle != i) {
            if (this.hover_handle !== null) {
                this.view.drawSlider(this.hover_handle, {hover: false});
            }
            this.hover_handle = i;
            if (this.hover_handle !== null) {
                this.view.drawSlider(this.hover_handle, {hover: true});
            }
        }
    }

    dragHandle(event) {
        let i = this.picked_slider;
        let val = this.view.mapHandle(i, event.offsetX, event.offsetY);
        if (val !== null) {
            this.model.values[i] = val;
            this.view.drawSlider(i, {dragged: true});
        }
    }

    dropHandle(event) {
        let i = this.picked_slider;
        this.view.drawSlider(i, {});
        this.picked_slider = null;
        this.submitValues();
    }
}

window.onload = (event) => {
    const model = new Model();
    const view = new View(model, js_vars.slider_size);
    const ctrl = new Controller(model, view);
};
