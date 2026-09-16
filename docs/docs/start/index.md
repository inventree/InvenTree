---
title: Setup Introduction
---

## Introduction

A functional InvenTree server can be hosted with minimal setup requirements. Multiple installation methods and database back-ends are supported, allowing for flexibility where required.

!!! info "Production Ready"
	InvenTree is designed to be a production-ready application, and can be deployed in a variety of environments. The following instructions are designed to help you get started with a *production* setup. For a development setup, refer to the [devcontainer setup guide](../develop/devcontainer.md).

## Installation Methods

To quickly jump to a specific installation method, refer to the following links:

- [**Docker**](./docker.md)
- [**Package Installer**](./installer.md)
- [**Bare Metal**](./install.md)

!!! success "Docker Recommended"
    The recommended method of installing InvenTree is to follow our [docker setup guide](./docker.md). InvenTree provides out-of-the-box support for docker and docker compose, which provides a simple, reliable and repeatable pipeline for integration into your production environment.

!!! warning "Important Security Considerations"
    We provide documentation around the security posture that is assumed by the InvenTree project in the software design. Assessing this is a *critical* part of the setup process, and should be read carefully before deploying InvenTree in a production environment. You can read more about the [threat modelling inputs here](../concepts/threat_model.md).

!!! info "Further Reading"
    For more information on the InvenTree tech stack, continue reading below!

### Configuration Options

Independent of the preferred installation method, InvenTree provides a number of [configuration options](./config.md) which can be used to customize the server environment.

## System Components

The InvenTree software stack is composed of multiple components, each of which is required for a fully functional server environment. Your can read more about the [InvenTree processes here](./processes.md).

## OS Requirements

The InvenTree documentation *assumes* that the operating system is a debian based Linux OS. Some installation steps may differ for different systems.

!!! warning "Installing on Windows"
    To install on a Windows system, you should [install WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10#manual-installation-steps), and then follow installation procedure from within the WSL environment.

!!! success "Docker"
    Installation on any OS is simplified by following the [docker setup guide](./docker.md).

## Python Requirements

InvenTree requires a minimum Python version of {{ config.extra.min_python_version}}. If your system has an older version of Python installed, you will need to follow the update instructions for your OS.

### Invoke

InvenTree makes use of the [invoke](https://www.pyinvoke.org/) python toolkit for performing various administrative actions. You can read [more about out use of the invoke tool here](./invoke.md)

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

To configure InvenTree inside a virtual environment, ``cd`` into the inventree base directory and run the following command:

```
source env/bin/activate
```

Or, if that does not work, try:

```
. env/bin/activate
```

This will place the current shell session inside a virtual environment - the terminal should display the ``(env)`` prefix.

### Invoke in Virtual Environment

If you are using a virtual environment (and you should be!) you will need to ensure that you have installed the `invoke` package inside the virtual environment! If the invoke commands are run from outside the virtual environment, they may not work correctly - and may be extremely difficult to debug!

To install the `invoke` package inside the virtual environment, run the following command (after activating the virtual environment):

```
pip install --upgrade --ignore-installed invoke
```

To check that the `invoke` package is correctly installed, run the following command:

```
which invoke
```

This should return the path to the `invoke` binary inside the virtual environment. If the path is *not* inside the virtual environment, the `invoke` package is not correctly installed!

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

So, for a production setup, you should ensure that `INVENTREE_DEBUG=false` in the [configuration options](./config.md).

!!! warning "Security Risk"
    Running InvenTree in DEBUG mode in a production environment is a significant security risk, and should be avoided at all costs.

### Turning Debug Mode off

When running in DEBUG mode, the InvenTree web server natively manages *static* and *media* files, which means that when DEBUG mode is *disabled* (which is the default for a production setup), the proxy setup has to be configured to handle this.

!!! info "Read More"
    Refer to the [proxy server documentation](./processes.md#proxy-server) for more details
