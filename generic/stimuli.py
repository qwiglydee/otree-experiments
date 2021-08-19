""" Utils to load pool of stimuli.

Pool is auto-loaded from file `stimuli.csv`
The variable POOL is a list of all records from the file as dicts with keys for all fields from header row.

The file should contain at least 'stimulus' and 'category' fields.
All other fields are preserved for some specific needs.
"""

from pathlib import Path
import csv


BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "stimuli.csv"
REQ_FIELDS = ['stimulus', 'category']


POOL = []


def filter_by_category(category):
    def filt(row):
        return row['category'] == category
    return list(filter(filt, POOL))


def filter_by_fields(**fields):
    def filt(row):
        return all([row[k] == v for k, v in fields.items()])
    return list(filter(filt, POOL))


def load_csv(filename, required_fields=None):
    data = list()
    required = required_fields or []
    with open(filename, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, dialect='excel')
        fields = reader.fieldnames
        for fld in required:
            if fld not in fields:
                raise RuntimeError(f"field '{fld}' is missing in {filename}")
        for row in reader:
            for fld in required:
                if row[fld] == "" or row[fld] is None:
                    raise RuntimeError(f"field '{fld}' is empty in {filename}:{reader.line_num}")
            for fld in fields:
                val = row[fld]
                if val.startswith("image:"):
                    path = BASE_DIR / "static" / "images" / val[6:]
                    if not path.exists():
                        raise RuntimeError(f"missing file '{path}' for field '{fld}' in {filename}:{reader.line_num}")

            data.append(row)
    return data


if CSV_FILE.exists():
    POOL = load_csv(CSV_FILE, REQ_FIELDS)
