"""Dictionary of all words by category

The categories should be paired and put into `primary` or `secondary` session config parameters:
```primary = ['male', 'female'], secondary = ['work', 'family']```

If a file stimuli.csv is present in app dir,
it's content is loaded into the DICT
the csv should contain (at least) two columns: category, stimulus
"""

from pathlib import Path
import csv

DICT = {
    'family': [
        "garden",
        "kitchen",
        "marriage",
        "laundry",
        "home",
        "children",
        "relatives",
    ],
    'career': [
        "office",
        "manager",
        "salary",
        "job",
        "briefcase",
        "profession",
        "employees",
    ],
    "male": [
        "man",
        "he",
        "men",
        "boy",
        "his",
        "gent",
    ],
    "female": [
        "woman",
        "she",
        "women",
        "her",
        "girl",
        "hers",
        "lady",
    ],
}

csvfile = Path(__file__).parent / "stimuli.csv"

if csvfile.exists():
    with open(csvfile, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row['category']
            word = row['stimulus']
            if cat not in DICT:
                DICT[cat] = []
            DICT[cat].append(word)
