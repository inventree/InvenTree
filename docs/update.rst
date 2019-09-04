Update InvenTree
================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Update
   :hidden:

Adminitrators wishing to update InvenTree to the latest version should follow the instructions below. The commands listed below should be run from the InvenTree root directory.

.. important::
   It is advisable to backup the InvenTree database before performing these steps.

Stop Server
-----------

Stop the InvenTree server (e.g. gunicorn)

Update Source
-------------

Update the InvenTree source code to the latest version.

``git pull origin master``

Perform Migrations
------------------

Updating the database is as simple as calling the makefile target:

``make migrate``

Restart Server
--------------

Restart the InvenTree server