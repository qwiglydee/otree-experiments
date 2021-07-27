# oTree experiments

Some experimental implementation of games for oTree v5

Games:
- `captcha`: classic distorted text (configurable characters and length)
- `arithmetics`: solving equations in form of "A + B ="
- `matrices`: matrices of 0 and 1 (configurable symbols and size)
- `symmatrices`: version of matrices with special symbols
- `colors`: random color names rendered in random color

The task units are referenced as 'puzzles' in docs and code.

Common features:
- live page with infinite iterations (micro-rounds) and timeout
- generating randomized puzzle on the fly
- creating images for each puzzle on the fly
- showing the images on the live page
- recording outcome of each trial in database
- custom export of all recorded data
- some server-side anti-cheating and anti-script-kiddies protection

Configurable features, via session config:
- `allow_skip`: allow user to skip a puzzle without giving an answer
- `force_solve`: do not advance to next puzzle until current one isn't solved
- `num_iterations`: complete round after given number of iterations 

Anti-cheating parameters:
- `trial_delay`: minimal delay between iterations
- `retry_delay`: minimal delay before next retry after wrong answer 


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
