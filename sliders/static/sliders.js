class Model {
    /** hold all current game state */
    constructor() {
//        this.progress = {};
        this.values = [];
        this.correct = [];
        this.attempts = [];
    }

    reset() {
        this.values = [];
        this.correct = [];
    }

    load(values) {
        this.values = values;
        this.correct = values.map(v => false);
        this.attempts = values.map(v => 0);
    }
}


class View {
    /** renders everything */
    constructor(model, size) {
        this.model = model;
        this.slider_size = size;
//        this.$progress = document.getElementById("progress-bar");
        this.$canvas = document.getElementById("canvas");
        this.size = [];
        this.grid = [];
        this.img = new Image();
        this.canvas = this.$canvas.getContext('2d');
        this.picked_slider = null;
    }

    reset() {
        this.img.src = "";
        this.size = [];
        this.grid = [];
    }

    clear() {
        this.canvas.clearRect(0, 0, this.$canvas.wodth, this.$canvas.height);
    }

    load(size, image, grid) {
        this.size = size;
        this.grid = grid;
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
        this.grid.forEach((coord, i) => {
            let x = coord[0] + this.model.values[i],
                y = coord[1];
            this.drawHandle(x, y, {correct: this.model.correct[i]});
        });
    }

    drawSlider(i, state) {
        let x0 = this.grid[i][0], y0 = this.grid[i][1];
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
            this.canvas.fillStyle = "rgba(98, 0, 238, 0.04)";
            this.canvas.beginPath();
            this.canvas.arc(x, y, 20, 0, 2 * Math.PI);
            this.canvas.fill();
        } else if (state.dragged) {
            this.canvas.fillStyle = "rgba(98, 0, 238, 0.24)";
            this.canvas.beginPath();
            this.canvas.arc(x, y, 20, 0, 2 * Math.PI);
            this.canvas.fill();
        }

        // knob
        if (state.correct) {
            this.canvas.fillStyle = "rgb(0, 139, 0)";
        } else if (state.dragged) {
            this.canvas.fillStyle = "rgba(98, 0, 238, 0.5)";
        } else {
            this.canvas.fillStyle = "rgb(98, 0, 238)";
        }
        this.canvas.beginPath();
        this.canvas.arc(x, y, 10, 0, 2 * Math.PI);
        this.canvas.fill();
    }

    pickHandle(x, y) {
        for(let i=0; i < this.grid.length; i++) {
            let x0 = this.grid[i][0] + this.model.values[i], y0 = this.grid[i][1];
            let dx = x - x0, dy = y - y0;
            if (Math.abs(dx) < 10 && Math.abs(dy) < 10) {
                if (this.model.attempts[i] < js_vars.params.attempts_per_slider) return i;
                return null;
            }
        }
        return null;
    }

    mapHandle(i, x, y) {
        // return a value corresponding to coords
        let dx = x - this.grid[i][0];
        return Math.abs(dx) < this.slider_size[0]/2 ? dx : null;
    }

//    renderProgress() {
//        if (this.model.progress.total !== null) {
//            this.$progress.value = this.model.progress.iteration;
//        } else {
//            this.$progress.value = 0;
//        }
//    }
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
                    this.endGame();
                }
                break;

            case 'puzzle':
                this.recvPuzzle(message.puzzle);
                break;

            case 'feedback':
                this.recvFeedback(message);
                break;

            case 'solution':
                this.cheat(message.solution);
                break;
        }

//        if ('progress' in message) { // can be added to message of any type
//            this.recvProgress(message.progress);
//        }
    }

    recvPuzzle(data) {
        this.model.load(data.values);
        this.view.load(data.size, data.image, data.grid);
        this.view.render();
    }

    recvFeedback(message) {
        let i = message.slider;
        this.model.values[i] = message.value;
        this.model.correct[i] = message.is_correct;
        this.view.render();

        if (message.is_completed) { // current puzzle solved
            // auto advance to next
            window.setTimeout(() => this.reqNew(), js_vars.params.trial_delay * 1000);
        }
    }

//    recvProgress(data) {
//        this.model.progress = data;
//        this.view.renderProgress();
//    }

    startGame() {
        this.starting = false;
        this.reqNew();
    }

    submitSlider(i) {
        this.model.attempts[i] ++;
        liveSend({type: 'value', slider: i, value: this.model.values[i]});
    }

    reqNew() {
        this.model.reset();
        this.view.reset();
        this.view.clear();

        liveSend({type: 'new'});
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
        this.submitSlider(i);
    }

    endGame() {
        document.getElementById("form").submit();
    }

    cheat(values) {
        let i = 0;
        let timer = window.setInterval(() => {
            this.model.values[i] = values[i];
            this.submitSlider(i);

            i++;
            if (i >= this.model.values.length) window.clearInterval(timer);
        }, 100);
    }
}

window.onload = (event) => {
    const model = new Model();
    const view = new View(model, js_vars.slider_size);
    const ctrl = new Controller(model, view);
};
