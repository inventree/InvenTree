[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Build Status](https://travis-ci.org/inventree/InvenTree.svg?branch=master)](https://travis-ci.org/inventree/InvenTree) [![Documentation Status](https://readthedocs.org/projects/inventree/badge/?version=latest)](https://inventree.readthedocs.io/en/latest/?badge=latest) [![Coverage Status](https://coveralls.io/repos/github/inventree/InvenTree/badge.svg)](https://coveralls.io/github/inventree/InvenTree)

# InvenTree 
InvenTree is an open-source Inventory Management System which provides powerful low-level stock control and part tracking. The core of the InvenTree system is a Python/Django database backend which provides an admin interface (web-based) and a JSON API for interaction with external interfaces and applications.

InvenTree is designed to be lightweight and easy to use for SME or hobbyist applications, where many existing stock management solutions are bloated and cumbersome to use. Updating stock is a single-action procses and does not require a complex system of work orders or stock transactions. 

However, complex business logic works in the background to ensure that stock tracking history is maintained, and users have ready access to stock level information.

## User Documentation

**TODO:** User documentation will be provided on a linked ```.github.io``` site, and will document the various InvenTree functionality

## Code Documentation

For project code documentation, refer to the online [documentation](http://inventree.readthedocs.io/en/latest/) (auto-generated)


## Getting Started

It is recommended to set up a clean Python 3.4+ virtual environment first:
`mkdir ~/.env && python3 -m venv ~/.env/InvenTree && source ~/.env/InvenTree/bin/activate`

A makefile is provided for project configuration:

### Install

Run `make install` to ensure that all required pip packages are installed (see `requirements.txt`). This step will also generate a `SECRET_KEY.txt` file (unless one already exists) for Django authentication.

### Migrate

Run `make migrate` to perform all pending database migrations to ensure the database schema is up to date. 

**Note:** Run this step once after `make install` to create the initial empty database.

### Superuser

Run `make superuser` to create an admin account for the database

### Launch Development Server

Run `python InvenTree/manage.py runserver` to launch a (development / debug) server. InvenTree can be then accessed via a web browser at `http://127.0.0.1:8000`

### Test

Run `make test` to run all code tests

### Style

Run `make style` to check the codebase against PEP coding standards (uses Flake)

## Contributing

### Testing

Any new functionality should be submitted with matching test cases (using the Django testing framework). Tests should at bare minimum ensure that any new Python code is covered by the integrated coverage testing. Tests can be run using `make test`.

### Coding Style

All Python code should conform to the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide. Run `make style` which will compare all source (.py) files against the PEP 8 style. 
