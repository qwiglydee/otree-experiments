from generic_core import *

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

    live_method = play_game


class Results(Page):
    pass


page_sequence = [Intro, Main, Results]
