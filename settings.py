from os import environ

SESSION_CONFIGS = [
    dict(
        name="demo_stimuli",
        display_name="demo stimulus/response real time",
        app_sequence=['demo_stimuli'],
        num_demo_participants=1,
    ),
    dict(
        name="demo_trials",
        display_name="demo trial/answer live page",
        app_sequence=['demo_trials'],
        num_demo_participants=1,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = ['is_dropout']
SESSION_FIELDS = ['params']

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = "en"

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = "USD"
USE_POINTS = True

ADMIN_USERNAME = "admin"
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get("OTREE_ADMIN_PASSWORD")

DEMO_PAGE_TITLE = "Demo apps"
DEMO_PAGE_INTRO_HTML = """
Demo apps
"""

SECRET_KEY = "2015765205890"

# adjustments for testing
# generating session configs for all varieties of features
import sys


if sys.argv[1] == 'test':
    SESSION_CONFIGS = [
    ]
