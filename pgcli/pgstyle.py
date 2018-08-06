from __future__ import unicode_literals

import logging

import pygments.styles
from pygments.token import string_to_tokentype, Token
from pygments.style import Style as PygmentsStyle
from pygments.util import ClassNotFound
from prompt_toolkit.styles.pygments import style_from_pygments_cls, style_from_pygments_dict
from prompt_toolkit.styles import merge_styles, Style

logger = logging.getLogger(__name__)

token_to_prompt_style = {
    Token.Menu.Completions: 'completion-menu',
    Token.Menu.Completions.Completion: 'completion-menu.completion',
    Token.Menu.Completions.Completion.Current: 'completion-menu.completion.current',
    Token.Menu.Completions.Meta: 'completion-menu.meta.completion',
    Token.Menu.Completions.MultiColumnMeta: 'completion-menu.multi-column-meta',
    Token.Menu.Completions.ProgressBar: 'progress-bar',
}

def parse_pygments_style(token_name, style_object, style_dict):
    """Parse token type and style string.

    :param token_name: str name of Pygments token. Example: "Token.String"
    :param style_object: pygments.style.Style instance to use as base
    :param style_dict: dict of token names and their styles, customized to this cli
    """
    token_type = string_to_tokentype(token_name)
    try:
        other_token_type = string_to_tokentype(style_dict[token_name])
        return token_type, style_object.styles[other_token_type]
    except AttributeError as err:
        return token_type, style_dict[token_name]


def style_factory(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name)
    except ClassNotFound:
        style = pygments.styles.get_style_by_name('native')

    pygments_styles = {}
    prompt_styles = []
    # prompt-toolkit used pygments tokens for styling before, switched to style names in 2.0.
    # Convert some removed token types to new style names, for backwards compatibility.
    for token in cli_style:
        if token.startswith('Token.'):
            # treat as pygments token (1.0)
            token_type, style_value = parse_pygments_style(token, style, cli_style)
            if token_type in token_to_prompt_style:
                prompt_style = token_to_prompt_style[token_type]
                prompt_styles.append((prompt_style, style_value))
            else:
                pygments_styles[token_type] = style_value
        else:
            # treat as prompt style name (2.0). See default style names here:
            # https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/prompt_toolkit/styles/defaults.py
            prompt_styles.append((token, cli_style[token]))

    override_style = Style([('bottom-toolbar', 'noreverse')])
    return merge_styles([
        style_from_pygments_cls(style),
        style_from_pygments_dict(pygments_styles),
        override_style,
        Style(prompt_styles)
    ])


def style_factory_output(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name).styles
    except ClassNotFound:
        style = pygments.styles.get_style_by_name('native').styles

    for token in cli_style:
        if token.startswith('Token.'):
            token_type, style_value = parse_pygments_style(token, style, cli_style)
            style.update({token_type: style_value})
        else:
            # TODO: cli helpers are going to need to know how to handle
            # prompt-toolkit Style, instead of Pygments Style.
            logger.error('Unhandled style: %s', token)

    class OutputStyle(PygmentsStyle):
        default_style = ""
        styles = style

    return OutputStyle
