from os import environ

SESSION_CONFIGS = [
    # all features with their default values, to make them available in session config UI
    dict(
        name="transcription",
        display_name="Transcription of distorted text (configurable characters and length)",
        num_demo_participants=1,
        app_sequence=["real_effort"],
        task='transcription',
        attempts_per_puzzle=2,
        retry_delay=3.0,
    ),
    dict(
        name="matrices",
        display_name="matrices of 0 and 1 (configurable symbols and size)",
        num_demo_participants=1,
        app_sequence=["real_effort"],
        task='matrix',
        attempts_per_puzzle=1,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = ['ret_params']

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = "en"

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = "USD"
USE_POINTS = True

ADMIN_USERNAME = "admin"
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get("OTREE_ADMIN_PASSWORD")

DEMO_PAGE_TITLE = "Real-effort tasks"
DEMO_PAGE_INTRO_HTML = """
Real-effort tasks with multiple configuration options such as
        "puzzle_delay",
        and "retry_delay" (see settings.py).
"""

SECRET_KEY = "2015765205890"

# adjustments for testing
# generating session configs for all varieties of features
import sys

if sys.argv[1] == 'test':
    APPS = ['transcription', 'matrices']
    PUZZLE_DELAY = 0.2
    RETRY_DELAY = 0.4  # required anyway because test cases use it
    MAX_ITERATIONS = 5
    SESSION_CONFIGS = []
    for app in APPS:
        SESSION_CONFIGS.extend(
            [
                dict(
                    name=f"{app}_defaults",
                    num_demo_participants=1,
                    app_sequence=[app],
                    puzzle_delay=PUZZLE_DELAY,
                    retry_delay=RETRY_DELAY,
                ),
                dict(
                    name=f"{app}_limited",
                    num_demo_participants=1,
                    app_sequence=[app],
                    max_iterations=MAX_ITERATIONS,
                    puzzle_delay=PUZZLE_DELAY,
                    retry_delay=RETRY_DELAY,
                ),
                dict(
                    name=f"{app}_forcing",
                    num_demo_participants=1,
                    app_sequence=[app],
                    force_solve=True,
                    puzzle_delay=PUZZLE_DELAY,
                    retry_delay=RETRY_DELAY,
                ),
                dict(
                    name=f"{app}_retrying",
                    num_demo_participants=1,
                    app_sequence=[app],
                    puzzle_delay=PUZZLE_DELAY,
                    retry_delay=RETRY_DELAY,
                    allow_retry=True,
                ),
            ]
        )
