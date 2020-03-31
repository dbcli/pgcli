import logging

import pygments.styles
from pygments.token import string_to_tokentype, Token
from pygments.style import Style as PygmentsStyle
from pygments.util import ClassNotFound
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.styles import merge_styles, Style

logger = logging.getLogger(__name__)

# map Pygments tokens (ptk 1.0) to class names (ptk 2.0).
TOKEN_TO_PROMPT_STYLE = {
    Token.Menu.Completions.Completion.Current: "completion-menu.completion.current",
    Token.Menu.Completions.Completion: "completion-menu.completion",
    Token.Menu.Completions.Meta.Current: "completion-menu.meta.completion.current",
    Token.Menu.Completions.Meta: "completion-menu.meta.completion",
    Token.Menu.Completions.MultiColumnMeta: "completion-menu.multi-column-meta",
    Token.Menu.Completions.ProgressButton: "scrollbar.arrow",  # best guess
    Token.Menu.Completions.ProgressBar: "scrollbar",  # best guess
    Token.SelectedText: "selected",
    Token.SearchMatch: "search",
    Token.SearchMatch.Current: "search.current",
    Token.Toolbar: "bottom-toolbar",
    Token.Toolbar.Off: "bottom-toolbar.off",
    Token.Toolbar.On: "bottom-toolbar.on",
    Token.Toolbar.Search: "search-toolbar",
    Token.Toolbar.Search.Text: "search-toolbar.text",
    Token.Toolbar.System: "system-toolbar",
    Token.Toolbar.Arg: "arg-toolbar",
    Token.Toolbar.Arg.Text: "arg-toolbar.text",
    Token.Toolbar.Transaction.Valid: "bottom-toolbar.transaction.valid",
    Token.Toolbar.Transaction.Failed: "bottom-toolbar.transaction.failed",
    Token.Output.Header: "output.header",
    Token.Output.OddRow: "output.odd-row",
    Token.Output.EvenRow: "output.even-row",
    Token.Output.Null: "output.null",
    Token.Literal.String: "literal.string",
    Token.Literal.Number: "literal.number",
    Token.Keyword: "keyword",
    Token.Prompt: "prompt",
    Token.Continuation: "continuation",
}

# reverse dict for cli_helpers, because they still expect Pygments tokens.
PROMPT_STYLE_TO_TOKEN = {v: k for k, v in TOKEN_TO_PROMPT_STYLE.items()}


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
    except AttributeError:
        return token_type, style_dict[token_name]


def style_factory(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name)
    except ClassNotFound:
        style = pygments.styles.get_style_by_name("native")

    prompt_styles = []
    # prompt-toolkit used pygments tokens for styling before, switched to style
    # names in 2.0. Convert old token types to new style names, for backwards compatibility.
    for token in cli_style:
        if token.startswith("Token."):
            # treat as pygments token (1.0)
            token_type, style_value = parse_pygments_style(token, style, cli_style)
            if token_type in TOKEN_TO_PROMPT_STYLE:
                prompt_style = TOKEN_TO_PROMPT_STYLE[token_type]
                prompt_styles.append((prompt_style, style_value))
            else:
                # we don't want to support tokens anymore
                logger.error("Unhandled style / class name: %s", token)
        else:
            # treat as prompt style name (2.0). See default style names here:
            # https://github.com/jonathanslenders/python-prompt-toolkit/blob/master/prompt_toolkit/styles/defaults.py
            prompt_styles.append((token, cli_style[token]))

    override_style = Style([("bottom-toolbar", "noreverse")])
    return merge_styles(
        [style_from_pygments_cls(style), override_style, Style(prompt_styles)]
    )


def style_factory_output(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name).styles
    except ClassNotFound:
        style = pygments.styles.get_style_by_name("native").styles

    for token in cli_style:
        if token.startswith("Token."):
            token_type, style_value = parse_pygments_style(token, style, cli_style)
            style.update({token_type: style_value})
        elif token in PROMPT_STYLE_TO_TOKEN:
            token_type = PROMPT_STYLE_TO_TOKEN[token]
            style.update({token_type: cli_style[token]})
        else:
            # TODO: cli helpers will have to switch to ptk.Style
            logger.error("Unhandled style / class name: %s", token)

    class OutputStyle(PygmentsStyle):
        default_style = ""
        styles = style

    return OutputStyle
