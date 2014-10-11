from __future__ import unicode_literals, absolute_import
from prompt_toolkit.contrib.regular_languages.compiler import compile

import re


def create_pdb_grammar(pdb_commands):
    """
    Create a compiled grammar for this list of PDB commands.

    (Note: this is an expensive function. Call only when `pdb_commands`
    changes.)
    """
    pdb_commands_re = '|'.join(map(re.escape, pdb_commands))

    def create_grammar(recursive=True):
        return r"""
        \s* (
            (?P<pdb_command>p|pp|whatis)     \s+  (?P<python_code>.*) |
            (?P<pdb_command>enable)          \s+  (?P<disabled_breakpoint>.*) |
            (?P<pdb_command>disable)         \s+  (?P<enabled_breakpoint>.*) |
            (?P<pdb_command>condition)       \s+  [0-9]+  \s+ (?P<python_code>.*)  |
            (?P<pdb_command>ignore)          \s+  (?P<breakpoint>[0-9]+)  \s+ [0-9]+  |
            (?P<pdb_command>commands)        \s+  (?P<breakpoint>[0-9]+)  |
            (?P<pdb_command>alias)           \s+  [^\s]+   \s+  """ + (create_grammar(False) if recursive else '.+') + """
            (?P<pdb_command>unalias)         \s+  (?P<alias_name>.*) |
            (?P<pdb_command>h|help)          \s+  (?P<pdb_command>.*) |

            # For the break command, do autocompletion on file and function names.
            # After the comma, do completion on python code.
            (?P<pdb_command>break|b|tbreak)  \s+
                        (
                                # Break on a <function>
                                (?P<python_function>[^\s:]+)              |

                                # Break on a <file>:<lineno>
                                (?P<python_file>(?![0-9])[^\s:]+):[^\s]+  |

                                # Break on a <lineno>
                                [0-9]+
                        )
                        \s* (, \s* (?P<python_code>.*))? |

            # Known PDB commands (autocompletion & highlighting of all commands)
            (?P<pdb_command>""" + pdb_commands_re + """)  (\s+  .*)? |

            # Starting with exclamation mark -> always Python code.
            !(?P<python_code>.*) |

            # When the input is no valid PDB command, we consider it Python code.
            # (We use negative lookahead to be sure it doesn't start with a pdb
            # command or an exclamation mark.)
            (?P<python_code>(?!(""" + pdb_commands_re + """)(\s+|$))(?!\!).*) |
        ) \s*
        """
    return compile(create_grammar())
