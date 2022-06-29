"""Custom string formatting functions and helpers"""

import string


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
