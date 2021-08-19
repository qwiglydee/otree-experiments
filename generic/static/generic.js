liveRecv = function(msg) {
    console.debug("received:", msg)
}

function send(type, data) {
    msg = Object.assign({}, {type: type}, data)
    console.debug("sending:", msg);
    liveSend(msg);
}