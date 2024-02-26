---
title: Setup Introduction
---

## Introduction

A functional InvenTree server can be hosted with minimal setup requirements. Multiple installation methods and database back-ends are supported, allowing for flexibility where required.

!!! info "Production Ready"
	InvenTree is designed to be a production-ready application, and can be deployed in a variety of environments. The following instructions are designed to help you get started with a *production* setup. For a development setup, refer to the [development setup guide](../develop/starting.md).

## Installation Methods

To quickly jump to a specific installation method, refer to the following links:

- [**Docker**](./docker.md)
- [**Package Installer**](./installer.md)
- [**Bare Metal**](./install.md)

!!! success "Docker Recommended"
    The recommended method of installing InvenTree is to follow our [docker setup guide](./docker.md). InvenTree provides out-of-the-box support for docker and docker compose, which provides a simple, reliable and repeatable pipeline for integration into your production environment.

!!! info "Further Reading"
    For more information on the InvenTree tech stack, continue reading below!

## System Components

The InvenTree server ecosystem consists of the following components:

### Database

A persistent database is required for data storage. By default, InvenTree is configured to use [PostgreSQL](https://www.postgresql.org/) - and this is the recommended database backend to use. However, InvenTree can also be configured to connect to any database backend [supported by Django]({% include "django.html" %}/ref/databases/)


### Web Server

The bulk of the InvenTree code base supports the custom web server application. The web server application services user requests and facilitates database access. The webserver provides access to the [API](../api/api.md) for performing database query actions.

InvenTree uses [Gunicorn](https://gunicorn.org/) as the web server - a Python WSGI HTTP server.

### Background Tasks

A separate application handles management of [background tasks](../settings/tasks.md), separate to user-facing web requests. The background task manager is required to perform asynchronous tasks, such as sending emails, generating reports, and other long-running tasks.

InvenTree uses [django-q2](https://django-q2.readthedocs.io/en/master/) as the background task manager.

### File Storage

Uploaded *media* files (images, attachments, reports, etc) and *static* files (javascript, html) are stored to a persistent storage volume. A *file server* is required to serve these files to the user.

InvenTree uses [Caddy](https://caddyserver.com/) as a file server, which is configured to serve both *static* and *media* files. Additionally, Caddy provides SSL termination and reverse proxy services.

## OS Requirements

The InvenTree documentation *assumes* that the operating system is a debian based Linux OS. Some installation steps may differ for different systems.

!!! warning "Installing on Windows"
    To install on a Windows system, you should [install WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10#manual-installation-steps), and then follow installation procedure from within the WSL environment.

!!! success "Docker"
    Installation on any OS is simplified by following the [docker setup guide](../docker).

## Python Requirements

InvenTree requires a minimum Python version of {{ config.extra.min_python_version}}. If your system has an older version of Python installed, you will need to follow the update instructions for your OS.

### Invoke

InvenTree makes use of the [invoke](https://www.pyinvoke.org/) python toolkit for performing various administrative actions.

!!! warning "Invoke Version"
	InvenTree requires invoke version {{ config.extra.min_invoke_version }} or newer. Some platforms may be shipped with older versions of invoke!

!!! tip "Updating Invoke"
    To update your invoke version, run `pip install -U invoke`

To display a list of the available InvenTree administration actions, run the following commands from the top level source directory:

```
invoke --list
```

### Virtual Environment

Installing the required Python packages inside a virtual environment allows a local install separate to the system-wide Python installation. While not strictly necessary, using a virtual environment is **highly recommended** as it prevents conflicts between the different Python installations.

You can read more about Python virtual environments [here](https://docs.python.org/3/tutorial/venv.html).

!!! info "Virtual Environment"
    The installation instruction assume that a virtual environment is configured

`cd` into the InvenTree directory, and create a virtual environment with the following command:

```
python3 -m venv env
```

### Activating a Virtual Environment

The virtual environment needs to be activated to ensure the correct python binaries and libraries are used. The InvenTree instructions assume that the virtual environment is always correctly activated.

To configure Inventree inside a virtual environment, ``cd`` into the inventree base directory and run the following command:

```
source env/bin/activate
```

Or, if that does not work, try:

```
. env/bin/activate
```

This will place the current shell session inside a virtual environment - the terminal should display the ``(env)`` prefix.

## InvenTree Source Code

InvenTree source code is distributed on [GitHub](https://github.com/inventree/inventree/), and the latest version can be downloaded (using Git) with the following command:

```
git clone https://github.com/inventree/inventree/
```

Alternatively, the source can be downloaded as a [.zip archive](https://github.com/inventree/InvenTree/archive/master.zip).

!!! info "Updating via Git"
    Downloading the source code using Git is recommended, as it allows for simple updates when a new version of InvenTree is released.


## Debug Mode

By default, a production InvenTree installation is configured to run with [DEBUG mode]({% include "django.html" %}/ref/settings/#std:setting-DEBUG) *disabled*.

Running in DEBUG mode provides many handy development features, however it is strongly recommended *NOT* to run in DEBUG mode in a production environment. This recommendation is made because DEBUG mode leaks a lot of information about your installation and may pose a security risk.

So, for a production setup, you should set `INVENTREE_DEBUG=false` in the [configuration options](./config.md).

### Potential Issues

Turning off DEBUG mode creates further work for the system administrator. In particular, when running in DEBUG mode, the InvenTree web server natively manages *static* and *media* files, which means that the InvenTree server can run "monolithically" without the need for a separate web server.

!!! info "Read More"
    Refer to the [Serving Files](./serving_files.md) section for more details
