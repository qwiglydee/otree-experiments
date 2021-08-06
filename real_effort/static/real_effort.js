/*
Generic game workflow, from client's point of view:

- send: {type: 'load'} -- when page loaded or reloaded
- receive: {type: 'status', progress: ...} -- if the game just started
- receive: {type: 'status', progress: ..., puzzle: data} -- in case of reload midgame

- send: {type: 'next'} -- request puzzle
- receive: {type: 'puzzle', puzzle: data, progress: ...}
- display the puzzle and progress
- wait for user to answer

- send: {type: 'answer', 'answer': ...}
- receive: {type: 'feedback', is_correct: ..., progress: ..., retries_left: ...}
- display feedback and progress
- if the anwser is wrong and retries allowed:
  - wait for new answer from user
  - lock submitting for `retry_delay`

- wait for `puzzle_delay` seconds
- request next puzzle

- receive {type: 'status', progress: ..., iterations_left: 0} -- when max_iterations exhausted
*/

let isFrozen = false;  // retry delay active, submitting is blocked
let image = document.getElementById('captcha-img');
let input = document.getElementById('answer-inp');
let warn = document.getElementById('warning-txt');
let submit_btn = document.getElementById('submit-btn');
let fields = {
    iter: document.getElementById('iter-txt'),
    solved: document.getElementById('solved-txt'),
    failed: document.getElementById('failed-txt'),
}

document.addEventListener("DOMContentLoaded", (event) => {
    liveSend({type: 'load'}); // expect 'status' response
});

function liveRecv(message) {
    switch(message.type) {

        case 'status':
            if (message.puzzle) { // restoring existing state
                newPuzzle(message.puzzle);
            } else if (message.progress.iteration === 0) {   // start of the game
                liveSend({type: 'next'});
            } else if (message.iterations_left === 0) {  // exhausted max iterations
                document.getElementById("form").submit();
            }
            break;

        case 'puzzle':
            newPuzzle(message.puzzle);
            break;

        case 'feedback':
            showFeedback(message);
            if (message.is_correct === false && message.retries_left > 0) { // allow retry
                tempFreeze(js_vars.params.retry_delay);
                enableInput();
            } else {
                moveForward(js_vars.params.puzzle_delay);
            }
            break;

        case 'solution':
            cheat(message.solution);
            break;
    }

    if ('progress' in message) { // can be added to message of any type
        showProgress(message.progress);
    }
}

input.oninput = function (ev) {
    resetFeedback();
}

input.onkeydown = function (ev) {
    if (ev.key === 'Enter') {
        submitAnswer();
    }
}

submit_btn.onclick = function (ev) {
    submitAnswer();
}

function newPuzzle(data) {
    showPuzzle(data);
    resetFeedback();
    resetInput();
    enableInput();
}


function resetPuzzle() {
    // a trick to avoid image collapsing/blinking
    image.width = image.width;
    image.height = image.height;

    image.src = "";
}

function showPuzzle(data) {
    image.src = data.image;
}

function resetInput() {
    input.value = "";
}

function lockInput() {
    input.disabled = true;
    input.blur();
}

function enableInput() {
    input.disabled = false;
    input.focus();
}

function submitAnswer() {
    if (isFrozen || input.value === "") return;
    lockInput();
    resetFeedback();
    liveSend({type: 'answer', answer: input.value});
}

function resetFeedback() {
    input.classList.remove("is-valid", "is-invalid");
}

function showFeedback(data) {
    input.classList.add(data.is_correct ? "is-valid" : "is-invalid");
}


function moveForward(wait) {
    window.setTimeout(gotoNext, wait * 1000);
}

function gotoNext() {
    resetPuzzle();
    resetInput();
    resetFeedback();
    liveSend({type: 'next'});
}

function showProgress(data) {
    fields.iter.textContent = data.iteration;
    fields.solved.textContent = data.num_correct;
    fields.failed.textContent = data.num_incorrect;
}

function waitMsg(seconds) {
    warn.textContent = `Wait ${Math.round(seconds)} seconds before trying again`;
}

function setFrozen(val) {
    // freeze/unfreeze submitting
    submit_btn.disabled = val;
    isFrozen = val;
}

function tempFreeze(countdown) {
    setFrozen(true);
    waitMsg(countdown);
    let timer = window.setInterval(function() {
        countdown -= 1;
        if (countdown > 0) {
            waitMsg(countdown);
        } else {
            setFrozen(false);
            warn.textContent = "";
            clearInterval(timer);
        }
    }, 1000);
}
