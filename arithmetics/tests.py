from otree.api import Bot, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield Intro
        yield Game
        # yield Results

        expect(len(PuzzleRecord.filter(player=self.player, is_correct=True)), 3)
        expect(len(PuzzleRecord.filter(player=self.player, is_correct=False, is_skipped=False)), 5)
        expect(len(PuzzleRecord.filter(player=self.player, is_correct=False, is_skipped=True)), 7)


def call_live_method(method, **kwargs):
    # expecting predictable equations like iter_number + ter_number
    method(1, {'start': True})
    # 3 correct answers
    for i in range(1, 4):
        method(1, {'answer': f"{i+i:03}"})
    # 5 incorrect answers
    for i in range(0, 5):
        method(1, {'answer': "0"})
    # 7 skipped
    for i in range(0, 7):
        method(1, {'answer': ""})
