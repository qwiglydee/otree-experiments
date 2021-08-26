# oTree apps

Some experimental implementation of games for oTree v5

- `generic`: base code
- `real_effort`: some real effort tasks
- `sliders`: the sliders task
- `iat`: implicit association test
- `ldt_choice`: lexical decision task with word/nonword responses
- `ldt_gonogo`: lexical decision task with go/nogo

## Genric code

The code implements generic stimulus/response app with many useful features.
It is intended to be used as base code to develop other apps with some particular design.

Features:
- loading stimuli from csv file
- selecting stimuli by category for a session
- pregenerating random non-repeating sequence of trials
- running the experiment on real-time live page
- displaying stimuli as plain text, static images or images generated on the go
- configurable keymap for any number of keys/responses
- configurable go/no-go scheme
- basic touch screen support
- recording all trials and responses
- recording reaction time
- custom export of all the data

Anti-cheating and anti-scripting protection: 
- all trials generated on server
- not revealing any important data in browser
- responses are validated on server
- data and timing violations are checked

Generic configuration params:
- app constants:
  - `choices`: set of responses, independent from keys or selected stimuli categories
  - `keymap`: mapping of keys to responses
  - `timeout_response`: response for no-go timeout
- session config:
  - `categories`: mapping of response choices to categories in stimuli pool 
  - `labels`: text labels for choices to show in page instructions
  - `num_iterations`: number of trials (stimuli) to show in a single session/round
  - `attempts_per_trial`: number of response attempts allowed
- timing parameters in session config, all in ms
  - `focus_display_time`: time to display attention focus cross
  - `stimulus_display_time`: time to display stimulus, `0` to do not hide it
  - `feedback_display_time`: time to display given response and feedback
  - `auto_response_time`: timeout of autoresponse for no-go option, `0` to disable
  - `input_freezing_time`: time to block all inputs after response, to prevent rage typing
  - `inter_trial_time`: time after response is given before next trial starts (including post-response feedback display time) 
 
 Note: the inter-trial time is affected by network latency and extended by time of transfering data from server and loading an image.
 However, the latency does not affect display timing of measuring reaction time.
 
 The generic implemented trial scheme is:
 - load trial from server and wait until all images are loaded
 - display focus cross for some configured time
 - display stimulus
 - wait for response
 - hide stimulus after some configured time, while still waiting for response
 - auto submit a timeout response after some configured time
 - wait for some time and advance for next trial
 
 The reaction time is measured since the moment when stimuli get actually displayed on screen and until a response is given.
 It is not affected by network latency but might be affected by some other processes running in the same browser or other applications running on the same device.


## Real-effort tasks

Games:
- `transcription`: transcribing of distorted text from image
- `matrices`: counting symbols in matrix
- `decoding`: decoding a letters/numbers cipher 
- `sliders`: moving sliders task

The task units are referenced as 'puzzles' in docs and code.

All games are impemented as single-user, single page apps.

Common features:
- live page with infinite iterations (micro-rounds) and timeout
- generating randomized puzzle on the fly
- creating images for each puzzle on the fly
- showing the images on the live page
- recording outcome of each puzzle in database
- custom export of all recorded data

Anti-cheating and anti-scripting protection:
- the puzzles are generated as images, no solution data is even revealed into browser
- validation of answers on server side
- `puzzle_delay`: minimal delay between iterations
- `retry_delay`: minimal delay before next retry after wrong answer 

Configurable features, via session config:
- `attempts_per_puzzle`: number of attempts allowed to solve puzzle 
- `max_iterations`: complete round after given number of iterations.
  (if timeout is also specified for a page, round is terminated by whichever comes first.)
  
For sliders:
- `num_sliders`: total number of sliders
- `num_columns`: number of columns in grid

More detailed adjustments are available via variables in files `task_something.py`

## Implicit Association Test

Features:
- customizable categories and stimuli
- using either words or images, or mix of them
- specifying stimuli in code or loading from csv file
- calculating d-score (in pure python) 
- some server-side anti-cheating and anti-script-kiddies protection

Configurable parameters (in session config):
- `primary: [left_primary, right_primary]` -- primary (top, concepts) categories,   
- `secondary: [left_secondary, right_secondary]` -- primary (top, concepts) categories
- `primary_images=True` or `secondary_images=True` -- use values as references to images instead of words  
- `num_iterations={1: int, 2: int, 3: int, 4: int, 5: int, 6: int, 7: int}` -- number of iterations for each round

# Development 

## command-line

0. download/unzip content of this repo into some working directory, or clone it using git 
   ```bash
   git clone https://github.com/qwiglydee/otree-experiments/
   cd otree-experiments
   ```
1. create and activate virtualenv in working directory
   ```bash
   python -m venv .venv
   source .venv.bin/activate
   pip install --upgrade pip
   ```
2. install requirements
   ```bash
   pip install -r requirements.txt
   pip install -r requirements.devel.txt
   ```
3. run the development server
   ```bash
   otree devserver
   ```
4. open browser at `http://localhost:8000/`

## PyCharm

0. download/unzip content of this repo into some working directory, or clone it using git 
1. Start Pycharm and open project from the working directory
2. Create virtual environment
   - Open Settings / Project: otree-experiments / Python interpreter
   - Open "⚙" / "Add..."
   - Select "Virtual environment"
   - Select "New environment"
   - Set Location := WORKINGDIR/.venv  or somewhere else
3. Install requirements
   - Open internal terminal from the very bottom
   - Make sure it displays "venv" in prompt
   - run pip 
     ```bash
      pip install -r requirements.txt
      pip install -r requirements.devel.txt
     ```
5. Setup Debugger:
   - Menu / Run / Edit Configurations / Add new
   - Select "Python"
   - Set Working directory
   - Set Script path := .venv/bin/otree  or a full path to venv otree
   - Parameters := devserver_inner
6. To run and debug devserver with Shift-F10 or Shift-F9
   - autoreloading on files changes won't work, press Ctrl-5 to reload manually
   - breakpoints will work, including code of `live_method`

# Customization

## RET

> TODO

## IAT

### Creating custom stimuli

Edit file `stimuli.py` and modify variable `DICT` to add categories and words, similar to what already exists.
The categories in dictionary are unpaired. You specify pairs in session config.

Category names can have prefixes like `english:family`, `spanish:familia`, `words:positive`, `emojis:positive`. 
The prefixes are stripped when displayed on pages in instructions or results.

### Loading stimuli from csv file

Put file `stimuli.csv` into the app directory. 
The file should contain first row for headers and at least 2 columns: `category`, `stimulus`.

Content of the file will be loaded into `DICT` at server startup/reload. 

### Using images

Put all you images into folder `static/images` within the app directory.

List filenames of the images in dictionary or csv file, just like words.

In initial setup images are expected to be about 240px height. 
Make sure your images are not too huge and wont consume too much traffic. 

### Adjusting styles and appearence

All the appearence is defined in file `static/iat.css`. 
Edit the file to change colors or sizes of category labels or stimuli.

Stimulus is marked as `.stimulus`, category labels in corners as `.category`.  

To style primary and secondary differently, change blocks referencing `.primary` and `.secondary`.

### Changing rounds' setup

Layouts for each round are given in file `blocks.py` variable `BLOCKS`,
which is set to `= BLOCKS1` initially.

There are two predefined setups: `BLOCKS1` and `BLOCKS2`. 
The first one is for classic setup, when primary category switches in last 3 rounds, and secondary remains in place.  
The second one is for alternative setup, when primary category stays, and secondary switches.
