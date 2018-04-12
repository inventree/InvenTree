[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Build Status](https://travis-ci.org/inventree/InvenTree.svg?branch=master)](https://travis-ci.org/inventree/InvenTree) 

# InvenTree 
InvenTree is an open-source Inventory Management System which provides powerful low-level stock control and part tracking. The core of the InvenTree system is a Python/Django database backend which provides an admin interface (web-based) and a JSON API for interaction with external interfaces and applications.

## Installation
It is recommended to set up a clean Python 3.4+ virtual environment first:
`mkdir ~/.env && python3 -m venv ~/.env/InvenTree && source ~/.env/InvenTree/bin/activate`

You can then continue running `make setup` (which will be replaced by a proper setup.py soon). This will do the following:

1. Installs required Python dependencies (requires [pip](https://pypi.python.org/pypi/pip), should be part of your virtual environment by default)
1. Performs initial database setup
1. Updates database tables for all InvenTree components

This command can also be used to update the installation if changes have been made to the database configuration.

To create an initial user account, run the command `make superuser`.

## Documentation
For project code documentation, refer to the online [documentation](http://inventree.readthedocs.io/en/latest/) (auto-generated)

## Coding Style
If you'd like to contribute, install our development dependencies using `make develop`.
All Python code should conform to the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide. Run `make style` which will compare all source (.py) files against the PEP 8 style. Tests can be run using `make test`.
