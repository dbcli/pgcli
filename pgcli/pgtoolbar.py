from pkg_resources import packaging

import prompt_toolkit
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.application import get_app

parse_version = packaging.version.parse

vi_modes = {
    InputMode.INSERT: "I",
    InputMode.NAVIGATION: "N",
    InputMode.REPLACE: "R",
    InputMode.INSERT_MULTIPLE: "M",
}
if parse_version(prompt_toolkit.__version__) >= parse_version("3.0.6"):
    vi_modes[InputMode.REPLACE_SINGLE] = "R"


def _get_vi_mode():
    return vi_modes[get_app().vi_state.input_mode]


def create_toolbar_tokens_func(pgcli):
    """Return a function that generates the toolbar tokens."""

    def get_toolbar_tokens():
        result = []
        result.append(("class:bottom-toolbar", " "))

        if pgcli.completer.smart_completion:
            result.append(("class:bottom-toolbar.on", "[F2] Smart Completion: ON  "))
        else:
            result.append(("class:bottom-toolbar.off", "[F2] Smart Completion: OFF  "))

        if pgcli.multi_line:
            if pgcli.multiline_mode == "safe":
                result.append(("class:bottom-toolbar.on", "[F3] Multiline: ON (;)  "))
            else:
                result.append(
                    ("class:bottom-toolbar.on", "[F3] Multiline: ON (alt ⏎)  ")
                )
        else:
            result.append(("class:bottom-toolbar.off", "[F3] Multiline: OFF  "))

        if pgcli.vi_mode:
            result.append(
                ("class:bottom-toolbar", "[F4] Vi-mode (" + _get_vi_mode() + ")  ")
            )
        else:
            result.append(("class:bottom-toolbar", "[F4] Emacs-mode  "))

        if pgcli.explain_mode:
            result.append(("class:bottom-toolbar.on", "[F5] Explain: ON  "))
        else:
            result.append(("class:bottom-toolbar.off", "[F5] Explain: OFF  "))

        if pgcli.autocommit:
            result.append(("class:bottom-toolbar.on", "[F6] Autocommit: ON  "))
        else:
            result.append(("class:bottom-toolbar.off", "[F6] Autocommit: OFF  "))

        if pgcli.completion_refresher.is_refreshing():
            result.append(("class:bottom-toolbar", "<REFRESHING>"))
        elif pgcli.pgexecute.failed_transaction():
            result.append(("class:bottom-toolbar.transaction.failed", "<TRANSACTION>"))
        elif pgcli.pgexecute.valid_transaction():
            result.append(("class:bottom-toolbar.transaction.valid", "<TRANSACTION>"))

        return result

    return get_toolbar_tokens
