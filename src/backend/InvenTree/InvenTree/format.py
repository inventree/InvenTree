"""Custom string formatting functions and helpers."""

import re
import string
from typing import Optional

from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from babel import Locale
from babel.numbers import parse_pattern
from djmoney.money import Money


def parse_format_string(fmt_string: str) -> dict:
    """Extract formatting information from the provided format string.

    Returns a dict object which contains structured information about the format groups
    """
    groups = string.Formatter().parse(fmt_string)

    info = {}

    seen_groups = set()

    for group in groups:
        # Skip any group which does not have a named value
        if not group[1]:
            continue

        name = group[1]

        # Check for duplicate named groups
        if name in seen_groups:
            raise ValueError(f"Duplicate group '{name}'")
        else:
            seen_groups.add(name)

        info[group[1]] = {'format': group[1], 'prefix': group[0]}

    return info


def construct_format_regex(fmt_string: str) -> str:
    r"""Construct a regular expression based on a provided format string.

    This function turns a python format string into a regular expression,
    which can be used for two purposes:

    - Ensure that a particular string matches the specified format
    - Extract named variables from a matching string

    This function also provides support for wildcard characters:

    - '?' provides single character matching; is converted to a '.' (period) for regex
    - '#' provides single digit matching; is converted to '\d'

    Args:
        fmt_string: A typical format string e.g. "PO-???-{ref:04d}"

    Returns:
        str: A regular expression pattern e.g. ^PO\-...\-(?P<ref>.*)$

    Raises:
        ValueError: Format string is invalid
    """
    pattern = '^'

    for group in string.Formatter().parse(fmt_string):
        prefix = group[0]  # Prefix (literal text appearing before this group)
        name = group[1]  # Name of this format variable
        _fmt = group[2]  # Format specifier e.g :04d

        rep = [
            '+',
            '-',
            '.',
            '{',
            '}',
            '(',
            ')',
            '^',
            '$',
            '~',
            '!',
            '@',
            ':',
            ';',
            '|',
            "'",
            '"',
        ]

        # Escape any special regex characters
        for ch in rep:
            prefix = prefix.replace(ch, '\\' + ch)

        # Replace ? with single-character match
        prefix = prefix.replace('?', '.')

        # Replace # with single-digit match
        prefix = prefix.replace('#', r'\d')

        pattern += prefix

        # Add a named capture group for the format entry
        if name:
            # Check if integer values are required
            c = '\\d' if _fmt.endswith('d') else '.'

            # Specify width
            # TODO: Introspect required width
            w = '+'

            # replace invalid regex group name '?' with a valid name
            if name == '?':
                name = 'wild'

            pattern += f'(?P<{name}>{c}{w})'

    pattern += '$'

    return pattern


def validate_string(value: str, fmt_string: str) -> str:
    """Validate that the provided string matches the specified format.

    Args:
        value: The string to be tested e.g. 'SO-1234-ABC',
        fmt_string: The required format e.g. 'SO-{ref}-???',

    Returns:
        bool: True if the value matches the required format, else False

    Raises:
        ValueError: The provided format string is invalid
    """
    pattern = construct_format_regex(fmt_string)

    result = re.match(pattern, value)

    return result is not None


def extract_named_group(name: str, value: str, fmt_string: str) -> str:
    """Extract a named value from the provided string, given the provided format string.

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

    if name not in info:
        raise NameError(_(f"Value '{name}' does not appear in pattern format"))

    # Construct a regular expression for matching against the provided format string
    # Note: This will raise a ValueError if 'fmt_string' is incorrectly specified
    pattern = construct_format_regex(fmt_string)

    # Run the regex matcher against the raw string
    result = re.match(pattern, value)

    if not result:
        raise ValueError(
            _('Provided value does not match required pattern: ') + fmt_string
        )

    # And return the value we are interested in
    # Note: This will raise an IndexError if the named group was not matched
    return result.group(name)


def format_money(
    money: Money,
    decimal_places: Optional[int] = None,
    fmt: Optional[str] = None,
    include_symbol: bool = True,
) -> str:
    """Format money object according to the currently set local.

    Args:
        money (Money): The money object to format
        decimal_places (int): Number of decimal places to use
        fmt (str): Format pattern according LDML / the babel format pattern syntax (https://babel.pocoo.org/en/latest/numbers.html)

    Returns:
        str: The formatted string

    Raises:
        ValueError: format string is incorrectly specified
    """
    language = (None) or settings.LANGUAGE_CODE
    locale = Locale.parse(translation.to_locale(language))
    if fmt:
        pattern = parse_pattern(fmt)
    else:
        pattern = locale.currency_formats['standard']
        if decimal_places is not None:
            pattern.frac_prec = (decimal_places, decimal_places)

    result = pattern.apply(
        money.amount,
        locale,
        currency=money.currency.code if include_symbol else '',
        currency_digits=decimal_places is None,
        decimal_quantization=decimal_places is not None,
    )

    return result
