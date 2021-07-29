import time
from contextlib import contextmanager
from otree.api import *
from importlib import import_module

# NB: some operations on sqlite may be slow

TEST_CASES = [
    # normal flow
    'normal',  # solving 2 puzzles in normal sequence
    'replying_correct',  # giving a correct answer
    'replying_incorrect',  # giving an incorrect answer
    # violations
    'messaging_bogus',  # sending bogus message
    'replying_null',  # giving null as an answer
    'replying_empty',  # giving empty string as an answer
    'replying_premature',  # giving reply without current puzzle
    'forward_premature',  # advancing without current puzzle
    'forward_nodelay',  # advancing to a next puzzle w/out delay
    'reloading',  # page reload in the middle of round
    # optional features
    'skipping_unanswered',  # advancing to a next puzzle w/out replying
    'skipping_incorrect',  # advancing to a next puzzle after incorrect answer
    'retrying_correct',  # answering to the same puzzle correctly after incorrect answer
    'retrying_incorrect',  # answering the same puzzle incorrectly after correct answer, for no reason
    'retrying_nodelay',  # retrying w/out delay
    'iter_limit',  # reaching maximum number of iterations
]

# TEST_CASES = ['iter_limit']


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


def get_trial_class(player):
    app_module = import_module(type(player).__module__)
    return app_module.Trial


def end_game_assertions(player):
    Trial = get_trial_class(player)

    expect(player.total, len(Trial.filter(player=player, round=0)))
    expect(player.correct, len(Trial.filter(player=player, round=0, is_correct=True)))
    expect(
        player.incorrect, len(Trial.filter(player=player, round=0, is_correct=False))
    )


def call_live_method(method, group, case, **kwargs):
    conf = group.session.config
    trial_delay = conf.get('trial_delay')
    retry_delay = conf.get('retry_delay')
    allow_skip = conf.get('allow_skip', False)
    force_solve = conf.get('force_solve', False)
    allow_retry = conf.get('allow_retry', False) or force_solve
    max_iter = conf.get('num_iterations')

    player = group.get_players()[0]
    Trial = get_trial_class(player)

    print(
        f"Testing case '{case}', allow_skip={allow_skip}, force_solve={force_solve}, max_iter={max_iter}"
    )

    def get_last_trial(player):
        trials = Trial.filter(player=player, round=0, iteration=player.game_iteration)
        trial = trials[-1] if len(trials) else None
        return trial

    def get_last_trial_clone(player):
        # makes a clone to check changes of the same instance
        data = Trial.values_dicts(player=player)
        if len(data) == 0:
            return None
        datum = data[-1]
        del datum['id']
        return Trial(**datum)

    def get_stats(player):
        return {
            'total': len(Trial.filter(player=player, round=0)),
            'correct': len(Trial.filter(player=player, round=0, is_correct=True)),
            'incorrect': len(Trial.filter(player=player, round=0, is_correct=False)),
        }

    def restart(player):
        return method(player.id_in_group, {})[player.id_in_group]

    def move_forward(player):
        return method(player.id_in_group, {'next': True})[player.id_in_group]

    def expect_forwarded(player, _last):
        _trial = get_last_trial(player)
        expect(_trial.id, "!=", _last.id)
        expect(_trial.timestamp, ">", _last.timestamp)
        expect(_trial.iteration, ">", _last.iteration)

    def expect_not_forwarded(player, _last):
        _trial = get_last_trial(player)
        expect(_trial.id, "==", _last.id)
        expect(_trial.timestamp, "==", _last.timestamp)
        expect(_trial.iteration, "==", _last.iteration)

    def solution(player):
        _trial = get_last_trial(player)
        return _trial.solution

    def give_answer(player, ans):
        _response = method(player.id_in_group, {'answer': ans})[player.id_in_group]
        return _response

    def expect_stats(player, **values):
        stats = get_stats(player)
        expect(stats, values)

    def expect_answered(player, ans, correct=None):
        _trial = get_last_trial(player)

        # make it work for both strings and numbers
        expect(str(_trial.answer), str(ans))

        expect(_trial.answer_timestamp, '>', _trial.timestamp)
        if correct is not None:
            expect(_trial.is_correct, correct)

    def expect_answered_correctly(player, ans):
        expect_answered(player, ans, True)

    def expect_answered_incorrectly(player, ans):
        expect_answered(player, ans, False)

    def expect_reanswered(player, last):
        # NB: `last` should be a clone of Trial
        _trial = get_last_trial(player)
        expect(_trial.answer_timestamp, '>', last.answer_timestamp)
        expect(_trial.retries, '>', last.retries)

    def expect_not_reanswered(player, last):
        # NB: `last` should be a clone of Trial
        _trial = get_last_trial(player)
        expect(_trial.answer_timestamp, '==', last.answer_timestamp)
        expect(_trial.retries, '==', last.retries)

    def expect_not_answered(player):
        _trial = get_last_trial(player)
        expect(_trial.answer, None)
        expect(_trial.is_correct, None)

    def expect_response_puzzle(response):
        expect('image', 'in', response)
        expect(response['image'].startswith("data:text/plain;base64"), True)

    def expect_response_stats(response, **values):
        expect('stats', 'in', response)
        expect(response['stats'], values)

    def expect_response_correct(response):
        expect('feedback', 'in', response)
        expect(response['feedback'], True)

    def expect_response_incorrect(response):
        expect('feedback', 'in', response)
        expect(response['feedback'], False)

    # all test cases are run individually in separate sessions

    if case == 'normal':
        # part of normal flow, checking everything

        # 1st puzzle
        resp = restart(player)
        expect_stats(player, total=1, correct=0, incorrect=0)
        expect_response_puzzle(resp)
        expect_response_stats(resp, total=1, correct=0, incorrect=0)

        last = get_last_trial(player)

        answer = solution(player)
        resp = give_answer(player, answer)
        expect_answered_correctly(player, answer)
        expect_stats(player, total=1, correct=1, incorrect=0)
        expect_not_forwarded(player, last)
        expect_response_correct(resp)
        expect_response_stats(resp, total=1, correct=1, incorrect=0)

        time.sleep(trial_delay)

        # 2nd puzzle
        resp = move_forward(player)
        expect_stats(player, total=2, correct=1, incorrect=0)
        expect_response_puzzle(resp)
        expect_response_stats(resp, total=2, correct=1, incorrect=0)

        last = get_last_trial(player)

        answer = solution(player)
        resp = give_answer(player, answer)
        expect_answered_correctly(player, answer)
        expect_stats(player, total=2, correct=2, incorrect=0)
        expect_not_forwarded(player, last)
        expect_response_correct(resp)
        expect_response_stats(resp, total=2, correct=2, incorrect=0)

        return

    if case == 'replying_correct':
        # part of normal flow, checking everything
        resp = restart(player)
        expect_stats(player, total=1, correct=0, incorrect=0)
        expect_response_puzzle(resp)
        expect_response_stats(resp, total=1, correct=0, incorrect=0)

        answer = solution(player)
        resp = give_answer(player, answer)
        expect_answered_correctly(player, answer)
        expect_stats(player, total=1, correct=1, incorrect=0)
        expect_response_correct(resp)
        expect_response_stats(resp, total=1, correct=1, incorrect=0)

        return

    if case == 'replying_incorrect':
        # part of normal flow, checking everything
        resp = restart(player)
        expect_stats(player, total=1, correct=0, incorrect=0)
        expect_response_puzzle(resp)
        expect_response_stats(resp, total=1, correct=0, incorrect=0)

        answer = "0"  # should work as invalid both for string and numeric
        resp = give_answer(player, answer)
        expect_answered_incorrectly(player, answer)
        expect_stats(player, total=1, correct=0, incorrect=1)
        expect_response_incorrect(resp)
        expect_response_stats(resp, total=1, correct=0, incorrect=1)

        return

    if case == 'messaging_bogus':
        with expect_failure(ValueError):
            method(player.id_in_group, "BOGUS")
        return

    if case == 'reloading':
        restart(player)
        first = get_last_trial(player)

        restart(player)
        last = get_last_trial(player)

        expect_not_forwarded(player, first)
        return

    if case == 'forward_premature':
        with expect_failure(RuntimeError):
            move_forward(player)
        last = get_last_trial_clone(player)
        expect(last, None)
        return

    if case == 'replying_empty':
        restart(player)
        with expect_failure(ValueError):
            give_answer(player, "")
        expect_not_answered(player)
        return

    if case == 'replying_null':
        restart(player)
        with expect_failure(ValueError):
            give_answer(player, None)
        expect_not_answered(player)
        return

    if case == 'replying_premature':
        last = get_last_trial(player)
        expect(last, None)
        answer = "123"
        with expect_failure(RuntimeError):
            give_answer(player, answer)
        return

    if case == 'retrying_correct':
        restart(player)

        # 1st incorrect answer
        answer1 = "0"
        give_answer(player, answer1)
        expect_answered_incorrectly(player, answer1)
        expect_stats(player, total=1, correct=0, incorrect=1)

        last = get_last_trial_clone(player)

        time.sleep(retry_delay)

        # 2nd correct answer
        answer2 = solution(player)

        if allow_retry:
            give_answer(player, answer2)
            last2 = get_last_trial(player)
            expect_reanswered(player, last)
            expect_answered_correctly(player, answer2)
            expect_stats(player, total=1, correct=1, incorrect=0)
        else:
            with expect_failure(RuntimeError):
                give_answer(player, answer2)
            expect_not_reanswered(player, last)
            # state not changed
            expect_answered_incorrectly(player, answer1)
            expect_stats(player, total=1, correct=0, incorrect=1)
        return

    if case == 'retrying_incorrect':
        restart(player)

        # 1st correct answer
        answer1 = solution(player)
        resp = give_answer(player, answer1)
        expect_answered_correctly(player, answer1)
        expect_stats(player, total=1, correct=1, incorrect=0)

        last = get_last_trial_clone(player)

        time.sleep(retry_delay)

        # 2nd incorrect answer
        answer2 = "0"

        if allow_retry:
            give_answer(player, answer2)
            expect_reanswered(player, last)
            expect_answered_incorrectly(player, answer2)
            expect_stats(player, total=1, correct=0, incorrect=1)
        else:
            with expect_failure(RuntimeError):
                give_answer(player, answer2)
            expect_not_reanswered(player, last)
            # state not changed
            expect_answered_correctly(player, answer1)
            expect_stats(player, total=1, correct=1, incorrect=0)
        return

    if case == 'retrying_nodelay':
        restart(player)

        # 1st incorrect answer
        answer1 = "0"
        resp = give_answer(player, answer1)
        expect_answered_incorrectly(player, answer1)
        expect_stats(player, total=1, correct=0, incorrect=1)

        last = get_last_trial_clone(player)

        # 2nd correct answer
        answer2 = solution(player)

        # no matter if retry is allowed or not
        with expect_failure(RuntimeError):
            give_answer(player, answer2)
        expect_not_reanswered(player, last)
        # state not changed
        expect_answered_incorrectly(player, answer1)
        expect_stats(player, total=1, correct=0, incorrect=1)

        return

    if case == 'forward_nodelay':
        restart(player)
        last = get_last_trial(player)

        answer = solution(player)
        give_answer(player, answer)

        with expect_failure(RuntimeError):
            move_forward(player)
        expect_not_forwarded(player, last)

        return

    if case == 'skipping_unanswered':
        restart(player)
        expect_stats(player, total=1, correct=0, incorrect=0)
        last = get_last_trial(player)

        time.sleep(trial_delay)

        if allow_skip:
            move_forward(player)
            expect_forwarded(player, last)
            expect_stats(player, total=2, correct=0, incorrect=0)
        else:
            with expect_failure(RuntimeError):
                move_forward(player)
            expect_not_forwarded(player, last)
            expect_stats(player, total=1, correct=0, incorrect=0)
        return

    if case == 'skipping_incorrect':
        restart(player)
        expect_stats(player, total=1, correct=0, incorrect=0)
        last = get_last_trial(player)

        answer = "0"  # should work as invalid both for string and numeric
        give_answer(player, answer)
        expect_answered_incorrectly(player, answer)
        expect_stats(player, total=1, correct=0, incorrect=1)

        time.sleep(trial_delay)

        if force_solve:
            with expect_failure(RuntimeError):
                move_forward(player)
            expect_not_forwarded(player, last)
            expect_stats(player, total=1, correct=0, incorrect=1)
        else:  # just a part of normal flow
            move_forward(player)
            expect_forwarded(player, last)
            expect_stats(player, total=2, correct=0, incorrect=1)
        return

    if case == 'iter_limit':
        # exhaust all iterations
        if max_iter is None:
            return

        last = None

        for _ in range(max_iter):
            if _ == 0:
                resp = restart(player)
                expect_response_puzzle(resp)
                last = get_last_trial(player)
            else:
                time.sleep(trial_delay)
                resp = move_forward(player)
                expect_forwarded(player, last)
                expect_response_puzzle(resp)
                last = get_last_trial(player)

            answer = solution(player)
            resp = give_answer(player, answer)
            expect_answered_correctly(player, answer)
            expect_response_correct(resp)

        time.sleep(trial_delay)
        resp = move_forward(player)
        expect_not_forwarded(player, last)
        expect('gameover', 'in', resp)

        return

    raise NotImplementedError("missing test case", case)  # or missing `return`
