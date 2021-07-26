import time
from otree.api import expect, Bot
from . import *


TRIAL_DELAY = 0.01


class PlayerBot(Bot):
    def play_round(self):
        self.session.config['trial_delay'] = TRIAL_DELAY

        yield Game

        trials = Trial.filter(player=self.player)
        expect(len(trials), 5)

        expect(self.player.total, 5)
        expect(self.player.correct, 2)
        expect(self.player.incorrect, 3)


def call_live_method(method, group: Group, **kwargs):
    player = group.get_players()[0]

    last = None
    stats = {}

    def forward():
        time.sleep(TRIAL_DELAY)
        method(1, {'next': True})
        _trial = get_last_trial(player)
        if last:
            expect(_trial.timestamp, ">", last.timestamp)
            expect(_trial.iteration, ">", last.iteration)
        return _trial

    def answer(ans, correct):
        _response = method(1, {'answer': ans})[1]
        _feedback = _response['feedback']
        _stats = _response['stats']
        _trial = get_last_trial(player)
        expect(_trial.answer, ans)
        expect(_feedback, correct)
        expect(_trial.is_correct, correct)
        return _trial, _feedback, _stats

    # 2 correct answers
    for i in range(2):
        trial = forward()
        trial, feeback, stats = answer(trial.solution, True)
        last = trial

    expect(
        stats,
        {'total': 2, 'answered': 2, 'unanswered': 0, 'correct': 2, 'incorrect': 0},
    )

    # 3 incorrect answers
    for i in range(3):
        trial = forward()
        trial, feedback, stats = answer("0", False)
        last = trial

    expect(
        stats,
        {'total': 5, 'answered': 5, 'unanswered': 0, 'correct': 2, 'incorrect': 3},
    )
