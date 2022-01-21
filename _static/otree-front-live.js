function liveRecv(data) {
  console.debug("liveRecv", data);

  if (!Array.isArray(data)) {
    data = [data];
  }

  let game = window.game;

  data.forEach(message => {
    console.debug("liveMessage", message);
    switch(message.type) {
      case 'trial':
        game.onLiveTrial(message);
        break;
      case 'feedback':
        game.onLiveFeedback(message);
        break;
      case 'update':
        game.onLiveUpdate(message.changes);
        break;
      case 'status':
        game.onLiveStatus(message);
        break;
      case 'progress':
        game.onLiveProgress(message);
      } 
  });
}