let cheat_btn = document.getElementById('cheat-btn');
cheat_btn.onclick = function() {
    liveSend({cheat: true});
}

function cheat(solution) {
    input.value = solution;
}
