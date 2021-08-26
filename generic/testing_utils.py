from contextlib import contextmanager
import time
import random

from otree.api import expect


def sleep(time_ms):
    time.sleep(time_ms / 1000)


def get_trial(Trial, p):  # noqa
    puzzles = Trial.filter(player=p, iteration=p.iteration)
    assert len(puzzles) <= 1
    return puzzles[0] if len(puzzles) == 1 else None


def get_correct_response(z):
    return z.solution


def get_incorrect_response(z, choices):
    return random.choice([c for c in choices if c != z.solution])


def send(m, p, tp, **values):
    data = {'type': tp}
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


def expect_response(r, tp, **fields):
    expect(r['type'], tp)
    for f, v in fields.items():
        expect(r[f], v)


def expect_fields(data, **expected):
    actual = {k: data[k] for k in expected.keys()}
    expect(actual, expected)


def expect_attrs(obj, **expected):
    actual = {k: getattr(obj, k) for k in expected.keys()}
    expect(actual, expected)


def expect_new(trial, last):
    expect(trial.id, '!=', last.id)
    expect(trial.iteration, last.iteration + 1)
    expect(trial.server_loaded_timestamp, '>', last.server_loaded_timestamp)


def expect_answered(z, response):
    expect(z.server_response_timestamp, '>', 0)
    expect(z.response, response)
    expect(z.reaction_time, '>', 0)
    expect(z.is_correct, 'in', (True, False))
