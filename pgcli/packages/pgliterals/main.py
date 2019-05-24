import os
import json

root = os.path.dirname(__file__)
literal_file = os.path.join(root, "pgliterals.json")

with open(literal_file) as f:
    literals = json.load(f)


def get_literals(literal_type, type_=tuple):
    # Where `literal_type` is one of 'keywords', 'functions', 'datatypes',
    # returns a tuple of literal values of that type.

    return type_(literals[literal_type])
