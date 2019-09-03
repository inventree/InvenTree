Deploying InvenTree
===================

.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Deployment
   :hidden:

The development server provided by the Django ecosystem may be fine for a testing environment or small contained setups. However special consideration must be given when deploying InvenTree in a real-world environment.

Django apps provide multiple deployment methods - see the `Django documentation <https://docs.djangoproject.com/en/2.2/howto/deployment/>`_.

There are also numerous online tutorials describing how to deploy a Django application either locally or on an online platform.

Following is a simple tutorial on serving InvenTree using `Gunicorn <https://gunicorn.org/>`_. Gunicorn is a Python WSGI server which provides a multi-worker server which is much better suited to handling multiple simultaneous requests. 

Install Gunicorn
----------------

Gunicorn can be installed using PIP:

``pip3 install gunicorn``


Configure Static Directories
----------------------------

Directories for storing *media* files and *static* files should be specified in the ``config.yaml`` configuration file. These directories are the ``MEDIA_ROOT`` and ``STATIC_ROOT`` paths required by the Django app.

Collect Static Files
--------------------

The required static files must be collected into the specified ``STATIC_ROOT`` directory:

``python3 InvenTree/manage.py collectstatic``

Configure Gunicorn
------------------

The Gunicorn server can be configured with a simple configuration file (e.g. python script). An example configuration file is provided in ``InvenTree/gunicorn.conf.py``

.. literalinclude :: ../InvenTree/gunicorn.conf.py
   :language: python
   :linenos:

This file can be used to configure the Gunicorn server to match particular requirements.

Run Gunicorn
------------

From the directory where ``manage.py`` is located:

Run ``gunicorn -c gunicorn.conf.py InvenTree.wsgi``