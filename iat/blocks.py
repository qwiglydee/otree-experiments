# classic setup of rounds
# 'primary' and 'secondary' are configured in session as pairs of dictionary categories
# numbers refer to positions in the pairs
BLOCKS = {
    1: {
        'title': "Round 1 (practice)",
        'practice': True,
        'left': {'primary': 1},
        'right': {'primary': 2},
    },
    2: {
        'title': "Round 2 (practice)",
        'practice': True,
        'left': {'secondary': 1},
        'right': {'secondary': 2},
    },
    3: {
        'title': "Round 3",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    4: {
        'title': "Round 4",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    5: {
        'title': "Round 5 (practice)",
        'practice': True,
        'left': {'secondary': 2},
        'right': {'secondary': 1},
    },
    6: {
        'title': "Round 6",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
    7: {
        'title': "Round 7",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
}
