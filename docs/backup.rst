Backup and Restore
==================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Backup
   :hidden:

InvenTree provides database backup and restore functionality through the `django-dbbackup <https://github.com/django-dbbackup/django-dbbackup>`_ extension.

This extension allows database models and uploaded media files to be backed up (and restored) via the command line.

In the root InvenTre directory, run ``make backup`` to generate backup files for the database models and media files.