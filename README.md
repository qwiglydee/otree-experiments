# oTree experiments

Some experimental implementation of games for oTree v5

Features:
- live page with infinite iterations (micro-rounds) and timeout
- generating each puzzle on the fly
- showing a puzzle as an image on the live page
- recording each iteration, elapsed time, puzzle, solution, given answer, correctness, and if the puzzle was skipped
- custom export of all recorded data

Puzzle types implemented:
- `captcha`: classic distorted text (configurable characters and length)
- `matrices`: matrices of 0 and 1 (configurable symbols and size)
- `symmatrices`: version of matrices with special symbols


## Development

0. clone this repo into working directory
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

## Integration into your code

TODO
