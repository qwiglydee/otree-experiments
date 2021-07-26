import time
from contextlib import contextmanager
from otree.bots import Bot, expect
from otree.bots.bot import ExpectError
from . import *


TRIAL_DELAY = 0.1
RETRY_DELAY = 0.2


class PlayerBot(Bot):
    def play_round(self):
        conf = self.player.session.config
        force_solve = conf.get('force_solve', False)

        yield Game

        trials = Trial.filter(player=self.player)

        if force_solve:
            expect(len(trials), 3)
            expect(self.player.total, 3)
            expect(self.player.correct, 3)
            expect(self.player.incorrect, 0)
        else:
            expect(len(trials), 5)
            expect(self.player.total, 5)
            expect(self.player.correct, 2)
            expect(self.player.incorrect, 3)


@contextmanager
def expect_failure(*exceptions):
    try:
        yield
    except exceptions:
        return
    except Exception as e:
        raise ExpectError(
            f"A piece of code was expected to fail with {exceptions} but it failed with {e.__class__}"
        )
    raise ExpectError(
        f"A piece of code was expected to fail with {exceptions} but it didn't"
    )


def call_live_method(method, group: Group, **kwargs):
    player = group.get_players()[0]
    conf = player.session.config
    # patch session to speed up tests
    conf['trial_delay'] = TRIAL_DELAY
    conf['retry_delay'] = RETRY_DELAY

    force_solve = conf.get('force_solve', False)

    last = None
    response = {}

    def move_forward():
        _response = method(1, {'next': True})[1]
        return _response, get_last_trial(player)

    def expect_forwarded(_trial, _response):
        if last:
            expect(_trial.timestamp, ">", last.timestamp)
            expect(_trial.iteration, ">", last.iteration)
        expect('image', 'in', _response)

    def give_answer(ans):
        _response = method(1, {'answer': ans})[1]
        return _response, get_last_trial(player)

    def expect_answered(_trial, _response, ans, valid):
        expect(_trial.answer, ans)
        expect(_trial.is_correct, valid)
        expect(_response['feedback'], valid)

    # 2 correct answers
    for i in range(2):
        time.sleep(TRIAL_DELAY)
        response, trial = move_forward()
        expect_forwarded(trial, response)

        answer = trial.solution
        response, trial = give_answer(answer)
        expect_answered(trial, response, answer, True)

        last = get_last_trial(player)

    expect(
        response['stats'],
        {'total': 2, 'answered': 2, 'unanswered': 0, 'correct': 2, 'incorrect': 0},
    )

    if force_solve:
        time.sleep(TRIAL_DELAY)
        response, trial = move_forward()
        expect_forwarded(trial, response)

        # give incorrect answer
        answer1 = "0"
        response, trial = give_answer(answer1)
        expect_answered(trial, response, answer1, False)

        # try to skip
        with expect_failure(RuntimeError):
            time.sleep(TRIAL_DELAY)
            move_forward()

        # should stay with same trial
        expect(get_last_trial(player), trial)

        # retry w/out waiting
        answer2 = trial.solution
        with expect_failure(RuntimeError):
            response, trial = give_answer(answer2)

        # trial stays with old answer
        expect_answered(trial, response, answer1, False)

        # retry with waiting
        answer3 = trial.solution
        time.sleep(RETRY_DELAY)
        response, trial = give_answer(answer3)

        expect_answered(trial, response, answer3, True)

        expect(trial.retries, 2)  # 1st and 3rd

        expect(
            response['stats'],
            {'total': 3, 'answered': 3, 'unanswered': 0, 'correct': 3, 'incorrect': 0},
        )
    else:
        # give 3 incorrect answers
        for i in range(3):
            time.sleep(TRIAL_DELAY)
            response, trial = move_forward()
            expect_forwarded(trial, response)

            # give incorrect answer
            answer = "0"
            response, trial = give_answer(answer)
            expect_answered(trial, response, answer, False)

            last = get_last_trial(player)
        expect(
            response['stats'],
            {'total': 5, 'answered': 5, 'unanswered': 0, 'correct': 2, 'incorrect': 3},
        )
