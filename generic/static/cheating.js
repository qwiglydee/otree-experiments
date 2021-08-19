let cheat_btn = document.getElementById('cheat-btn');
let cheat_inp = document.getElementById('cheat-rt-inp');
cheat_btn.onclick = function() {
    liveSend({type: 'cheat', rt: cheat_inp.value});
}
