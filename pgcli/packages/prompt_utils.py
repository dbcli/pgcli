# -*- coding: utf-8 -*-


import sys
import click
from .parseutils import is_destructive


def confirm_destructive_query(queries):
    """Check if the query is destructive and prompts the user to confirm.

    Returns:
    * None if the query is non-destructive or we can't prompt the user.
    * True if the query is destructive and the user wants to proceed.
    * False if the query is destructive and the user doesn't want to proceed.

    """
    prompt_text = ("You're about to run a destructive command.\n"
                   "Do you want to proceed? (y/n)")
    if is_destructive(queries) and sys.stdin.isatty():
        return prompt(prompt_text, type=bool)


def confirm(*args, **kwargs):
    """Prompt for confirmation (yes/no) and handle any abort exceptions."""
    try:
        return click.confirm(*args, **kwargs)
    except click.Abort:
        return False


def prompt(*args, **kwargs):
    """Prompt the user for input and handle any abort exceptions."""
    try:
        return click.prompt(*args, **kwargs)
    except click.Abort:
        return False
