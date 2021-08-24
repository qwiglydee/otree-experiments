""" Utils to work with of stimuli

The pool is supposed to get loaded from csv file.
It is loaded into a list of dicts representing all loaded rows and columns as dicts' fields.
"""

from pathlib import Path
import csv


def filter_by_category(pool, categories):
    """Filter stimuli pool by category

    Checks if a stimulis['category'] is in the requested

    Example:
        stimuli = filter_by_category(POOL, ['emojis_positive', 'emojis_negative'])

    Args:
        pool (list of dicts): stimuli to filter
        categories (list): required categories

    Return:
        list of dicts: the matching stimuli

    """

    def filt(row):
        return row['category'] in categories

    return list(filter(filt, pool))


def filter_by_fields(pool, **fields):
    """Filter stimuli pool by fields

    Checks if a stimulis[field] matches given value.

    Example:
        stimuli = filter_by_category(POOL, stimulus_type='emojis')

    Args:
        pool (list of dicts): stimuli to filter
        fields (kwargs): required categories

    Return:
        list of dicts: the matching stimuli
    """

    def filt(row):
        return all([row[k] == v for k, v in fields.items()])

    return list(filter(filt, pool))


def load_csv(filepath, fields=None):
    """Load stimuli from csv file

    If fields aren't specified, all fields are loaded.

    Example:
        POOL = load_csv("stimuli.csv", ['stimulus', 'category'])

    Args:
        filepath (str|Path): full path to the file to load
        fields (list): list of fields to load

    Returns:
        list of dicts: all the records in the file
    """
    data = list()
    with open(filepath, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, dialect='excel')

        if fields is not None:
            headers = reader.fieldnames
            for fld in fields:
                if fld not in headers:
                    raise RuntimeError(f"field '{fld}' is missing in {filepath}")
        else:
            fields = reader.fieldnames

        for row in reader:
            for fld in fields:
                if row[fld] == "" or row[fld] is None:
                    raise RuntimeError(
                        f"field '{fld}' is empty in {filepath}:{reader.line_num}"
                    )
            data.append(row)
    return data
