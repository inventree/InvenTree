"""
Checks all source files (.py) against PEP8 coding style.
The following rules are ignored:
  - W293 - blank lines contain whitespace
  - E501 - line too long (82 characters)

Run this script before submitting a Pull-Request to check your code.
"""

import subprocess

subprocess.call(['pep8', '--exclude=migrations', '--ignore=W293,E501', 'InvenTree'])
