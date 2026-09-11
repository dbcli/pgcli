import shutil
import os
import platform
import configparser
from os.path import expanduser, exists, dirname
import re
from typing import TextIO


class ConfigSection(dict):
    """A case-sensitive config section with ConfigObj's typed accessors."""

    def as_bool(self, key):
        value = self[key].lower()
        if value in ("1", "yes", "true", "on"):
            return True
        if value in ("0", "no", "false", "off"):
            return False
        raise ValueError(f"Not a boolean: {self[key]}")

    def as_int(self, key):
        return int(self[key])

    def as_list(self, key):
        value = self[key]
        if not value:
            return [""]
        if value == ",":
            return []
        if isinstance(value, ConfigValue) and value.quoted:
            return [str(value)]
        items = []
        start = 0
        quote = None
        for index, character in enumerate(value):
            if character in "\"'" and not _is_escaped(value, index):
                quote = None if quote == character else character if quote is None else quote
            elif character == "," and quote is None:
                items.append(str(_unquote(value[start:index])))
                start = index + 1
        items.append(str(_unquote(value[start:])))
        if value.endswith(","):
            items.pop()
        return items


class ConfigValue(str):
    """A string that remembers when its entire source value was quoted."""

    def __new__(cls, value, quoted=False):
        instance = super().__new__(cls, value)
        instance.quoted = quoted
        return instance


class PgcliConfig(dict):
    """The subset of ConfigObj's interface used by pgcli and pgspecial."""

    def __init__(self, filename, sections=None):
        super().__init__(sections or {})
        self.filename = filename
        self._original = {name: dict(section) for name, section in self.items()}

    def write(self):
        """Update values in place while retaining user comments and layout."""
        try:
            with open(self.filename, encoding="utf-8") as source:
                lines = source.readlines()
        except FileNotFoundError:
            lines = []

        output = []
        seen_sections = set()
        section = None
        seen_options = set()
        skip_continuations = False

        def append_missing_options():
            if section not in self:
                return
            for key, value in self[section].items():
                if key not in seen_options:
                    output.extend(_format_option(key, value))

        line_number = 0
        while line_number < len(lines):
            line = lines[line_number]
            section_match = re.match(r"\s*\[([^]]+)\]\s*(?:[#;].*)?$", line)
            if section_match:
                append_missing_options()
                section = section_match.group(1)
                seen_sections.add(section)
                seen_options = set()
                skip_continuations = False
                output.append(line)
                line_number += 1
                continue

            if skip_continuations and line.startswith((" ", "\t")) and line.strip() and not line.lstrip().startswith(("#", ";")):
                line_number += 1
                continue
            skip_continuations = False

            option_match = re.match(r"(\s*)([^#;\s][^:=]*?)(\s*[=:]\s*)(.*?)(\r?\n)?$", line)
            if section in self and option_match:
                key = option_match.group(2).rstrip()
                value_end, triple_quoted_comment = _triple_quoted_value_end(lines, line_number, option_match.group(4))
                if key in self[section]:
                    seen_options.add(key)
                    if self[section][key] == self._original.get(section, {}).get(key):
                        output.extend(lines[line_number : value_end + 1])
                    else:
                        _, inline_comment = _split_value_comment(option_match.group(4))
                        inline_comment = triple_quoted_comment or inline_comment
                        output.extend(
                            _format_option(
                                key,
                                self[section][key],
                                option_match.group(1),
                                option_match.group(3),
                                inline_comment,
                            )
                        )
                        skip_continuations = True
                else:
                    if triple_quoted_comment:
                        output.append(f"{option_match.group(1)}{triple_quoted_comment.lstrip()}\n")
                    skip_continuations = True
                # A missing key was deliberately deleted.
                line_number = value_end + 1
                continue
            output.append(line)
            line_number += 1

        append_missing_options()
        for name, values in self.items():
            if name in seen_sections:
                continue
            if output and output[-1].strip():
                output.append("\n")
            output.append(f"[{name}]\n")
            for key, value in values.items():
                output.extend(_format_option(key, value))

        with open(self.filename, "w", encoding="utf-8", newline="") as destination:
            destination.writelines(output)
        self._original = {name: dict(values) for name, values in self.items()}


def _triple_quoted_value_end(lines, start, first_value):
    """Return the last source line and trailing comment for a triple-quoted value."""
    stripped = first_value.lstrip()
    quote = stripped[:3]
    if quote not in ('"""', "'''"):
        return start, ""

    for line_number in range(start, len(lines)):
        value = stripped[3:] if line_number == start else lines[line_number]
        closing = value.find(quote)
        if closing == -1:
            continue
        suffix = value[closing + 3 :].rstrip("\r\n")
        match = re.fullmatch(r"[ \t]*(#[^\r\n]*)?", suffix)
        if match:
            return line_number, suffix if match.group(1) else ""
    return start, ""


def _format_option(key, value, indent="", separator=" = ", inline_comment=""):
    value = str(value)
    if "\n" in value or "\r" in value:
        quote = next((candidate for candidate in ('"""', "'''") if candidate not in value), None)
        if quote is None:
            raise ValueError(f"Cannot serialize {key!r}: value contains both triple-quote delimiters")
        return [f"{indent}{key}{separator}{quote}{value}{quote}{inline_comment}\n"]
    if "#" in value or value != value.strip():
        if "'" not in value:
            value = f"'{value}'"
        elif '"' not in value:
            value = f'"{value}"'
        else:
            value = f'"""{value}"""'
    elif "\n" not in value and "\r" not in value and len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        outer_quote = '"' if value[0] == "'" else "'"
        value = f"{outer_quote}{value}{outer_quote}"
    parts = value.splitlines() or [""]
    lines = [f"{indent}{key}{separator}{parts[0]}{inline_comment}\n"]
    lines.extend(f"{indent}\t{part}\n" for part in parts[1:])
    return lines


def _read_config(filename):
    parser = configparser.RawConfigParser(
        delimiters=("=",),
        comment_prefixes=("#", ";"),
        inline_comment_prefixes=None,
        interpolation=None,
        strict=True,
        empty_lines_in_values=False,
        default_section=None,
    )
    parser.optionxform = str
    try:
        with open(expanduser(filename), encoding="utf-8") as source:
            contents = source.read()
    except FileNotFoundError:
        return {}
    normalized, multiline_values = _extract_triple_quoted_values(contents, filename)
    parser.read_string(normalized, source=filename)
    return {
        name: ConfigSection({
            key: multiline_values.get(str(parsed := _unquote(_split_value_comment(value)[0])), parsed)
            for key, value in parser.items(name, raw=True)
        })
        for name in parser.sections()
    }


def _extract_triple_quoted_values(contents, source):
    """Hide ConfigObj multiline values from configparser and retain them exactly."""
    pattern = re.compile(
        r"^([ \t]*[^#;\s][^=\r\n]*?[ \t]*=[ \t]*)(\"\"\"|''')(.*?)\2([ \t]*(?:#[^\r\n]*)?)$",
        re.MULTILINE | re.DOTALL,
    )
    values = {}
    counter = 0

    def replace(match):
        nonlocal counter
        while True:
            placeholder = f"__pgcli_multiline_{counter}__"
            counter += 1
            if placeholder not in contents:
                break
        values[placeholder] = ConfigValue(match.group(3), quoted=True)
        return f'{match.group(1)}"{placeholder}"{match.group(4)}'

    normalized = pattern.sub(replace, contents)
    _validate_supported_structure(normalized, source)
    return normalized, values


def _validate_supported_structure(contents, source):
    """Reject ConfigObj structures that pgclirc has never needed."""
    section_seen = False
    for line_number, line in enumerate(contents.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ";")):
            continue
        if re.match(r"^\[\[.*\]\](?:\s*[#;].*)?$", stripped):
            raise ValueError(f"{source}:{line_number}: nested [[sections]] are not supported")
        if re.match(r"^\[[^]]+\](?:\s*[#;].*)?$", stripped):
            section_seen = True
        elif not section_seen and re.match(r"^[^#;\s][^=]*=", stripped):
            raise ValueError(f"{source}:{line_number}: root-level options are not supported")


def _split_value_comment(value):
    stripped = value.lstrip()
    triple_quote = stripped[:3]
    if triple_quote in ('"""', "'''"):
        closing = value.rfind(triple_quote)
        if closing > len(value) - len(stripped):
            suffix = value[closing + 3 :]
            comment = re.fullmatch(r"([ \t]*#[^\r\n]*)(\r?\n.*)?", suffix, re.DOTALL)
            if comment:
                return value[: closing + 3] + (comment.group(2) or ""), comment.group(1)
            return value, ""

    quote = None
    for index, character in enumerate(value):
        if character in "\"'" and not _is_escaped(value, index):
            quote = None if quote == character else character if quote is None else quote
        elif character == "#" and quote is None:
            uncommented = value[:index].rstrip()
            newline = value.find("\n", index)
            if newline == -1:
                return uncommented, value[len(uncommented) :]
            return uncommented + value[newline:], value[len(uncommented) : newline]
    return value, ""


def _is_escaped(value, index):
    """Return whether the character at index follows an odd run of slashes."""
    slashes = 0
    index -= 1
    while index >= 0 and value[index] == "\\":
        slashes += 1
        index -= 1
    return slashes % 2 == 1


def _unquote(value):
    stripped = value.strip()
    if len(stripped) >= 6 and stripped[:3] in ('"""', "'''") and stripped.endswith(stripped[:3]):
        return ConfigValue(stripped[3:-3], quoted=True)
    if len(stripped) >= 2 and stripped[0] in "\"'":
        quote = stripped[0]
        closing = next(
            (index for index in range(1, len(stripped)) if stripped[index] == quote and not _is_escaped(stripped, index)),
            None,
        )
        if closing == len(stripped) - 1:
            return ConfigValue(stripped[1:-1], quoted=True)
    return ConfigValue(stripped)


def config_location():
    if "XDG_CONFIG_HOME" in os.environ:
        return "%s/pgcli/" % expanduser(os.environ["XDG_CONFIG_HOME"])
    elif platform.system() == "Windows":
        return os.getenv("USERPROFILE") + "\\AppData\\Local\\dbcli\\pgcli\\"
    else:
        return expanduser("~/.config/pgcli/")


def load_config(usr_cfg, def_cfg=None):
    usr_cfg = expanduser(usr_cfg)
    if def_cfg:
        sections = _read_config(def_cfg)
        for name, values in _read_config(usr_cfg).items():
            sections.setdefault(name, ConfigSection()).update(values)
    else:
        sections = _read_config(usr_cfg)
    return PgcliConfig(usr_cfg, sections)


def ensure_dir_exists(path):
    parent_dir = expanduser(dirname(path))
    os.makedirs(parent_dir, exist_ok=True)


def write_default_config(source, destination, overwrite=False):
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    ensure_dir_exists(destination)

    shutil.copyfile(source, destination)


def upgrade_config(config, def_config):
    cfg = load_config(config, def_config)
    cfg.write()


def get_config_filename(pgclirc_file=None):
    return pgclirc_file or "%sconfig" % config_location()


def get_config(pgclirc_file=None):
    from pgcli import __file__ as package_root

    package_root = os.path.dirname(package_root)

    pgclirc_file = get_config_filename(pgclirc_file)

    default_config = os.path.join(package_root, "pgclirc")
    write_default_config(default_config, pgclirc_file)

    return load_config(pgclirc_file, default_config)


def get_casing_file(config):
    casing_file = config["main"]["casing_file"]
    if casing_file == "default":
        casing_file = config_location() + "casing"
    return casing_file


def skip_initial_comment(f_stream: TextIO) -> int:
    """
    Initial comment in ~/.pg_service.conf is not always marked with '#'
    which crashes the parser. This function takes a file object and
    "rewinds" it to the beginning of the first section,
    from where on it can be parsed safely

    :return: number of skipped lines
    """
    section_regex = r"\s*\["
    pos = f_stream.tell()
    lines_skipped = 0
    while True:
        line = f_stream.readline()
        if line == "":
            break
        if re.match(section_regex, line) is not None:
            f_stream.seek(pos)
            break
        else:
            pos += len(line)
            lines_skipped += 1
    return lines_skipped
