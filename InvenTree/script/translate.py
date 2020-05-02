"""
This script is used to simplify the translation process.

Django provides a framework for working out which strings are "translatable",
and these strings are then dumped in a file under InvenTree/locale/<lang>/LC_MESSAGES/django.po

This script presents the translator with a list of strings which have not yet been translated,
allowing for a simpler and quicker translation process.

If a string translation needs to be updated, this will still need to be done manually,
by editing the appropriate .po file.

"""

import argparse
import os
import sys


def manually_translate_file(filename):
    """
    Manually translate a .po file.
    Present any missing translation strings to the translator,
    and write their responses back to the file.
    """

    print("here we go!", filename)


if __name__ == '__main__':

    MY_DIR = os.path.dirname(os.path.realpath(__file__))
    LOCALE_DIR = os.path.join(MY_DIR, '..', 'locale')

    if not os.path.exists(LOCALE_DIR):
        print("Error: {d} does not exist!".format(d=LOCALE_DIR))
        sys.exit(1)

    parser = argparse.ArgumentParser(description="InvenTree Translation Helper")

    parser.add_argument('language', help='Language code', action='store')

    args = parser.parse_args()

    language = args.language

    LANGUAGE_DIR = os.path.abspath(os.path.join(LOCALE_DIR, language))

    # Check that a locale directory exists for the given language!
    if not os.path.exists(LANGUAGE_DIR):
        print("Error: Locale directory for language '{l}' does not exist".format(l=language))
        sys.exit(1)

    # Check that a .po file exists for the given language!
    PO_FILE = os.path.join(LANGUAGE_DIR, 'LC_MESSAGES', 'django.po')

    if not os.path.exists(PO_FILE):
        print("Error: File '{f}' does not exist".format(f=PO_FILE))
        sys.exit(1)

    # Ok, now we run the user through the translation file
    manually_translate_file(PO_FILE)
    