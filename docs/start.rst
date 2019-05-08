Getting Started Guide
=====================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

To install a complete development environment for InvenTree, follow the steps presented below.

A makefile in the root directory provides shortcuts for the installation process, and can also be very useful during development.

Installation
------------

All packages required to develop and test InvenTree can be installed via pip package manager. Package requirements can be found in ``requirements.txt``.

To setup the InvenTree environment, run the command

``make install``

which performs the following actions:

* Installs all required Python packages using pip package manager
* Generates a SECREY_KEY file required for the django authentication framework

Superuser Account
-----------------

Run ``make superuser`` to create a superuser account, required for initial system login.

Run Development Server
----------------------

Run ``python InvenTree/manage.py runserver`` to launch a development server. This will launch the InvenTree web interface at ``127.0.0.1:8000``. For other options refer to the `django docs <https://docs.djangoproject.com/en/2.2/ref/django-admin/>`_.

Database Migrations
-------------------

Whenever a change is made to the underlying database schema, database migrations must be performed. Call ``make migrate`` to run any outstanding database migrations.

Development and Testing
-----------------------

Other shorthand functions are provided for the development and testing process:

* ``make test`` - Run all unit tests
* ``make coverage`` - Run all unit tests and generate code coverage report
* ``make style`` - Check Python codebase against PEP coding standards (using Flake)
* ``make documentation`` - Generate this documentation