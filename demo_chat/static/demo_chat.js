liveRecv = otree_live_utils.livePageRecv;

function main() {
  let page = otree.page;

  let mynickname;
  let recipient;
  let party;
  let chat = [],
    maxlog = 10;

  function loadParty(data) {
    party = data;
    page.emitUpdate({ party: party });
  }

  function addMessage(cls, txt, src, dst) {
    chat.push({ class: cls, text: txt, source: src, dest: dst });
    chat = chat.slice(-maxlog);
    page.emitUpdate({ chat: chat });
  }

  function resetInput() {
    recipient = undefined;
    page.emitReset(['text', 'recipient']);
  }

  page.onEvent("ot.live.joining", function (event) {
    let data = event.detail;
    console.debug("ot.live.joining", data);

    if (data.newcomer == mynickname) {
      page.emitUpdate({ phase: "chatting" });
    }
    
    loadParty(data.party);
    addMessage('system', `Welcome, ${data.newcomer}!`);
  });

  page.onEvent("ot.live.saying", function (event) {
    let data = event.detail;
    console.debug("ot.live.saying", data);
    addMessage('talk', data.text, data.source);
  });

  page.onEvent("ot.live.wispering", function (event) {
    let data = event.detail;
    console.debug("ot.live.wispering", data);
    addMessage('wisper', data.text, data.source, mynickname);
  });

  page.onInput = function (name, value) {
    console.debug("input", name, value);
    if (name == "nickname") {
      mynickname = value;
      liveSend({ type: "join", nickname: mynickname });
      return;
    }

    if (name == "text") {
      if (recipient != undefined ) {
        liveSend({ type: "wisper", text: value, dest: recipient });
        addMessage('wisper', value, mynickname, recipient);
      } else {
        liveSend({ type: "say", text: value });
      }
      resetInput();
      return;
    }

    if (name == "action" && value == "clear") {
      recipinent = null;
      page.emitReset(['text', 'recipient']);
      return;
    }

    if (name == "action" && value == "send") {
      page.submitInputs('text');
      return;
    }

    if (name == "action" && value == "leave") {
      page.submit();
      return;
    }

    if (name == 'recipient') {
      recipient = party[value];
      page.emitUpdate({ recipient: recipient });
      return;
    }
  };

  page.emitUpdate({ phase: "joining" });
}
