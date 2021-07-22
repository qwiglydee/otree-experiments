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
- `trial_delay`: a delay between trials
- `allow_skip`: allow user to skip a trial without giving an answer
- `force_solve`: do not advance to next trial until current puzzle is correctly solved


## Development

0. clone this repo into some working directory
   ```bash
   git clone ...
   cd ...
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
3. run the server
   ```bash
   otree devserver
   ```

## Development with PyCharm

0. Clone this repo into some working directory
1. Start Pycharm and open project from the working directory
2. Run "Add python interpreter" from popup, or from Settings/Project/Python interpreter
   - Location := WORKINGDIR/.venv  or somewhere else
3. Open files `requirements.txt` and `requirements.devel.txt` and invoke "install requirements" from top popup line
4. Setup Debugger:
   - Menu Run/Edit Configurations
   - Add new, "Python"
   - Working directory: the working directory
   - Script path := .vent/bin/otree
   - Parameters := devserver_inner
6. To run/debug devserver with Shift-F10 or Shift-F9
   - autoreloading on files changes won't work, press Ctrl-5 to reload manually
   - breakpoints will work, including live pages code
   

## Using in your project

TODO
