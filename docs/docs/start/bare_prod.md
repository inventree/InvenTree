---
title: Bare Metal Production Server
---

## Bare Metal Production Server

!!! warning "Installation"
    Before continuing, ensure that the [installation steps](./install.md) have been completed.

The following instructions provide a reasonably performant server, using [gunicorn](https://gunicorn.org/) as a webserver, and [supervisor](http://supervisord.org/) as a process manager.

For alternative deployment methods, django apps provide multiple deployment methods - see the [Django documentation]({% include "django.html" %}/howto/deployment/).

There are also numerous online tutorials describing how to deploy a Django application either locally or on an online platform.

### Gunicorn

The InvenTree web server is hosted using [Gunicorn](https://gunicorn.org/). Gunicorn is a Python WSGI server which provides a multi-worker server which is well suited to handling multiple simultaneous requests. Gunicorn is a solid choice for a production server which is easy to configure and performs well in a multi-user environment.

### Supervisor

[Supervisor](http://supervisord.org/) is a process control system which monitors and controls multiple background processes. It is used in the InvenTree production setup to ensure that the server and background worker processes are always running.

## Gunicorn

Gunicorn should have already been installed (within the python virtual environment) as part of the installation procedure.

A simple gunicorn configuration file is also provided. This configuration file can be edited if different server settings are required

### Test Gunicorn Server

First, let's confirm that the gunicorn server is operational.

!!! info "Virtual Environment"
    Don't forget to activate the python virtual environment

```
cd /home/InvenTree
source ./env/bin/activate

cd src/InvenTree
/home/inventree/env/bin/gunicorn -c gunicorn.conf.py InvenTree.wsgi -b 127.0.0.1:8000
```

This should start the gunicorn server as a foreground process.

Check that you can access the InvenTree web server [in your browser](http://127.0.0.1:8000):

### Stop Gunicorn Server

Once the gunicorn server is operational, kill the server with <kbd>Ctrl</kbd>+<kbd>c</kbd>

## Supervisor

We will use [supervisor](http://supervisord.org/) as a process monitor, to ensure the web server and background worker processes are automatically started, and restarted if something goes wrong.

### Install Supervisor

!!! info "Sudo Actions"
    Perform sudo actions from a separate shell, as 'inventree' user does not have sudo access

```
sudo apt-get install supervisor
```

### Configure Supervisor

!!! warning "Configuration Override"
    If you already have supervisor installed on your system, you will not want to override your existing configuration file.
    In this case, edit the existing configuration file at `/etc/supervisord.conf` to integrate the InvenTree processes

Copy the supervisor configuration file:

```
sudo cp /home/inventree/src/deploy/supervisord.conf /etc/supervisord.conf
```

### Start Supervisor Daemon

```
sudo supervisord
```

### Check Server

Check that the InvenTree [web server is running](http://localhost:8000).

### View Process Status

The process status can be viewed [in your web browser](http://localhost:9001).

## Production Ready

The InvenTree server (and background task manager) should now be running!

### Static and Media Files

In addition to the InvenTree server, you will need a method of delivering static and media files (this is *not* handled by the InvenTree server in a production environment).

!!! info "Read More"
    Refer to the [Serving Files](./serving_files.md) section for more details

### Next Steps

You (or your system administrator) may wish to perform further steps such as placing the InvenTree server behind a reverse-proxy such as [caddy](https://caddyserver.com/), or [nginx](https://www.nginx.com/).
As production environment options are many and varied, such tasks are outside the scope of this documentation.

There are many great online tutorials about running django applications in production!

As a starting point, you can refer to the [docker guide](./docker.md) for a demonstration of running InvenTree behind a Caddy proxy.
