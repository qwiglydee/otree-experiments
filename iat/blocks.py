# setup of rounds
# categories are configured in session config like:
# primary = ['male', 'female'], secondary = ['work', 'family']
# numbers in block config corresponds to 1st and 2nd element of corresponding pair
#


# classic setup
# primary category switches, secondary stays in place
BLOCKS1 = {
    # e.g: male vs female
    1: {
        'title': "Round 1 (practice)",
        'practice': True,
        'left': {'primary': 1},
        'right': {'primary': 2},
    },
    # e.g: work vs family
    2: {
        'title': "Round 2 (practice)",
        'practice': True,
        'left': {'secondary': 1},
        'right': {'secondary': 2},
    },
    # e.g: male+work vs female+family
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
    # e.g: female vs male
    5: {
        'title': "Round 5 (practice)",
        'practice': True,
        'left': {'primary': 2},
        'right': {'primary': 1},
    },
    # e.g: female+work vs male+family
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

# alternative setup
# primary category stays in place, secondary switches
BLOCKS2 = {
    # e.g: male vs female
    1: {
        'title': "Round 1 (practice)",
        'practice': True,
        'left': {'primary': 1},
        'right': {'primary': 2},
    },
    # e.g: work vs family
    2: {
        'title': "Round 2 (practice)",
        'practice': True,
        'left': {'secondary': 1},
        'right': {'secondary': 2},
    },
    # e.g: male+work vs female+family
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
    # e.g: family vs work
    5: {
        'title': "Round 5 (practice)",
        'practice': True,
        'left': {'secondary': 2},
        'right': {'secondary': 1},
    },
    # e.g: male+family vs female+work
    6: {
        'title': "Round 6",
        'practice': False,
        'left': {'primary': 1, 'secondary': 2},
        'right': {'primary': 2, 'secondary': 1},
    },
    7: {
        'title': "Round 7",
        'practice': False,
        'left': {'primary': 1, 'secondary': 2},
        'right': {'primary': 2, 'secondary': 1},
    },
}

BLOCKS = BLOCKS1
