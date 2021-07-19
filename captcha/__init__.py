from otree import api

from . import utils

doc = """
Experimental catcha game
"""


class Constants(api.BaseConstants):
    name_in_url = 'captcha'
    players_per_group = None
    num_rounds = 1


class Subsession(api.BaseSubsession):
    pass


class Group(api.BaseGroup):
    pass


class Player(api.BasePlayer):
    pass


# customizable functions

def generate_text(player: Player, difficulty: int):
    return utils.generate_text(difficulty)


def generate_image(text):
    image = utils.generate_image(text)
    image = utils.distort_image(image)
    return image


# PAGES


class MainPage(api.Page):
    timeout_seconds = 60

    def live_method(player: Player, data):
        difficulty = 5
        puzzle = generate_text(player, difficulty)
        image = generate_image(puzzle)
        data = utils.encode_image(image)
        return {player.id_in_group: {'image': data}}


class Results(api.Page):
    pass


page_sequence = [MainPage, Results]
