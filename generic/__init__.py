from otree.api import *
from .core import custom_export_core, common_vars, creating_session_core, play_game

doc = """
Generic stimulus/response app
"""


class Constants(BaseConstants):
    name_in_url = "generic"
    players_per_group = None
    num_rounds = 1

    """possible choices 
    both for stimuli categories and responses
    should be associated with actual categories from pool in session config: 
    `categories={'left': something, 'right': something}`
    """
    choices = ["left", "right"]

    """Mapping of keys to choices
    the key names to use to match KeyboardEvent
    possible key names reference and compatibility: 
    https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code/code_values
    """
    keymap = {'KeyF': 'left', 'KeyJ': 'right'}

    instructions_template = __name__ + "/instructions.html"


class Subsession(BaseSubsession):
    is_practice = models.BooleanField(initial=False)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)
    num_trials = models.IntegerField(initial=0)
    num_solved = models.IntegerField(initial=0)
    num_failed = models.IntegerField(initial=0)


class Trial(ExtraModel):
    """A record of single iteration"""

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)
    # time when the trial was picked up, None for pregenerated
    server_loaded_timestamp = models.FloatField()

    stimulus = models.StringField()
    category = models.StringField()
    solution = models.StringField()

    server_response_timestamp = models.FloatField()
    response = models.StringField()
    reaction_time = models.FloatField()
    is_correct = models.BooleanField()


def creating_session(subsession):
    creating_session_core(subsession, Trial)


def custom_export(players):
    return custom_export_core(players, Trial)


class Intro(Page):
    @staticmethod
    def vars_for_template(player: Player):
        d = common_vars(player, Constants)
        # add any extra keys to d here
        return d


class Main(Page):
    @staticmethod
    def js_vars(player: Player):
        d = common_vars(player, Constants)
        # add any extra keys to d here
        return d

    @staticmethod
    def vars_for_template(player: Player):
        d = common_vars(player, Constants)
        # add any extra keys to d here
        return d

    @staticmethod
    def live_method(player: Player, data):
        return play_game(player, data, Trial)


class Results(Page):
    pass


page_sequence = [Intro, Main, Results]
