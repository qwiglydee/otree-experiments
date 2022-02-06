import random

from otree.api import *

from common.live_utils import live_multiplayer

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = "demo_auction"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    INSTRUCTIONS = __name__ + "/instructions.html"

    BID_INCREMENT = 10
    JACKPOT = 100


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


class Auction(ExtraModel):
    group = models.Link(Group)
    is_completed = models.BooleanField(initial=False)

    top_bid = models.CurrencyField(initial=0)
    top_bidder = models.IntegerField()

    second_bid = models.CurrencyField(initial=0)
    second_bidder = models.IntegerField()


def creating_session(subsession: Subsession):
    # initialize games for groups
    for group in subsession.get_groups():
        Auction.create(group=group)


# PAGES


@live_multiplayer
class AuctionPage(Page):
    trial_model = Auction

    @staticmethod
    def encode_trial(auction: Auction):
        return dict(
            top_bid=cu(auction.top_bid),
            top_bidder=f"Player {auction.top_bidder}",
            second_bid=cu(auction.second_bid),
            second_bidder=f"Player {auction.second_bidder}",
            bid=auction.top_bid + C.BID_INCREMENT
        )

    @staticmethod
    def validate_response(auction: Auction, player: Player, response, timeout_happened):
        print("validating", auction, "\nplayer", player, "\nresponse:", response)

        bid = response['input']
        if auction.top_bid and bid <= auction.top_bid:
            return dict(feedback=dict(responseCorrect=False, error="invalid bid"))

        if auction.top_bid:
            auction.second_bid = auction.top_bid
            auction.second_bidder = auction.top_bidder
        auction.top_bid = bid
        auction.top_bidder = player.id_in_group

        # full update
        return dict(update=AuctionPage.encode_trial(auction))

    @staticmethod
    def get_status(auction: Auction, player: Player):
        pid = player.id_in_group
        if pid == auction.top_bidder:
            rank = 1
        elif pid == auction.second_bidder:
            rank = 2
        else:
            rank = None

        return dict(
            playerRank=rank,
            playerActive=(rank != 1),
        )


page_sequence = [AuctionPage]
