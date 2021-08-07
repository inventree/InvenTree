"""
On release, ensure that the release tag matches the InvenTree version number!
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import re
import os
import argparse

if __name__ == '__main__':

    here = os.path.abspath(os.path.dirname(__file__))

    version_file = os.path.join(here, '..', 'InvenTree', 'InvenTree', 'version.py')

    with open(version_file, 'r') as f:

        results = re.findall(r'INVENTREE_SW_VERSION = "(.*)"', f.read())

        if not len(results) == 1:
            print(f"Could not find INVENTREE_SW_VERSION in {version_file}")
            sys.exit(1)

        version = results[0]

    parser = argparse.ArgumentParser()
    parser.add_argument('tag', help='Version tag', action='store')

    args = parser.parse_args()

    if not args.tag == version:
        print(f"Release tag '{args.tag}' does not match INVENTREE_SW_VERSION '{version}'")
        sys.exit(1)

sys.exit(0)