from os import stat
from otree.api import *

from common.live_utils import live_page

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = "chat"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    joined = models.BooleanField(initial=False)
    nickname = models.StringField()


def get_party(group):
    return [p.nickname for p in group.get_players() if p.joined]


# PAGES


@live_page
class Main(Page):
    @staticmethod
    def handle_join(player, message: dict):
        print("joining", message)
        player.joined = True
        player.nickname = message["nickname"]
        return {0: dict(joined=dict(newcomer=player.nickname, party=get_party(player.group)))}

    def handle_leave(player, message: dict):
        print("leaving", message)
        player.joined = False
        return {0: dict(left=dict(nickname=player.nickname, party=get_party(player.group)))}

    @staticmethod
    def handle_saying(player, message):
        print("saying", message)
        return {0: dict(talk=dict(source=player.nickname, text=message["text"]))}

    @staticmethod
    def handle_wispering(player, message):
        print("whispering", message)
        dest = [p for p in player.group.get_players() if p.nickname == message['dest']][0]
        return {dest: dict(wisper=dict(source=player.nickname, text=message["text"]))}


page_sequence = [Main]
