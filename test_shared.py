TRIAL_DELAY = 0.1
RETRY_DELAY = 0.2
import time
from contextlib import contextmanager
from otree.api import *
from importlib import import_module


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

    expect(player.total, len(Trial.filter(player=player)))
    expect(player.correct, len(Trial.filter(player=player, is_correct=True)))
    expect(player.incorrect, len(Trial.filter(player=player, is_correct=False)))


def call_live_method(method, group, **kwargs):
    player = group.get_players()[0]
    Trial = get_trial_class(player)

    def get_last_trial(player):
        trials = Trial.filter(player=player)
        trial = trials[-1] if len(trials) else None
        return trial

    conf = player.session.config
    # patch session to speed up tests
    conf['trial_delay'] = TRIAL_DELAY
    conf['retry_delay'] = RETRY_DELAY

    force_solve = conf.get('force_solve', False)
    allow_skip = conf.get('allow_skip', False)
    max_iterations = conf.get('num_iterations')

    def move_forward():
        _response = method(1, {'next': True})[1]
        return _response, get_last_trial(player)

    def expect_forwarded(_last, _trial):
        if _last:
            expect(_trial.id, "!=", _last.id)
            expect(_trial.timestamp, ">", _last.timestamp)
            expect(_trial.iteration, ">", _last.iteration)

    def expect_not_forwarded(_last, _trial):
        if _last:
            expect(_trial.id, "==", _last.id)
            expect(_trial.timestamp, "==", _last.timestamp)
            expect(_trial.iteration, "==", _last.iteration)

    def expect_image(_response):
        expect('image', 'in', _response)
        expect(_response['image'].startswith("data:text/plain;base64"), True)

    def give_answer(ans):
        _response = method(1, {'answer': ans})[1]
        return _response, get_last_trial(player)

    def expect_answered(_trial, _response, ans, valid):
        expect(_trial.answer, ans)
        expect(_trial.answer_timestamp, '>', _trial.timestamp)
        expect(_trial.is_correct, valid)
        expect(_response['feedback'], valid)

    def expect_stats(_last_stats, _stats, **updates):
        for k, v in updates.items():
            exp = _last_stats[k] + v if _last_stats else v
            if _stats[k] != exp:
                raise AssertionError(
                    f"Stats key `{k}`: expected to be {exp}, actual {_stats[k]}"
                )

    last = None
    last_stats = {}
    response = {}

    # fail to submit bogus message
    with expect_failure(ValueError):
        _response = method(1, "BOGUS")

    # fail to answer w/out start
    with expect_failure(RuntimeError):
        _response = method(1, {'answer': "123"})

    # start
    time.sleep(TRIAL_DELAY)
    response, trial = move_forward()
    expect_forwarded(last, trial)
    expect_image(response)

    # fail to advance w/out delay ####
    with expect_failure(RuntimeError):
        response, trial = move_forward()
    expect_not_forwarded(last, trial)

    # fail to submit empty answer
    with expect_failure(ValueError):
        _response = method(1, {'answer': ""})

    # 1 correct answer
    answer = trial.solution
    response, trial = give_answer(answer)
    expect_answered(trial, response, answer, True)
    stats = response['stats']
    expect_stats(None, stats, total=1, answered=1, correct=1)

    last = trial
    last_stats = stats

    # fail to answer again w/out delay
    with expect_failure(RuntimeError):
        give_answer(answer)

    # succeed to answer again after delay
    time.sleep(RETRY_DELAY)
    response, trial = give_answer(answer)
    expect_answered(trial, response, answer, True)
    # stats shan't change though
    expect(response['stats'], last_stats)

    if force_solve:
        # create new trial
        time.sleep(TRIAL_DELAY)
        response, trial = move_forward()
        expect_forwarded(last, trial)

        # give incorrect answer
        answer1 = "0"
        response, trial = give_answer(answer1)
        expect_answered(trial, response, answer1, False)

        stats = response['stats']
        expect_stats(last_stats, stats, total=1, answered=1, incorrect=1)

        last = trial
        last_stats = stats

        # fail to retry w/out delay
        answer2 = trial.solution
        with expect_failure(RuntimeError):
            response, trial = give_answer(answer2)

        # trial should stay with old answer
        expect_answered(trial, response, answer1, False)

        # fail to skip
        with expect_failure(RuntimeError):
            time.sleep(TRIAL_DELAY)
            move_forward()

        expect_not_forwarded(last, trial)

        # retry with waiting
        answer3 = trial.solution
        time.sleep(RETRY_DELAY)
        response, trial = give_answer(answer3)

        expect_answered(trial, response, answer3, True)

        expect(trial.retries, 2)  # 1st and 3rd

        stats = response['stats']
        expect_stats(last_stats, stats, incorrect=-1, correct=1)
        last_stats = stats

    elif allow_skip:
        # create new trial
        time.sleep(TRIAL_DELAY)
        response, trial = move_forward()
        expect_forwarded(last, trial)
        last = trial

        # skip to next
        time.sleep(TRIAL_DELAY)
        response, trial = move_forward()
        expect_forwarded(last, trial)

        # answer
        answer = trial.solution
        response, trial = give_answer(answer)
        expect_answered(trial, response, answer, True)

        stats = response['stats']
        expect_stats(last_stats, stats, total=2, answered=1, correct=1)

        last = trial
        last_stats = stats
    else:
        # create new trial
        time.sleep(TRIAL_DELAY)
        response, trial = move_forward()
        expect_forwarded(last, trial)
        last = trial

        # fail to skip
        with expect_failure(RuntimeError):
            time.sleep(TRIAL_DELAY)
            response, trial = move_forward()

        expect_not_forwarded(last, trial)

        # answer incorrectly
        answer = "0"
        response, trial = give_answer(answer)
        expect_answered(trial, response, answer, False)

        stats = response['stats']
        expect_stats(last_stats, stats, total=1, answered=1, incorrect=1)

        last = trial
        last_stats = stats

    if max_iterations:
        # exhaust all iterations
        for _ in range(stats['total'], max_iterations):
            time.sleep(TRIAL_DELAY)
            response, trial = move_forward()
            expect_forwarded(last, trial)
            expect('image', 'in', response)

            answer = trial.solution
            response, trial = give_answer(answer)
            expect_answered(trial, response, answer, True)

        time.sleep(TRIAL_DELAY)
        response, trial = move_forward()
        expect_forwarded(last, trial)
        expect('gameover', 'in', response)
