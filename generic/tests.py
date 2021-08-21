import time
import random
from contextlib import contextmanager

from otree.api import *
from otree import settings

from . import Constants, Player, Trial, Intro, Main, Results


class PlayerBot(Bot):
    cases = [
        "normal",
    ]

    def play_round(self):
        print(f"Playing test case: {self.case}")
        method_name = f"play_{self.case}"
        method = getattr(self, method_name, self.play_default)
        yield from method()

    def play_default(self):  # noqa
        yield Submission(Intro, check_html=False)
        yield Submission(Main, check_html=False)
        yield Submission(Results, check_html=False)

    def play_normal(self):
        yield Submission(Intro, check_html=False)
        yield Submission(Main, check_html=False)
        yield Submission(Results, check_html=False)

        player = self.player
        num_correct = len(Trial.filter(player=player, is_correct=True))
        num_incorrect = len(Trial.filter(player=player, is_correct=False))
        num_total = num_correct + num_incorrect

        expect(player.num_trials, num_total)
        expect(player.num_solved, num_correct)
        expect(player.num_failed, num_incorrect)

        generated = [t.stimulus for t in Trial.filter(player=player)]
        uniq = set(generated)
        expect(len(generated), len(uniq))


def call_live_method(method, group, case, **kwargs):  # noqa
    print(f"Playing live case: {case}")

    try:
        test = globals()[f"live_test_{case}"]
    except KeyError:
        raise NotImplementedError(f"Test case {case} not implemented")

    test(method, group.get_players()[0], group.session.params)


# utils


def get_trial(p):
    puzzles = Trial.filter(player=p, iteration=p.iteration)
    return puzzles[0] if len(puzzles) == 1 else None


def get_correct_response(z):
    return z.solution


def get_incorrect_response(z):
    return random.choice([c for c in Constants.choices if c != z.solution])


def send(m, p, tp, **values):
    data = {'type': tp}
    data.update(values)
    return m(p.id_in_group, data)[p.id_in_group]


def expect_response(r, tp, **fields):
    expect(r['type'], tp)
    for f, v in fields.items():
        expect(r[f], v)


def live_test_normal(method, player, conf):  # noqa
    m = method
    p = player

    resp = send(m, p, 'load')
    expect_response(resp, 'status')

    for i in range(conf['num_iterations']):
        resp = send(m, p, 'new')
        expect_response(resp, 'trial')

        z = get_trial(p)

        give_correct = i % 2 == 0

        if give_correct:
            response = get_correct_response(z)
        else:
            response = get_incorrect_response(z)
        resp = send(m, p, 'response', response=response, reaction=1.0)
        expect_response(resp, 'feedback', is_correct=give_correct)

        time.sleep(conf['trial_pause'])

    resp = send(m, p, 'new')
    expect_response(resp, 'status', game_over=True)
