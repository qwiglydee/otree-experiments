import time
import random
import json
from contextlib import contextmanager

from otree.api import *
from otree import settings

from . import Player, Puzzle, Slider,  Game
from .task_sliders import snap_value, SLIDER_SNAP


class PlayerBot(Bot):
    cases = [
        "normal",
        "normal_timeout",
        "dropout_timeout",
        "snapping",
        "reloading",
        "submitting_null",
        "submitting_empty",
        "submitting_none",
        "submitting_blank",
        "submitting_premature",
        "submitting_toofast",
        "submitting_toomany",
        "skipping",
        "cheat_debug",
        "cheat_nodebug",
    ]

    def play_round(self):
        if self.case == 'iter_limit' and not self.session.params['max_iterations']:
            print(f"Skipping case {self.case} under no max_iterations")
            return

        make_timeout = 'timeout' in self.case
        yield Submission(Game, check_html=False, timeout_happened=make_timeout)


# utils

# `m` stands for method
# `p` for player
# `z` for puzzle
# `r` for response


def get_last_puzzle(p) -> Puzzle:
    puzzles = Puzzle.filter(player=p, iteration=p.iteration)
    puzzle = puzzles[-1] if len(puzzles) else None
    return puzzle


def get_slider(z, i):
    return Slider.filter(puzzle=z, idx=i)[0]


def get_value(z, i):
    slider = get_slider(z, i)
    return slider.value


def get_target(z, i):
    slider = Slider.filter(puzzle=z, idx=i)[0]
    return slider.target


def get_progress(p):
    return {
        "total": len(Puzzle.filter(player=p)),
    }


def send(m, p, t, **values):
    data = {'type': t}
    data.update(values)
    return m(p.id_in_group, data)[p.id_in_group]


@contextmanager
def expect_failure(*exceptions):
    try:
        yield
    except exceptions:
        return
    except Exception as e:
        raise AssertionError(
            f"A piece of code was expected to fail with {exceptions} but it failed with {e.__class__}"
        )
    raise AssertionError(
        f"A piece of code was expected to fail with {exceptions} but it didn't"
    )


def expect_progress(p, **values):
    progress = get_progress(p)
    expect(progress, values)


def expect_puzzle(z, **values):
    expect(z, '!=', None)
    for k, v in values.items():
        expect(getattr(z, k), v)


def expect_slider(z, i, expected):
    value = get_value(z, i)
    expect(value, expected)


def expect_response(r, t, **values):
    expect(r['type'], t)
    for k, v in values.items():
        expect(k, 'in', r)
        expect(r[k], v)


def expect_response_progress(r, **values):
    expect('progress', 'in', r)
    p = r['progress']
    for k, v in values.items():
        expect(k, 'in', p)
        expect(p[k], v)


# test case dispatching


def call_live_method(method, group, case, **kwargs):  # noqa
    print(f"Testing case '{case}'")

    try:
        test = globals()[f"live_test_{case}"]
    except KeyError:
        raise NotImplementedError("Test case not implemented", case)

    test(method, group.get_players()[0], group.session.params)


# test cases


def live_test_normal(method, player, conf):
    num_sliders = conf['num_sliders']
    retry_delay = conf['retry_delay']

    send(method, player, 'load')
    send(method, player, 'new')

    puzzle = get_last_puzzle(player)

    for i in range(num_sliders):
        last = (i == num_sliders-1)
        target = get_target(puzzle, i)
        # 1st attempt - incorrect
        value = target + SLIDER_SNAP * 2
        resp = send(method, player, 'value', slider=i, value=value)
        expect_puzzle(puzzle, iteration=1, num_correct=i, is_solved=False)
        expect_slider(puzzle, i, value)
        expect_response(resp, 'feedback', slider=i, value=value, is_correct=False, is_completed=False)

        time.sleep(retry_delay)

        # 2nd attempt - correct
        value = target
        resp = send(method, player, 'value', slider=i, value=value)
        expect_puzzle(puzzle, iteration=1, num_correct=i+1, is_solved=last)
        expect_slider(puzzle, i, value)
        expect_response(resp, 'feedback', slider=i, value=value, is_correct=True, is_completed=last)

        time.sleep(retry_delay)


def live_test_normal_timeout(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')
    send(method, player, 'value', slider=0, value=100)


def live_test_dropout_timeout(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')


def live_test_snapping(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')

    puzzle = get_last_puzzle(player)

    solution0 = get_target(puzzle, 0)
    value = solution0 + 100
    snapped = snap_value(value, solution0)
    send(method, player, 'value', slider=0, value=value)
    expect_slider(puzzle, 0, snapped)


def live_test_reloading(method, player, conf):
    # start of the game
    resp = send(method, player, 'load')

    expect(get_last_puzzle(player), None)
    expect_response(resp, 'status')
    expect_response_progress(resp, iteration=0)

    resp = send(method, player, 'new')
    puzzle = get_last_puzzle(player)
    expect_puzzle(puzzle, iteration=1, num_correct=0)
    expect_response(resp, 'puzzle')
    expect_response_progress(resp, iteration=1)

    # 1 answer
    target = get_target(puzzle, 0)
    send(method, player, 'value', slider=0, value=target)
    expect_puzzle(puzzle, iteration=1, num_correct=1)
    expect_slider(puzzle, 0, target)

    # midgame reload
    resp = send(method, player, 'load')
    expect_response(resp, 'status')
    expect_response_progress(resp, iteration=1)

    puzzle = get_last_puzzle(player)
    expect_puzzle(puzzle, iteration=1, num_correct=1)
    expect_slider(puzzle, 0, target)


def live_test_submitting_null(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')

    with expect_failure(TypeError):
        method(player.id_in_group, None)

    expect_puzzle(get_last_puzzle(player), iteration=1, num_correct=0, is_solved=False)


def live_test_submitting_empty(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')

    with expect_failure(KeyError):
        method(player.id_in_group, {})

    expect_puzzle(get_last_puzzle(player), iteration=1, num_correct=0, is_solved=False)


def live_test_submitting_none(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')

    with expect_failure(KeyError):
        send(method, player, 'value')

    expect_puzzle(get_last_puzzle(player), iteration=1, num_correct=0, is_solved=False)


def live_test_submitting_blank(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')

    with expect_failure(ValueError):
        send(method, player, 'value', slider=0, value="")

    expect_puzzle(get_last_puzzle(player), iteration=1, num_correct=0, is_solved=False)


def live_test_submitting_premature(method, player, conf):
    send(method, player, 'load')

    with expect_failure(RuntimeError):
        send(method, player, 'value', slider=0, value=100)


def live_test_submitting_toomany(method, player, conf):
    retry_delay = conf['retry_delay']

    send(method, player, 'load')
    send(method, player, 'new')

    puzzle = get_last_puzzle(player)
    target = get_target(puzzle, 0)

    v1 = snap_value(100, target)
    v2 = snap_value(50, target)

    for _ in range(conf['attempts_per_slider']):
        resp = send(method, player, 'value', slider=0, value=v1)
        expect_response(resp, 'feedback')
        expect_slider(puzzle, 0, v1)
        time.sleep(retry_delay)

    with expect_failure(RuntimeError):
        send(method, player, 'value', slider=0, value=v2)

    expect_slider(puzzle, 0, v1)


def live_test_submitting_toofast(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')

    puzzle = get_last_puzzle(player)
    target = get_target(puzzle, 0)

    v1 = snap_value(100, target)
    v2 = snap_value(50, target)

    resp = send(method, player, 'value', slider=0, value=v1)
    expect_response(resp, 'feedback')
    expect_slider(puzzle, 0, v1)

    with expect_failure(RuntimeError):
        send(method, player, 'value', slider=0, value=v2)

    expect_slider(puzzle, 0, v1)


def live_test_skipping(method, player, conf):
    send(method, player, 'load')
    send(method, player, 'new')

    with expect_failure(RuntimeError):
        send(method, player, 'new')

    expect_puzzle(get_last_puzzle(player), iteration=1, num_correct=0, is_solved=False)


def live_test_cheat_debug(method, player, conf):
    settings.DEBUG = True
    send(method, player, 'load')
    send(method, player, 'new')

    resp = send(method, player, 'cheat')
    expect_response(resp, 'solution')


def live_test_cheat_nodebug(method, player, conf):
    settings.DEBUG = False
    send(method, player, 'load')
    send(method, player, 'new')

    with expect_failure(RuntimeError):
        send(method, player, 'cheat')
