import os
root = os.path.dirname(__file__)
literal_names = ['keywords', 'functions', 'datatypes']
__all__ = ['keywords', 'functions', 'datatypes']

for literals in literal_names:
    filepath = os.path.join(root, literals + '.txt')
    with open(filepath) as f:
        globals()[literals] = tuple(f.read().splitlines())
