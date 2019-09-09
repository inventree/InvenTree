InvenTree Configuration
=======================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Configuration
   :hidden:

Admin users will need to adjust the InvenTree installation to meet the particular needs of their setup. For example, pointing to the correct database backend, or specifying a list of allowed hosts.

The Django configuration parameters are found in the normal place (*settings.py*). However the settings presented in this file should not be adjusted as they will alter the core behaviour of the InvenTree application.

To support install specific settings, a simple configuration file ``config.yaml`` is provided. This configuration file is loaded by **settings.py** at runtime. Settings specific to a given install should be adjusted in ``config.yaml``.

The default configuration file launches a *DEBUG* configuration with a simple SQLITE database backend. This default configuration file is shown below:

.. literalinclude :: ../InvenTree/config_template.yaml
   :language: yaml
   :linenos:

Database Options
----------------

InvenTree provides support for multiple database backends - any backend supported natively by Django can be used. 

Database options are specified under the *database* heading in the configuration file. Any option available in the Django documentation can be used here - it is passed through transparently to the management scripts.

**SQLite:**
By default, InvenTree uses an sqlite database file : ``inventree_db.sqlite3``. This provides a simple, portable database file that is easy to use for debug and testing purposes. 


**MySQL:** MySQL database backend is supported with the native Django implemetation. To run InvenTree with the MySQL backend, a number of extra packages need to be installed:

* mysql-server - *MySQL backend server*
* libmysqlclient-dev - *Required for connecting to the MySQL database in Python*
* (pip) mysqlclient - *Python package for communication with MySQL database*

These requirements can be installed from the base directory with the command ``make mysql``.

It is then up to the database adminstrator to create a new MySQL database to store inventree data, in addition to a username/password to access the data.

.. important:: MySQL Collation: 
    When creating the MySQL database, the adminstrator must ensure that the collation option is set to *utf8_unicode_520_ci* to ensure that InvenTree features function correctly.

The database options (in the ``config.yaml`` file) then need to be adjusted to communicate the MySQL backend. Refer to the `Django docs <https://docs.djangoproject.com/en/dev/ref/databases/>`_ for further information.

**PostgreSQL:** PostgreSQL database backend is supported with the native Django implementation. Note that to use this backend, the following system packages must be installed:

* postgresql
* postgresql-contrib
* libpq-dev
* (pip3) psycopg2

These requirements can be installed from the base directory with the command ``make postgresql``.

It is then up to the database adminstrator to create a new PostgreSQL database to store inventree data, in addition to a username/password to access the data.

The database options (in the ``config.yaml`` file) then need to be adjusted to communicate the PostgreSQL backend. Refer to the `Django docs <https://docs.djangoproject.com/en/dev/ref/databases/>`_ for further information.

Allowed Hosts / CORS
--------------------

By default, all hosts are allowed, and CORS requests are enabled from any origin. **This is not secure and should be adjusted for your installation**. These options can be changed in the configuration file.

For further information, refer to the following documentation:

* `Django ALLOWED_HOSTS <https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts>`_
* `Django CORS headers <https://github.com/OttoYiu/django-cors-headers>`_

Uploaded File Storage
---------------------

By default, uploaded files are stored in the local direction ``./media``. This directory should be changed based on the particular installation requirements.

Backup Location
---------------

The default behaviour of the database backup is to generate backup files for database tables and media files to the user's temporary directory. The target directory can be overridden by setting the *backup_dir* parameter in the config file.