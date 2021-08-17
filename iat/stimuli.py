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
    'canidae': ['dog', 'wolf', 'coyote', 'fox', 'jackal'],
    'felidae': ['cat', 'tiger', 'lynx', 'wildcat', 'cougar'],
    'images:canidae': [
        "320px-Black_Labrador_Retriever_-_Male_IMG_3323.jpg",
        "247px-Kolmården_Wolf.jpg",
        "207px-2009-Coyote-Yosemite.jpg",
        "Vulpes_vulpes_ssp_fulvus.jpg",
        "320px-Black-backed_jackal_(Canis_mesomelas_mesomelas)_2.jpg",
    ],
    "images:felidae": [
        "320px-Cat_August_2010-4.jpg",
        "320px-Walking_tiger_female.jpg",
        "159px-Lynx_lynx2.jpg",
        "Felis_silvestris_silvestris_Luc_Viatour.jpg",
        "320px-Mountain_Lion_in_Glacier_National_Park.jpg",
    ],
    'positive': ['amusement', 'fun', 'friendship', 'happyness', 'joy'],
    'negative': ['anger', 'hate', 'fear', 'panic', 'sickness'],
    'emojis:positive': [
        "emoji_u263a.png",
        "emoji_u1f600.png",
        "emoji_u1f601.png",
        "emoji_u1f60a.png",
        "emoji_u1f60d.png",
    ],
    'emojis:negative': [
        "emoji_u2639.png",
        "emoji_u1f612.png",
        "emoji_u1f616.png",
        "emoji_u1f623.png",
        "emoji_u1f62c.png",
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
