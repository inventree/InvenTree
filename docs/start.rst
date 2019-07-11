Getting Started Guide
=====================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

To install a complete *development* environment for InvenTree, follow the steps presented below. A production environment will require further work as per the particular application requirements. 

A makefile in the root directory provides shortcuts for the installation process, and can also be very useful during development.

Installation
------------

InvenTree is a Python/Django application and relies on the pip package manager. All packages required to develop and test InvenTree can be installed via pip. Package requirements can be found in ``requirements.txt``.

To setup the InvenTree environment, run the command:

``make install``

which performs the following actions:

* Installs all required Python packages using pip package manager
* Generates a SECREY_KEY file required for the django authentication framework

Install Configuration
---------------------

InvenTree provides a simple default setup which should work *out of the box* for testing and debug purposes. For installation in production environments, further configuration options are available in the ``config.yaml`` configuration file. 

The configuration file provides administrators control over various setup options without digging into the Django ``settings.py`` script. The default setup uses a sqlite database with *DEBUG* mode enabled.

For further information on installation configuration, refer to the `Configuration <config.html>`_ section.

Superuser Account
-----------------

Run ``make superuser`` to create a superuser account, required for initial system login.

Run Development Server
----------------------

Run ``python3 InvenTree/manage.py runserver`` to launch a development server. This will launch the InvenTree web interface at ``127.0.0.1:8000``. For other options refer to the `django docs <https://docs.djangoproject.com/en/2.2/ref/django-admin/>`_.

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