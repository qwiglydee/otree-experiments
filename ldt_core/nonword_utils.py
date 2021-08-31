"""Utilities to generate readable non-words from words.
https://gist.github.com/qwiglydee/696cbc2d83a43906c5d8df59e47847a3

Mutation is based on replacing a cluster of vowels or consonants with another cluster of the same class.

No actual phonology or lexicology behind the method.
A mutated word may happen to be real or unreadable.
"""

import random
import re


# clusters taken from https://en.wikipedia.org/wiki/English_orthography

VOWL_CLUSTERS = [
    'a',
    'aa',
    'ae',
    'ai',
    'au',
    'au',
    'aw',
    'ay',
    'e',
    'ea',
    'eau',
    'ee',
    'ei',
    'ey',
    'eo',
    'eu',
    'eue',
    'ew',
    'ewe',
    'ieo',
    'iew',
    'i',
    'ie',
    'o',
    'oa',
    'oe',
    'oeu',
    'oi',
    'oo',
    'ou',
    'ow',
    'oy',
    'u',
    'ue',
    'ui',
    'uu',
    'uy',
    'y',
]

CONS_CLUSTERS = [
    'b',
    'bb',
    'c',
    'cc',
    'ch',
    'ck',
    'd',
    'dd',
    'dh',
    'dg',
    'f',
    'ff',
    'g',
    'gg',
    'gh',
    'h',
    'j',
    'k',
    'kk',
    'kh',
    'l',
    'll',
    'm',
    'mm',
    'n',
    'nn',
    'ng',
    'p',
    'pp',
    'ph',
    'pph',
    'q',
    'r',
    'rr',
    'rh',
    'rrh',
    's',
    'sc',
    'sch',
    'sh',
    'ss',
    'sw',
    't',
    'tt',
    'tch',
    'th',
    'v',
    'vv',
    'w',
    'wh',
    'wr',
    'x',
    'xc',
    'xh',
    'z',
    'zz',
]


# sort by length to make '|' work greedy
VOWL_CLUSTERS.sort(key=lambda c: -len(c))
CONS_CLUSTERS.sort(key=lambda c: -len(c))


def make_re(clusters):
    return re.compile("(" + "|".join(clusters) + ")")


CLUSTER_re = make_re(VOWL_CLUSTERS + CONS_CLUSTERS)


def fragmentize_word(word):
    """Split word into fragments of clustered letters"""
    word = word.lower()
    return [f for f in CLUSTER_re.split(word) if f != ""]


def wordize(frags):
    """Reverse fragmentation"""
    return "".join(frags)


def count_class(frags, clusters):
    """Count number of fragments of the same class"""
    return sum([f in clusters for f in frags])


def count_syllables(word: str):
    """Approximately count number of syllables"""
    word = word.rstrip('e')
    return count_class(fragmentize_word(word), VOWL_CLUSTERS)


def classify_frag(frag):
    """Return class of a fragment or None"""
    if frag in VOWL_CLUSTERS:
        return VOWL_CLUSTERS
    if frag in CONS_CLUSTERS:
        return CONS_CLUSTERS


def mutate_frag(frag):
    """Replace fragment with another from the same class"""
    clusters = classify_frag(frag)
    assert clusters is not None
    clusters = clusters.copy()
    clusters.remove(frag)
    return random.choice(clusters)


def mutate_word(word):
    """Mutate random fragment of a word
    Example:
        >>> mutate_word("lexical"), mutate_word("decision"), mutate_word("task")
        ('lexicah', 'deciseauon', 'tavk')
    """
    frags = fragmentize_word(word)
    i = random.randint(0, len(frags) - 1)
    frags[i] = mutate_frag(frags[i])
    return wordize(frags)


def shuffle_word(word):
    """Shuffle all fragments in the middle of word
    Example:
        >>> shuffle_word("lexical"), shuffle_word("decision"), shuffle_word("task")
        ('lxceail', 'dioecisn', 'tsak')
    """
    frags = fragmentize_word(word)
    if len(frags) < 4:
        return word
    mid = frags[1:-1]
    random.shuffle(mid)
    frags[1:-1] = mid
    return wordize(frags)
