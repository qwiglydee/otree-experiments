let cheat_btn = document.getElementById('cheat-btn');
let cheat_inp = document.getElementById('cheat-reaction');
cheat_btn.onclick = function() {
    liveSend({'type': 'cheat', reaction: cheat_inp.value});
}
