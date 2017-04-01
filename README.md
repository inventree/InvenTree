# InvenTree
Open Source Inventory Management System

[![Build Status](https://travis-ci.org/inventree/InvenTree.svg?branch=master)](https://travis-ci.org/inventree/InvenTree)

## Installation
When first installing InvenTree, initial database configuration must be performed. This is handled by the `install.py` script, which performs the following actions:

1. Installs required django packages (requires [pip](https://pypi.python.org/pypi/pip))
1. Performs initial database setup
1. Updates database tables for all InvenTree components

This script can also be used to update the installation if changes have been made to the database configuration.

To create an initial user account, run the command `python InvenTree/manage.py createsuperuser`

## Documentation
For project code documentation, refer to the online [documentation](http://inventree.readthedocs.io/en/latest/) (auto-generated)

## Coding Style
All python code should conform to the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide. Run the *pep_check.py* script which will compare all source (.py) files against the PEP 8 style.
