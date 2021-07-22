from otree.api import Bot, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield Game

        expect(len(Trial.filter(player=self.player, is_correct=True)), 3)
        expect(len(Trial.filter(player=self.player, is_correct=False)), 5)
        expect(len(Trial.filter(player=self.player, answer=None)), 7)

        expect(self.player.total, 15)
        expect(self.player.answered, 8)
        expect(self.player.correct, 3)
        expect(self.player.incorrect, 5)


def call_live_method(method, **kwargs):
    # expecting all puzzles be "yellow"

    # 3 correct answers
    for i in range(0, 3):
        method(1, {"next": True})
        response = method(1, {"answer": "yellow"})
        assert response[1]['feedback'] is True
    # 5 incorrect answers
    for i in range(0, 5):
        method(1, {"next": True})
        response = method(1, {"answer": "blue"})
        assert response[1]['feedback'] is False
    # 7 skipped
    for i in range(0, 7):
        method(1, {"next": True})
