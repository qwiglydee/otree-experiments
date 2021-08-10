# oTree experiments

Some experimental implementation of games for oTree v5

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


## Development with command-line

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

## Development with PyCharm

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
   - ```bash
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
