Getting Started Guide
=====================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

To install a complete *development* environment for InvenTree, follow the steps presented below. A production environment will require further work as per the particular application requirements. 

A makefile in the root directory provides shortcuts for the installation process, and can also be very useful during development.

Requirements
------------

To install InvenTree you will need the following system components installed:

* python3
* python3-pip (pip3)
* make

Each of these programs need to be installed (e.g. using apt or similar) before running the ``make install`` script.

Installation
------------

First, download the latest InvenTree source code:

``git clone https://github.com/inventree/inventree/``

InvenTree is a Python/Django application and relies on the pip package manager. All packages required to develop and test InvenTree can be installed via pip. Package requirements can be found in ``requirements.txt``.

To setup the InvenTree environment, *cd into the inventree directory* and run the command:

``make install``

which installs all required Python packages using pip package manager. It also creates a (default) database configuration file which needs to be edited to meet user needs before proceeding (see next step below).

Additionally, this step creates a *SECRET_KEY* file which is used for the django authentication framework. 

.. important:: 
    The *SECRET_KEY* file should never be shared or made public. 

Database Configuration
-----------------------

Once the required packages are installed, the database configuration must be adjusted to suit your particular needs. InvenTree provides a simple default setup which should work *out of the box* for testing and debug purposes.

As part of the previous *install* step, a configuration file (``config.yaml``) is created. The configuration file provides administrators control over various setup options without digging into the Django *settings.py* script. The default setup uses a local sqlite database with *DEBUG* mode enabled.

For further information on installation configuration, refer to the `Configuration <config.html>`_ section.

Initialize Database
-------------------

Once install settings are correctly configured (in *config.yaml*) run the initial setup script:

``make migrate``

which performs the initial database migrations, creating the required tables, etc

The database should now be installed!

Create Admin Account
--------------------

Create an initial superuser (administrator) account for the InvenTree instance:

``make superuser``

Run Development Server
----------------------

Run ``cd InvenTree && python3 manage.py runserver 127.0.0.1:8000`` to launch a development server. This will launch the InvenTree web interface at ``127.0.0.1:8000``. For other options refer to the `django docs <https://docs.djangoproject.com/en/2.2/ref/django-admin/>`_.

Database Migrations
-------------------

Whenever a change is made to the underlying database schema, database migrations must be performed. Call ``make migrate`` to run any outstanding database migrations.

Development and Testing
-----------------------

Other shorthand functions are provided for the development and testing process:

* ``make install`` - Install all required underlying packages using PIP
* ``make update`` - Update InvenTree installation (after database configuration)
* ``make superuser`` - Create a superuser account
* ``make migrate`` - Perform database migrations
* ``make mysql`` - Install packages required for MySQL database backend
* ``make postgresql`` - Install packages required for PostgreSQL database backend
* ``make translate`` - Compile language translation files (requires gettext system package)
* ``make backup`` - Backup database tables and media files
* ``make test`` - Run all unit tests
* ``make coverage`` - Run all unit tests and generate code coverage report
* ``make style`` - Check Python codebase against PEP coding standards (using Flake)
* ``make docreqs`` - Install the packages required to generate documentation
* ``make docs`` - Generate this documentation