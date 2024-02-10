---
title: Setup Introduction
---

!!! info "Fast install"
    A quick-and-easy install can be done done with the following one-liner.
	```bash
	wget -qO install.sh https://get.inventree.org && bash install.sh
	```
	Read more about the [installer](./installer.md).

## Introduction

InvenTree can be self-hosted with minimal system requirements. Multiple database back-ends are supported, allowing for flexibility where required.

The InvenTree server ecosystem consists of the following components:

### Database

A persistent database is required for data storage. InvenTree can be used with any of the following database backends:

* PostgreSQL
* MySQL / MariaDB
* SQLite

!!! warning "SQLite"
    While SQLite provides a simpler setup and is useful for a development environment, we strongly recommend against using it for a production environment. Use PostgreSQL or MySQL instead

Database selection should be determined by your particular installation requirements.

### Media Files

Uploaded media files (images, attachments, reports, etc) are stored to a persistent storage volume.

### Web Server

The bulk of the InvenTree code base supports the custom web server application. The web server application services user requests and facilitates database access.

The webserver code also provides a first-party API for performing database query actions.

Once a database is setup, you need a way of accessing the data. InvenTree provides a "server" application out of the box, but this may not scale particularly well with multiple users.  Instead, InvenTree can be served using a webserver such as [Gunicorn](https://gunicorn.org/). For more information see the [deployment documentation](./bare_prod.md).

### Background Tasks

A separate application handles management of [background tasks](../settings/tasks.md), separate to user-facing web requests.

## OS Requirements

The InvenTree documentation assumes that the operating system is a debian based Linux OS. Some installation steps may differ for different systems.

!!! warning "Installing on Windows"
    Installation on Windows is *not guaranteed* to work (at all). To install on a Windows system, it is highly recommended that you [install WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10#manual-installation-steps), and then follow installation procedure from within the WSL environment.

!!! success "Docker"
    Installation on any OS is simplified by following the [docker setup guide](./docker.md).

## Python Requirements

InvenTree runs on [Python](https://python.org).

!!! warning "Python Version"
    InvenTree requires Python 3.9 (or newer). If your system has an older version of Python installed, you will need to follow the update instructions for your OS.

### Invoke

InvenTree makes use of the [invoke](https://www.pyinvoke.org/) python toolkit for performing various administrative actions.

!!! warning "Invoke Version"
	InvenTree requires invoke version 2.0.0 or newer. Some platforms may be shipped with older versions of invoke!

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

!!! info "Activate Virtual Environment"
	if
	```
	source env/bin/activate
	```
	is not working try
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

## Installation Guides

There are multiple ways to get an InvenTree server up and running, of various complexity (and robustness)!

### Docker

The recommended method of installing InvenTree is to use [docker](https://www.docker.com). InvenTree provides out-of-the-box support for docker and docker compose, which provides a simple, reliable and repeatable pipeline for integration into your production environment.

Refer to the following guides for further instructions:

- [**Docker development server setup guide**](./docker_dev.md)
- [**Docker production server setup guide**](./docker.md)

### Bare Metal

If you do not wish to use the docker container, you will need to manually install the required packages and follow through the installation guide.

Refer to the following guides for further instructions:

- [**Bare metal development server setup guide**](./bare_dev.md)
- [**Bare metal production server setup guide**](./install.md)

## Debug Mode

By default, the InvenTree web server is configured to run in [DEBUG mode](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-DEBUG).

Running in DEBUG mode provides many handy development features, however it is strongly recommended *NOT* to run in DEBUG mode in a production environment. This recommendation is made because DEBUG mode leaks a lot of information about your installation and may pose a security risk.

So, for a production setup, you should set `INVENTREE_DEBUG=false` in the [configuration options](./config.md).

### Potential Issues

Turning off DEBUG mode creates further work for the system administrator. In particular, when running in DEBUG mode, the InvenTree web server natively manages *static* and *media* files, which means that the InvenTree server can run "monolithically" without the need for a separate web server.

!!! info "Read More"
    Refer to the [Serving Files](./serving_files.md) section for more details
