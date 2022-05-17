"""
Test that the "translated" javascript files to not contain template tags
which need to be determined at "run time".

This is because the "translated" javascript files are compiled into the "static" directory.

They should only contain template tags that render static information.
"""

import sys
import re
import os
import pathlib

here = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.abspath(os.path.join(here, '..', 'InvenTree', 'templates'))

# We only care about the 'translated' files
js_i18n_dir = os.path.join(template_dir, 'js', 'translated')
js_dynamic_dir = os.path.join(template_dir, 'js', 'dynamic')

errors = 0

print("=================================")
print("Checking static javascript files:")
print("=================================")


def check_invalid_tag(data):

    pattern = r"{%(\w+)"

    err_count = 0

    for idx, line in enumerate(data):

        results = re.findall(pattern, line)

        for result in results:
            err_count += 1

            print(f" - Error on line {idx+1}: %{{{result[0]}")

    return err_count


def check_prohibited_tags(data):

    allowed_tags = [
        'if',
        'elif',
        'else',
        'endif',
        'for',
        'endfor',
        'trans',
        'load',
        'include',
        'url',
    ]

    pattern = r"{% (\w+)\s"

    err_count = 0

    has_trans = False

    for idx, line in enumerate(data):

        for tag in re.findall(pattern, line):

            if tag not in allowed_tags:
                print(f" > Line {idx+1} contains prohibited template tag '{tag}'")
                err_count += 1

            if tag == 'trans':
                has_trans = True

    if not has_trans:
        print(" > file is missing 'trans' tags")
        err_count += 1

    return err_count


for filename in pathlib.Path(js_i18n_dir).rglob('*.js'):

    print(f"Checking file 'translated/{os.path.basename(filename)}':")

    with open(filename, 'r') as js_file:
        data = js_file.readlines()

    errors += check_invalid_tag(data)
    errors += check_prohibited_tags(data)

for filename in pathlib.Path(js_dynamic_dir).rglob('*.js'):

    print(f"Checking file 'dynamic/{os.path.basename(filename)}':")

    # Check that the 'dynamic' files do not contains any translated strings
    with open(filename, 'r') as js_file:
        data = js_file.readlines()

    pattern = r'{% trans '

    err_count = 0

    for idx, line in enumerate(data):

        results = re.findall(pattern, line)

        if len(results) > 0:
            errors += 1

            print(f" > prohibited {{% trans %}} tag found at line {idx + 1}")

if errors > 0:
    print(f"Found {errors} incorrect template tags")

sys.exit(errors)
