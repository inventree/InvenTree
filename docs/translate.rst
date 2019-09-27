Translations
============

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Language Translation
   :hidden:

InvenTree supports multi-language translation using the `Django Translation Framework <https://docs.djangoproject.com/en/2.2/topics/i18n/translation/>`_

Translation strings are located in the `InvenTree/locales/` directory, and translation files can be easily added here.

To set the default language, change the `language` setting in the `config.yaml` settings file.

To recompile the translation files (after adding new translation strings), run the command ``make translate`` from the root directory.
