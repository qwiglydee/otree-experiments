import random

from otree.api import *

from common.live_utils import live_page

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = "chat"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    SUPERVISOR_ROLE = "supervis"


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
class Chat(Page):
    @staticmethod
    def handle_join(player, message: dict):
        print("joining", message)
        player.joined = True
        player.nickname = message["nickname"]
        party = get_party(player.group)

        joinmsg = dict(newcomer=player.nickname, party=party)
        statmsg = dict(partysize=len(party))
        return {C.SUPERVISOR_ROLE: dict(join=joinmsg, stat=statmsg), 0: dict(join=joinmsg)}

    def handle_leave(player, message: dict):
        print("leaving", message)
        player.joined = False
        party = get_party(player.group)

        leavmsg = dict(leaver=player.nickname, party=party)
        statmsg = dict(partysize=len(party))
        return {C.SUPERVISOR_ROLE: dict(leave=leavmsg, stat=statmsg), 0: dict(leave=leavmsg)}

    @staticmethod
    def handle_talking(player, message):
        print("talking", message)
        talkmsg = dict(source=player.nickname, text=message["text"])
        return {0: dict(talk=talkmsg)}

    @staticmethod
    def handle_wispering(player, message):
        print("whispering", message)

        dest = [p for p in player.group.get_players() if p.nickname == message["dest"]][0]

        wispmsg = dict(source=player.nickname, dest=dest.nickname, text=message["text"])
        wispmsg0 = dict(source=player.nickname, dest=dest.nickname)

        return {player: dict(wisper=wispmsg), dest: dict(wisper=wispmsg), 0: dict(wisper=wispmsg0)}


page_sequence = [Chat]
