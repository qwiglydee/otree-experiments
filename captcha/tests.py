from otree.api import *
from . import Game, Trial
from test_shared import call_live_method  # noqa
from test_shared import end_game_assertions


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(Game, check_html=False, timeout_happened=True)

        player = self.player
        end_game_assertions(player)
