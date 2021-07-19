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


# PAGES
class MainPage(api.Page):
    timeout_seconds = 60

    @staticmethod
    def vars_for_template(player):
        text = utils.generate_text(5)
        image = utils.generate_image(text)
        image = utils.distort_image(image)
        data = utils.encode_image(image)
        return {'image': data}


class Results(api.Page):
    pass


page_sequence = [MainPage, Results]
