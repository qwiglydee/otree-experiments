from otree.api import *

from .testing_utils import *
from . import Constants, Trial, Intro, Main, Results


class PlayerBot(Bot):
    cases = [
        "normal",
        "messaging_bogus",
        "reloading",
        "responding_bogus",
        "responding_notrial",
        "responding_timeout",
        "responding_aftertimeout",
        "retrying_nofreeze",
        "retrying_exhaust",
        "advancing_nopause",
        "advancing_noanswer",
        "advancing_exhaust",
    ]

    def play_round(self):
        params = self.session.params

        if 'retrying' in self.case and params['attempts_per_trial'] == 1:
            print(f"Skipping test case: {self.case}")
            return

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
        num_skipped = len(Trial.filter(player=player, is_timeout=True))
        num_total = num_correct + num_incorrect + num_skipped

        expect(player.num_trials, num_total)
        expect(player.num_solved, num_correct)
        expect(player.num_failed, num_incorrect)

        generated = [t.stimulus for t in Trial.filter(player=player)]
        uniq = set(generated)
        expect(len(generated), len(uniq))


def call_live_method(method, group, case, **kwargs):  # noqa
    print(f"Playing live case: {case}")

    testname = f"live_test_{case}"
    try:
        test = globals()[testname]
    except KeyError:
        raise NotImplementedError(f"Test {testname} not implemented")

    test(method, group.get_players()[0], group.session.params)


def live_test_normal(m, p, conf):  # noqa
    """normal flow
    choses correct/incorrect responses for even/odd iterations
    for multi-attempts scenario, submits N-1 incorrect responses
    """
    num_iterations = conf['num_iterations']
    num_attempts = conf['attempts_per_trial']

    r = send(m, p, 'load')
    expect_fields(r, type='status')

    last = None

    for i in range(num_iterations):
        r = send(m, p, 'new')
        expect_fields(r, type='trial')

        z = get_trial(Trial, p)
        expect_attrs(z, iteration=i + 1)
        expect_attrs(p, iteration=i + 1)

        if last:
            expect_new(z, last)

        if num_attempts > 1:
            # give N-1 wrong responses
            for j in range(num_attempts - 1):
                response = get_incorrect_response(z, Constants.choices)
                r = send(m, p, 'response', response=response, reaction_time=1.0)
                expect_fields(r, type='feedback', is_correct=False, is_final=False)

                expect_answered(z, response)
                expect_attrs(z, is_correct=False)

                sleep(conf['input_freezing_time'])

        # last response
        give_correct = i % 2 == 0
        if give_correct:
            response = get_correct_response(z)
        else:
            response = get_incorrect_response(z, Constants.choices)

        r = send(m, p, 'response', response=response, reaction_time=1.0)
        expect_fields(r, type='feedback', is_correct=give_correct, is_final=True)

        expect_answered(z, response)
        expect_attrs(z, is_correct=give_correct, attempts=num_attempts)

        sleep(conf['inter_trial_time'])
        last = z

    expect_attrs(last, iteration=num_iterations)

    resp = send(m, p, 'new')
    expect_fields(resp, type='status', game_over=True)


def live_test_messaging_bogus(m, p, conf):  # noqa

    with expect_failure(ValueError):
        m(p.id_in_group, None)

    with expect_failure(ValueError):
        m(p.id_in_group, "")

    with expect_failure(ValueError):
        m(p.id_in_group, "BOGUS")

    with expect_failure(ValueError):
        m(p.id_in_group, {})

    with expect_failure(RuntimeError):
        m(p.id_in_group, {'type': 'BOGUS'})


def live_test_reloading(m, p, conf):  # noqa
    # start of game
    r = send(m, p, 'load')
    expect_fields(r, type='status')
    expect_attrs(p, iteration=0)

    z = get_trial(Trial, p)
    expect(z, '==', None)

    send(m, p, 'new')

    # midgame
    r = send(m, p, 'load')
    expect_fields(r, type='status')
    expect_attrs(p, iteration=1)

    z = get_trial(Trial, p)
    expect(z, '!=', None)


def live_test_responding_bogus(m, p, conf):  # noqa
    send(m, p, 'load')
    send(m, p, 'new')

    with expect_failure(ValueError):
        send(m, p, 'response')

    with expect_failure(ValueError):
        send(m, p, 'response', response=Constants.choices[0])

    with expect_failure(ValueError):
        send(m, p, 'response', response="BOGUS", reaction_time=1.0)


def live_test_responding_notrial(m, p, conf):  # noqa
    send(m, p, 'load')
    with expect_failure(RuntimeError):
        send(m, p, 'response', response=Constants.choices[0], reaction_time=1.0)


def live_test_responding_timeout(m, p, conf):  # noqa
    default_response = Constants.timeout_response

    send(m, p, 'load')
    send(m, p, 'new')
    z = get_trial(Trial, p)

    sleep(conf['auto_response_time'])

    r = send(m, p, 'timeout')
    expect_fields(
        r, type='feedback', is_correct=False, is_final=True, response=default_response
    )

    expect_attrs(
        z,
        response=default_response,
        is_correct=False,
        is_timeout=True,
        reaction_time=None,
    )


def live_test_responding_aftertimeout(m, p, conf):  # noqa
    default_response = Constants.timeout_response

    send(m, p, 'load')
    send(m, p, 'new')
    z = get_trial(Trial, p)

    sleep(conf['auto_response_time'])

    with expect_failure(RuntimeError):
        send(m, p, 'response', response=get_correct_response(z), reaction_time=1.0)

    expect_attrs(z, response=None)


def live_test_retrying_nofreeze(m, p, conf):  # noqa
    send(m, p, 'load')
    send(m, p, 'new')
    z = get_trial(Trial, p)

    response1 = get_incorrect_response(z, Constants.choices)
    response2 = get_correct_response(z)

    r = send(m, p, 'response', response=response1, reaction_time=1.0)

    with expect_failure(RuntimeError):
        send(m, p, 'response', response=response2, reaction_time=1.0)

    expect_attrs(z, response=response1, is_correct=False)


def live_test_retrying_exhaust(m, p, conf):  # noqa
    max_attempts = conf['attempts_per_trial']

    send(m, p, 'load')
    send(m, p, 'new')
    z = get_trial(Trial, p)

    response1 = get_incorrect_response(z, Constants.choices)
    response2 = get_correct_response(z)

    # give N-1 wrong responses
    for j in range(max_attempts - 1):
        r = send(m, p, 'response', response=response1, reaction_time=1.0)
        expect_fields(r, type='feedback', is_correct=False, is_final=False)
        sleep(conf['input_freezing_time'])

    # give last wrong response
    r = send(m, p, 'response', response=response1, reaction_time=1.0)
    expect_fields(r, type='feedback', is_correct=False, is_final=True)
    sleep(conf['input_freezing_time'])

    # fail to give more responses
    with expect_failure(RuntimeError):
        send(m, p, 'response', response=response2, reaction_time=1.0)

    expect_attrs(z, response=response1, is_correct=False)


def live_test_advancing_nopause(m, p, conf):  # noqa
    send(m, p, 'load')
    send(m, p, 'new')

    z = get_trial(Trial, p)
    send(m, p, 'response', response=get_correct_response(z), reaction_time=1.0)

    expect_attrs(p, iteration=1)

    with expect_failure(RuntimeError):
        send(m, p, 'new')

    expect_attrs(p, iteration=1)


def live_test_advancing_noanswer(m, p, conf):  # noqa
    send(m, p, 'load')
    send(m, p, 'new')

    z = get_trial(Trial, p)

    expect_attrs(p, iteration=1)

    sleep(conf['inter_trial_time'])

    with expect_failure(RuntimeError):
        send(m, p, 'new')

    expect_attrs(p, iteration=1)


def live_test_advancing_exhaust(m, p, conf):  # noqa
    num_iterations = conf['num_iterations']

    send(m, p, 'load')

    z = None
    for i in range(0, num_iterations):
        send(m, p, 'new')
        z = get_trial(Trial, p)
        send(m, p, 'response', response=get_correct_response(z), reaction_time=1.0)
        sleep(conf['inter_trial_time'])

    expect_attrs(p, iteration=num_iterations)
    z = get_trial(Trial, p)
    expect_attrs(z, iteration=num_iterations)

    send(m, p, 'new')

    expect_attrs(p, iteration=num_iterations)
    z = get_trial(Trial, p)
    expect_attrs(z, iteration=num_iterations)
