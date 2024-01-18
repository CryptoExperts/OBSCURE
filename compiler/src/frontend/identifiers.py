"""Some utilities to generate random uniq identifiers"""

import string
import random


all_identifiers = set()
next_counters = dict()

def gen_next_ident(length=6, prefix="t_"):
    """Generates a unique identifier by incrementing an internal counter

    There is one counter per prefix. However, this function will skip
    identifiers that have already been generated.

    parameters/arguments:
      - length: the length of the identifier to generate (excluding the prefix)
      - prefix: a prefix to prepend to the final identifier (could be for instance
                "tmp_" or "iterator_")

    """
    counter = next_counters.get(prefix, 0)
    ident = "" + prefix + str(counter)
    while ident in all_identifiers:
        counter += 1
        ident = "" + prefix + str(counter)
    counter += 1
    next_counters[prefix] = counter
    all_identifiers.add(ident)
    return ident


def gen_random_ident(length=6, prefix="t_", alphabet=string.ascii_letters + string.digits):
    """Generates a random unique identifier

    parameters/arguments:
      - length: the length of the identifier to generate (excluding the prefix)
      - prefix: a prefix to prepend to the final identifier (could be for instance
                "tmp_" or "iterator_")
      - alphabet: the alphabet to choose the characters of the identifier from
    """
    ident = prefix + ''.join(random.choice(alphabet) for _ in range(length))
    while ident in all_identifiers:
        ident = prefix + ''.join(random.choice(alphabet) for _ in range(length))
    all_identifiers.add(ident)
    return ident


def add_ident(ident):
    """Adds a new identifier to the internal memory"""
    all_identifiers.add(ident)

def ident_exists(ident):
    """Checks if an identifier exists in the internal memory"""
    return ident in all_identifiers

def reset():
    global all_identifiers, next_counters
    all_identifiers = set()
    next_counters = dict()
