from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.application import get_app

vi_modes = {
    InputMode.INSERT: "I",
    InputMode.NAVIGATION: "N",
    InputMode.REPLACE: "R",
    InputMode.INSERT_MULTIPLE: "M",
}
# REPLACE_SINGLE is available in prompt_toolkit >= 3.0.6
if "REPLACE_SINGLE" in {e.name for e in InputMode}:
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
            result.append(("class:bottom-toolbar.on", "[F3] Multiline: ON  "))
        else:
            result.append(("class:bottom-toolbar.off", "[F3] Multiline: OFF  "))

        if pgcli.multi_line:
            if pgcli.multiline_mode == "safe":
                result.append(("class:bottom-toolbar", " ([Esc] [Enter] to execute]) "))
            else:
                result.append(
                    ("class:bottom-toolbar", " (Semi-colon [;] will end the line) ")
                )

        if pgcli.vi_mode:
            result.append(
                ("class:bottom-toolbar", "[F4] Vi-mode (" + _get_vi_mode() + ")  ")
            )
        else:
            result.append(("class:bottom-toolbar", "[F4] Emacs-mode  "))

        if pgcli.explain_mode:
            result.append(("class:bottom-toolbar", "[F5] Explain: ON "))
        else:
            result.append(("class:bottom-toolbar", "[F5] Explain: OFF "))

        if pgcli.pgexecute.failed_transaction():
            result.append(
                ("class:bottom-toolbar.transaction.failed", "     Failed transaction")
            )

        if pgcli.pgexecute.valid_transaction():
            result.append(
                ("class:bottom-toolbar.transaction.valid", "     Transaction")
            )

        if pgcli.completion_refresher.is_refreshing():
            result.append(("class:bottom-toolbar", "     Refreshing completions..."))

        return result

    return get_toolbar_tokens
