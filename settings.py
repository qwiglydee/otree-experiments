from os import environ

SESSION_CONFIGS = [
    dict(
        name="generic",
        display_name="generic stimuli recognition task",
        num_demo_participants=1,
        app_sequence=["generic"],
        categories={'foo': 'positive', 'bar': 'negative'},
        labels={'foo': 'Positive', 'bar': 'Negative'},
    ),
    dict(
        name="sliders",
        display_name="RET Slider task",
        num_demo_participants=1,
        app_sequence=["sliders"],
    ),
    dict(
        name="decoding",
        display_name="RET Decoding numbers to words",
        num_demo_participants=1,
        app_sequence=["real_effort"],
        task='decoding',
        attempts_per_puzzle=1,
    ),
    dict(
        name="transcription",
        display_name="RET Transcription of text from an image",
        num_demo_participants=1,
        app_sequence=["real_effort"],
        task='transcription',
        attempts_per_puzzle=2,
        retry_delay=3.0,
    ),
    dict(
        name="matrices",
        display_name="RET Counting symbols in a matrix",
        num_demo_participants=1,
        app_sequence=["real_effort"],
        task='matrix',
        attempts_per_puzzle=1,
    ),
    dict(
        name="iat_words",
        display_name="IAT using words, from CSV",
        num_demo_participants=1,
        app_sequence=["iat"],
        primary=['male', 'female'],
        secondary=['career', 'family'],
        num_iterations={1: 5, 2: 5, 3: 10, 4: 20, 5: 5, 6: 10, 7: 20},
    ),
    dict(
        name="iat_images",
        display_name="IAT using images",
        num_demo_participants=1,
        app_sequence=["iat"],
        primary_images=True,
        primary=['images:felidae', 'images:canidae'],
        secondary_images=True,
        secondary=['emojis:positive', 'emojis:negative'],
        num_iterations={1: 5, 2: 5, 3: 10, 4: 20, 5: 5, 6: 10, 7: 20},
    ),
    dict(
        name="iat_mixed",
        display_name="IAT using images and words",
        num_demo_participants=1,
        app_sequence=["iat"],
        primary_images=True,
        primary=['images:felidae', 'images:canidae'],
        secondary=['male', 'female'],
        num_iterations={1: 5, 2: 5, 3: 10, 4: 20, 5: 5, 6: 10, 7: 20},
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

DEMO_PAGE_TITLE = "Real-effort tasks"
DEMO_PAGE_INTRO_HTML = """
Real-effort tasks with multiple configuration options.
"""

SECRET_KEY = "2015765205890"

# adjustments for testing
# generating session configs for all varieties of features
import sys


if sys.argv[1] == 'test':
    MAX_ITERATIONS = 5
    FREEZE_TIME = 0.1
    TRIAL_PAUSE = 0.2
    TRIAL_TIMEOUT = 0.3

    SESSION_CONFIGS = [
        dict(
            name=f"testing_generic",
            num_demo_participants=1,
            app_sequence=['generic'],
            trial_pause=TRIAL_PAUSE,
            trial_timeout=TRIAL_TIMEOUT,
            freeze_seconds=FREEZE_TIME,
            num_iterations=MAX_ITERATIONS,
            attempts_per_trial=1,
            categories={'foo': 'positive', 'bar': 'negative'},
            labels={'foo': 'Positive', 'bar': 'Negative'},
        ),
        dict(
            name=f"testing_generic_retries",
            num_demo_participants=1,
            app_sequence=['generic'],
            trial_pause=TRIAL_PAUSE,
            trial_timeout=TRIAL_TIMEOUT,
            freeze_seconds=FREEZE_TIME,
            num_iterations=MAX_ITERATIONS,
            attempts_per_trial=3,
            categories={'foo': 'positive', 'bar': 'negative'},
            labels={'foo': 'Positive', 'bar': 'Negative'},
        ),
        dict(
            name=f"testing_iat",
            num_demo_participants=1,
            app_sequence=['iat'],
            trial_delay=TRIAL_PAUSE,
            retry_delay=FREEZE_TIME,
            primary=['canidae', 'felidae'],
            secondary=['positive', 'negative'],
            num_iterations={1: 2, 2: 2, 3: 3, 4: 3, 5: 2, 6: 3, 7: 3},
        ),
        dict(
            name=f"testing_sliders",
            num_demo_participants=1,
            app_sequence=['sliders'],
            trial_delay=TRIAL_PAUSE,
            retry_delay=FREEZE_TIME,
            num_sliders=3,
            attempts_per_slider=3,
        ),
    ]
    for task in ['decoding', 'matrix', 'transcription']:
        SESSION_CONFIGS.extend(
            [
                dict(
                    name=f"testing_{task}_defaults",
                    num_demo_participants=1,
                    app_sequence=['real_effort'],
                    puzzle_delay=TRIAL_PAUSE,
                    retry_delay=FREEZE_TIME,
                ),
                dict(
                    name=f"testing_{task}_retrying",
                    num_demo_participants=1,
                    app_sequence=['real_effort'],
                    puzzle_delay=TRIAL_PAUSE,
                    retry_delay=FREEZE_TIME,
                    attempts_per_puzzle=5,
                ),
                dict(
                    name=f"testing_{task}_limited",
                    num_demo_participants=1,
                    app_sequence=['real_effort'],
                    puzzle_delay=TRIAL_PAUSE,
                    retry_delay=FREEZE_TIME,
                    max_iterations=MAX_ITERATIONS,
                ),
            ]
        )
