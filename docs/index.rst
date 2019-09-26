InvenTree Source Documentation
================================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Index
   :hidden:

   Getting Started<start>
   Configuration<config>
   Deployment<deploy>
   Migrate Data<migrate>
   Update InvenTree<update>
   Translations<translate>
   Backup and Restore<backup>
   Modal Forms<forms>
   Tables<tables>
   REST API<rest>
   InvenTree Modules <modules>
   Module Reference<reference>

The documentation found here is provided to be useful for developers working on the InvenTree codebase. User documentation can be found on the `InvenTree website <https://inventree.github.io>`_.

Documentation for the Python modules is auto-generated from the `InvenTree codebase <https://github.com/InvenTree/InvenTree>`_.

Code Structure
--------------

**Backend**

InvenTree is developed using the `django web framework <https://www.djangoproject.com/>`_, a powerful toolkit for making web applications in Python.

The database management code and business logic is written in Python 3. Core functionality is separated into individual modules (or *apps* using the django nomenclature).

Each *app* is located in a separate directory under InvenTree. Each *app* contains python modules named according to the standard django configuration.

**Frontend**

The web frontend rendered using a mixture of technologies.

Base HTML code is rendered using the `django templating language <https://docs.djangoproject.com/en/2.2/topics/templates/>`_ which provides low-level access to the underlying database models.

jQuery is also used to implement front-end logic, and desponse to user input. A REST API is provided to facilitate client-server communication.