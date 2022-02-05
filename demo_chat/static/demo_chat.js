// the default handler generates 'ot.live.*' events
liveRecv = otree.live_utils.liveDefaultRecv;

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
    chat = chat.slice(-maxlog); // cut down because number of lines is fixed
    page.update({ chat: chat });
  }

  function resetInput() {
    recipient = undefined;
    page.reset(["text", "recipient"]);
  }

  //// events from liveRecv

  page.onEvent("ot.live.joined", function (event, data) {
    console.debug("joined", data);
    loadParty(data.party);
    addMessage("system", `Welcome, ${data.newcomer}!`);
  });

  page.onEvent("ot.live.left", function (event, data) {
    console.debug("left", data);
    loadParty(data.party);
    addMessage("system", `Bye, ${data.nickname}!`);
  });

  page.onEvent("ot.live.talk", function (event, data) {
    console.debug("talk", data);
    addMessage("talk", data.text, data.source);
  });

  page.onEvent("ot.live.wisper", function (event, data) {
    console.debug("wisper", data);
    addMessage("wisper", data.text, data.source, mynickname);
  });

  //// events from buttons

  page.onEvent("chat.join", function () {
    page.submitInputs('nickname');
  });

  page.onEvent("chat.clear", function () {
    recipinent = null;
    page.reset(["text", "recipient"]);
  });

  page.onEvent("chat.send", function () {
    page.submitInputs("text");
  });

  page.onEvent("chat.leave", function () {
    liveSend({ type: "leave" });
    page.update({ stage: "leaving" });
    otree.utils.timers.delay(() => page.submit(), 3000);
  });

  //// events from inputs

  page.onEvent("ot.input", function (event, data) {
    let { name, value } = data;
    console.debug("input", name, value);

    if (name == "nickname") {
      mynickname = value;
      liveSend({ type: "join", nickname: mynickname });
      page.update({ stage: "chatting" });
    }

    if (name == "text") {
      if (recipient != undefined) {
        liveSend({ type: "wispering", text: value, dest: recipient });
        addMessage("wisper", value, mynickname, recipient);
      } else {
        liveSend({ type: "saying", text: value });
      }
      resetInput();
    }

    if (name == "recipient") {
      recipient = party[value];
      page.update({ recipient: recipient });
    }
  });

  //// main start

  page.update({ stage: "joining" });
}
