"""Custom string formatting functions and helpers"""

import re
import string

from django.utils.translation import gettext_lazy as _


def parse_format_string(fmt_string: str) -> dict:
    """Extract formatting information from the provided format string.

    Returns a dict object which contains structured information about the format groups
    """

    groups = string.Formatter().parse(fmt_string)

    info = {}

    for group in groups:
        # Skip any group which does not have a named value
        if not group[1]:
            continue

        info[group[1]] = {
            'format': group[1],
            'prefix': group[0],
        }

    return info


def construct_format_regex(fmt_string: str) -> str:
    r"""Construct a regular expression based on a provided format string

    This function turns a python format string into a regular expression,
    which can be used for two purposes:

    - Ensure that a particular string matches the specified format
    - Extract named variables from a matching string

    This function also provides support for wildcard characters:

    - '?' provides single character matching; is converted to a '.' (period) for regex

    Args:
        fmt_string: A typical format string e.g. "PO-???-{ref:04d}"

    Returns:
        str: A regular expression pattern e.g. ^PO\-...\-(?P<ref>.*)$
    """

    pattern = "^"

    for group in string.Formatter().parse(fmt_string):
        prefix = group[0]
        format = group[1]

        # Escape any special regex characters
        for ch in '+-.*^$%()!\'\":;|\{\}':
            prefix = prefix.replace(ch, f'\\{ch}')

        # Replace ? with single-character match
        prefix = prefix.replace('?', '.')

        pattern += prefix

        # Add a named capture group for the format entry
        if format:
            pattern += f"(?P<{format}>.*)"

    pattern += "$"

    return pattern


def extract_named_group(name: str, value: str, fmt_string: str) -> str:
    """Extract a named value from the provided string, given the provided format string

    Args:
        name: Name of group to extract e.g. 'ref'
        value: Raw string e.g. 'PO-ABC-1234'
        fmt_string: Format pattern e.g. 'PO-???-{ref}

    Returns:
        str: String value of the named group

    Raises:
        ValueError: format string is incorrectly specified, or provided value does not match format string
        NameError: named value does not exist in the format string
        IndexError: named value could not be found in the provided entry
    """

    info = parse_format_string(fmt_string)

    if name not in info.keys():
        raise ValueError(_(f"Value '{name}' does not appear in pattern format"))

    # Construct a regular expression for matching against the provided format string
    # Note: This will raise a ValueError if 'fmt_string' is incorrectly specified
    pattern = construct_format_regex(fmt_string)

    # Run the regex matcher against the raw string
    result = re.match(pattern, value)

    if not result:
        raise ValueError(_("Provided value does not match required pattern: ") + fmt_string)

    # And return the value we are interested in
    # Note: This will raise an IndexError if the named group was not matched
    return result.group(name)
