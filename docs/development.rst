InvenTree Development
===================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Development
   :hidden:

Development and Testing
-----------------------

Shorthand functions are provided for the development and testing process:

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

Dependency Documentation
-----------------------

Documentation/Project links for packages found in ``requirements.txt``:

`coreapi <https://github.com/core-api/python-client>`_
`coverage <https://github.com/nedbat/coveragepy>`_
`Django <https://docs.djangoproject.com/>`_
`django-cleanup <https://github.com/un1t/django-cleanup>`_
`django-cors-headers <https://github.com/adamchainz/django-cors-headers/>`_
`django-crispy-forms <https://github.com/django-crispy-forms/django-crispy-forms>`_
`django-dbbackup <https://github.com/django-dbbackup/django-dbbackup>`_
`django-guardian <https://github.com/django-guardian/django-guardian>`_
`django-import-export <https://github.com/django-import-export/django-import-export>`_
`django-mptt <https://github.com/django-mptt/django-mptt>`_
`django-qr-code <https://github.com/dprog-philippe-docourt/django-qr-code>`_
`django_filter <https://github.com/carltongibson/django-filter>`_
`djangorestframework <https://www.django-rest-framework.org/>`_
`djangorestframework-guardian <https://github.com/rpkilby/django-rest-framework-guardian>`_
`flake8 <https://gitlab.com/pycqa/flake8>`_
`fuzzywuzzy <https://github.com/seatgeek/fuzzywuzzy>`_
`pillow <https://pillow.readthedocs.io/en/stable/>`_
`pygments <https://pygments.org/>`_
`python-coveralls <https://github.com/z4r/python-coveralls>`_
`python-Levenshtein <https://github.com/ztane/python-Levenshtein>`_
`tablib <https://tablib.readthedocs.io/en/stable/>`_
