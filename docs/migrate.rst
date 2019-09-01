Migrating Data
==============

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Migrating Data
   :hidden:

In the case that data needs to be migrated from one database installation to another, the following procedure can be used to export data, initialize the new database, and re-import the data.

Export Data
-----------

``python3 manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 > data.json``

This will export all data (including user information) to a json data file.

Initialize Database
-------------------

Configure the new database using the normal processes (see `Getting Started <start.html>`_):

``python3 manage.py makemigrations``

``python3 manage.py migrate --run-syncdb``

Import Data
-----------

The new database should now be correctly initialized with the correct table structures requried to import the data.

``python3 manage.py loaddata data.json``