"""
This script calculates translation coverage for various languages
"""

import json
import os
import sys


def calculate_coverage(filename):
    """
    Calculate translation coverage for a .po file
    """

    with open(filename, 'r') as f:
        lines = f.readlines()

    lines_count = 0
    lines_covered = 0
    lines_uncovered = 0

    for line in lines:

        if line.startswith("msgid "):
            lines_count += 1

        elif line.startswith("msgstr"):
            if line.startswith('msgstr ""') or line.startswith("msgstr ''"):
                lines_uncovered += 1
            else:
                lines_covered += 1

    # Return stats for the file
    return (lines_count, lines_covered, lines_uncovered)


if __name__ == '__main__':

    MY_DIR = os.path.dirname(os.path.realpath(__file__))
    LC_DIR = os.path.abspath(os.path.join(MY_DIR, '..', 'locale'))
    STAT_FILE = os.path.abspath(os.path.join(MY_DIR, '..', 'InvenTree/locale_stats.json'))

    locales = {}
    locales_perc = {}

    verbose = '-v' in sys.argv

    for locale in os.listdir(LC_DIR):
        path = os.path.join(LC_DIR, locale)
        if os.path.exists(path) and os.path.isdir(path):

            locale_file = os.path.join(path, 'LC_MESSAGES', 'django.po')

            if os.path.exists(locale_file) and os.path.isfile(locale_file):
                locales[locale] = locale_file

    if verbose:
        print("-" * 16)

    percentages = []

    for locale in locales.keys():
        locale_file = locales[locale]
        stats = calculate_coverage(locale_file)

        (total, covered, uncovered) = stats

        if total > 0:
            percentage = int(covered / total * 100)
        else:
            percentage = 0

        if verbose:
            print(f"| {locale.ljust(4, ' ')} : {str(percentage).rjust(4, ' ')}% |")

        locales_perc[locale] = percentage

        percentages.append(percentage)

    if verbose:
        print("-" * 16)

    # write locale stats
    with open(STAT_FILE, 'w') as target:
        json.dump(locales_perc, target)

    if len(percentages) > 0:
        avg = int(sum(percentages) / len(percentages))
    else:
        avg = 0

    print(f"InvenTree translation coverage: {avg}%")
