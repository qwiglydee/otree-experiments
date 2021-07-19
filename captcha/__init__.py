from otree import api


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
    pass


class Results(api.Page):
    pass


page_sequence = [MainPage, Results]
