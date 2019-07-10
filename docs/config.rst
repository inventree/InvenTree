InvenTree Configuration
=======================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Configuration
   :hidden:

Admin users will need to adjust the InvenTree installation to meet the particular needs of their setup. For example, pointing to the correct database backend, or specifying a list of allowed hosts.

The Django configuration parameters are found in the normal place (``settings.py``). However the settings presented in this file should not be adjusted as they will alter the core behaviour of the InvenTree application.

To support install specific settings, a simple configuration file ``config.yaml`` is provided. This configuration file is loaded by ``settings.py`` at runtime. Settings specific to a given install should be adjusted in ``config.yaml``.

The default configuration file launches a *DEBUG* configuration with a simple SQLITE database backend. This default configuration file is shown below:

.. literalinclude :: ../InvenTree/config.yaml
   :language: yaml
   :linenos:

Database Options
----------------

InvenTree provides support for multiple database backends - any backend supported natively by Django can be used. 

Database options are specified under the *database* heading in the configuration file. Any option available in the Django documentation can be used here - it is passed through transparently to the management scripts.

**SQLITE:**
By default, InvenTree uses an sqlite database file : ``inventree_db.sqlite3``. This provides a simple, portable database file that is easy to use for debug and testing purposes. 


**MYSQL:** MySQL database backend is supported with the native Django implemetation.

**POSTGRESQL:** PostgreSQL database backend is supported with the native Django implementation. Note that to use this backend, the ``psycopg2`` Python library must first be installed.