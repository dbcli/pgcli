# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import os
import codecs


def read_fixture_lines(filename):
    """
    Read lines of text from file.
    :param filename: string name
    :return: list of strings
    """
    lines = []
    for line in codecs.open(filename, 'rb', encoding='utf-8'):
        lines.append(line.strip())
    return lines


def read_fixture_files():
    """Read all files inside fixture_data directory."""
    current_dir = os.path.dirname(__file__)
    fixture_dir = os.path.join(current_dir, 'fixture_data/')
    print('reading fixture data: {}'.format(fixture_dir))
    fixture_dict = {}
    for filename in os.listdir(fixture_dir):
        if filename not in ['.', '..']:
            fullname = os.path.join(fixture_dir, filename)
            fixture_dict[filename] = read_fixture_lines(fullname)

    return fixture_dict
