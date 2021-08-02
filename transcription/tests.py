from otree.api import *
from . import Game, Puzzle
from test_shared import call_live_method  # noqa
from test_shared import TEST_CASES
from test_shared import end_game_assertions


class PlayerBot(Bot):
    cases = TEST_CASES

    def play_round(self):
        yield Submission(Game, check_html=False, timeout_happened=True)

        player = self.player
        end_game_assertions(player)
