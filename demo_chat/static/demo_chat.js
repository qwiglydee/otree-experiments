liveRecv = otree.live_utils.livePageRecv;

function main() {
  let page = otree.page;

  let mynickname;
  let recipient;
  let party;
  let chat = [],
    maxlog = 10;

  function loadParty(data) {
    party = data;
    page.update({ party: party });
  }

  function addMessage(cls, txt, src, dst) {
    chat.push({ class: cls, text: txt, source: src, dest: dst });
    chat = chat.slice(-maxlog);
    page.update({ chat: chat });
  }

  function resetInput() {
    recipient = undefined;
    page.reset(['text', 'recipient']);
  }

  page.onEvent("ot.live.joined", function (event, data) {
    console.debug("joined", data);
    loadParty(data.party);
    addMessage('system', `Welcome, ${data.newcomer}!`);
  });

  page.onEvent("ot.live.left", function (event, data) {
    console.debug("left", data);
    loadParty(data.party);
    addMessage('system', `Bye, ${data.nickname}!`);
  });

  page.onEvent("ot.live.talk", function (event, data) {
    console.debug("talk", data);
    addMessage('talk', data.text, data.source);
  });

  page.onEvent("ot.live.wisper", function (event, data) {
    console.debug("wisper", data);
    addMessage('wisper', data.text, data.source, mynickname);
  });

  page.onEvent("chat.clear", function () {
    recipinent = null;
    page.reset(['text', 'recipient']);
  });

  page.onEvent("chat.send", function () {
    page.submitInputs('text');
  });

  page.onEvent("chat.leave", function () {
    liveSend({ type: "leave" });
    page.update({ stage: "left" });
    otree.utils.timers.delay(() => page.submit(), 3000);
});

  page.onInput = function (name, value) {
    console.debug("input", name, value);

    if (name == "nickname") {
      mynickname = value;
      liveSend({ type: "join", nickname: mynickname });
      page.update({ stage: "chatting" });
    }

    if (name == "text") {
      if (recipient != undefined ) {
        liveSend({ type: "wispering", text: value, dest: recipient });
        addMessage('wisper', value, mynickname, recipient);
      } else {
        liveSend({ type: "saying", text: value });
      }
      resetInput();
    }

    if (name == 'recipient') {
      recipient = party[value];
      page.update({ recipient: recipient });
    }
  };

  page.update({ stage: "joining" });
}
