from otree import api

from . import utils

doc = """
Experimental catcha game
"""


class Constants(api.BaseConstants):
    name_in_url = 'captcha'
    players_per_group = None
    num_rounds = 1

    default_captcha_length = 5


class Subsession(api.BaseSubsession):
    pass


class Group(api.BaseGroup):
    pass


class Player(api.BasePlayer):
    pass


# customizable functions

def generate_puzzle(player: Player):
    difficulty = player.session.config.get('captcha_length', Constants.default_captcha_length)
    return difficulty, utils.generate_text(difficulty)


def generate_image(text):
    image = utils.generate_image(text)
    image = utils.distort_image(image)
    return image


def play_captcha(player: Player, data: dict):
    difficulty, puzzle = generate_puzzle(player)
    image = generate_image(puzzle)
    data = utils.encode_image(image)
    return {player.id_in_group: {'image': data}}


# PAGES


class MainPage(api.Page):
    timeout_seconds = 60

    live_method = play_captcha


class Results(api.Page):
    pass


page_sequence = [MainPage, Results]
