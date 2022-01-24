# Live API

Draft

## Types of live games

### Trials

Simple trials like repeated stimulus/response or question/answer tasks.

- page requests new trial
- server sends initial progress, including current iteration
- server generates or retrieves a trial and sends it to the page
- page sends user input (a response or an answer)
- server checks the input and sends feedback, indicating if that's correct/incorrect 
- server sends status indicating if current trial is completed/solved/failed
- server sends updated progress indicating changing iteration or number of retries left, etc
- if there're more retries left, the scenario repeats sending more inputs
- if there're more iterations to go, the whole scenario repeats

### Puzzles

More complicated games involving several small actions to construct solution.

Two possible scenarios:

Full live:
- page requests new puzzle
- server sends puzzle data 
- page sends user action
- server validates action and sends feedback
- server assembles solution on it's side 
- server sends status indicating if the puzzle is completed/solved/failed  
- if not, page repeats sending actions

Alternative:
- page requests new puzzle
- server sends puzzle data 
- page handles all actions itself until solution is assembled or confirmed
- page sends the solution
- server validates and checks the soluton and sends feedback
- server sends status indicating if the puzzle is completed/solved/failed  
- if more retries left the scenario repeats sending solutions

The scenarios can also be iterative, just like trials. In the case, a progress message appears after puzzle data and status 

### Sequential multiplayer

A game involving two or more players that perform actions in turn.

- server initializes game when all players arrive 
- pages of each player requests game
- server sends initial game state
- server broadcasts status, indicating active player
- page of active player sends user action
- server checks the action and sends feedback
- server updates game state and broadcasts update 
- server broadcasts new status indicating if the game is over and who's winner or new active player
- if game is not over, it repeats sending actions   

### Concurrent multiplayer

A game involving two or more players that perform actions at any time.

- server initializes game when all players arrive 
- page of each player requests game
- server sends initial game state 
- page of any player sends user action
- server checks the action and sends feedback
- server updates game state and broadcasts update 
- server broadcasts new status indicating if the game is over and who's winner
- if game is not over, it repeats sending actions


### Emergency page reload scenario

- page reloads and requests game restoring
- server sends full game data, status, progress 


## Message structure

Messages contain fields `type` to indicate type of a message, and some data fields specific to the type
Several messages are combined into a list to send together.


### Requesting new trial

- `type` = 'load'
- no data

### Reponding with a trial data

- `type` = 'trial'
- whatever data is needed for a game

### Sending user input

Any player's action or response, including timeout event, which may count as a response (e.g. go/nogo games) or just failure.

- `type` = 'input'
- `input`: user input, e.g. an response to trial
  - `move`: single action for a puzzle
  - `solution`: whole sequence of actions to solve puzzle  
- `reaction_time`: reaction time
- `timeout`: boolean indicating that timeout happen w/out any input 

### Sending feedback

Server feedback for a user input that is a subject of assesment correct/incorrect, or needs some normalization (converting case, substituting no-go option, etc) 

- `type` = 'feedback'
- `input`: the corresponding original input, normalized
- `correct`: boolean indicating the answer/solution is correct   
- `error`: if present, indicates the input is wrong (a player fail)
  - `code`: a string code of an error to use in program code
  - `message`: a human readable string to display
- `final`: indicates no more responses on the trial allowed  


### Sending game updates

An update of game state from server, as a consequence of some player actions.
Send to the same single user or to all users. 

- `type` = 'update'
- `changes`: a dict indicating changin variables or subvariables, in form of { 'some.dot.path': value, ... }


### Sending game status

- `type`: 'status'
- `trial_completed`: indicates that current trial is completed
- `trial_succesful`: indicated if the trial is solved/failed
- `game_over`: indicates that the whole iteration loop is over
- `current_player`: indicates id of a current player in sequential multiplayer gam
- `winner_player`: indicates who win the game if it is over 


### Sending progress

Server sends status of the iterating progress

- `type` = 'progress'
- `total`: total/maximal number of iterations
- `current`: current iteration
- `completed`: number of completed trials
- `solved`: number of succesfully completed trials
- `failed`: number of unsuccesfully completed iterations
- `retries`: number of retries for current trial

### Requesting game restore

- `type` = 'reload'
-  no data


## back-end API 

Module `live_utils` contains functions to construct live_method for the page from user-provided functions.
The constructed method takes care about dispatching events and performs some common checks and errors. 

Usage:
```python
class GamePAge(Page):
  live_method = live_utils.live_trials(get_current_trial, on_load, on_input)
```

- `live_trials(get_current_trial, encode_trial, on_restore, on_load, on_input)`: for trials
- `live_puzzle(get_current_puzzle, encode_puzzle, on_restore, on_load, on_input)`: for puzzles, both scenarios
- `live_multiuser(get_current_game, encode_game, on_restore, on_load, on_input)`: for all multiplayer games

The `get_current_trial(player)` and others should return a model instance corresponding to current game state or None if its not yet created

The `encode_something(trial)` should return a dict containing the data needed by page to handle game

The `on_load(player)` should generate or retrieve pregenerated trial instance

The `on_input(trial, input, reaction_time, timeout_happened)` a handler for messages of type `input` with single input. It should update all the data and ake all necessary checks.


The handlers returns a dictionary with keys corresponding to messages to send back.
- `trial`: the trial instance
- `status`: the status fields
- `feedback`: the feedback fields
- `update`: dict of changes
- `progress`: the progress data


## front-end API

Module `otree-front-live.js` receives all the messages and pass them to corresponding handlers defined on the global `otree.game` instance.
The arg of the handlers is content of the message, or a value of the only field ('trial', 'changes')  

- `game.onLiveTrial(trial)`: when new trial arrived from server
- `game.onLiveStatus(status)`
- `game.onLiveFeedback(feedback)` 
- `game.onLiveUpdate(changes)`: the changes, ready to use as `game.updateState(changes)`
- `game.onLiveProgress(progress)`

Sending message to server is as usual, via `liveSend({ type: "...", ... })` 
