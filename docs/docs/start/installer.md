---
title: InvenTree Installer
---

## Installer
The InvenTree installer automates the installation procedure for a production InvenTree server.

Supported OSs are Debian 11 and Ubuntu 20.04 LTS.

### Quick Script

```bash
wget -qO install.sh https://get.inventree.org && bash install.sh
```

This script does all manual steps without any input. The installation might take up to 5-10 minutes to finish.

### File Locations

The installer creates the following directories:

| Directory | Description |
| --- | --- |
| `/etc/inventree/` | Configuration files |
| `/opt/inventree/` | InvenTree application files |
| `/opt/inventree/data/` | Inventree data files |

#### Performed steps

The installer script performs the following functions:

- Checks if the current OS is supported
- Installs packages needed for getting the packages keys
- Executes the manual steps listed below

#### Script Options

The install script supports pulling packages from different branches and publishers.
Defaults are to use branch `stable` and publisher `inventree`.

For example to install the `master` (latest) InvenTree code:

```bash
install master inventree
```

To install from branch master and publisher matmair the install command would be.
```bash
install master matmair
```

Furthermore there are several command flags for advanced usage:
`--help` to show all options
`--version` to print the version of the install script
`--dry-run` to print but not execute the commands that would change system files

### Manual Install

The steps below are for Ubuntu 20.04 LTS, the current instructions for Ubuntu and Debian  can be found [here](https://packager.io/gh/inventree/InvenTree).

Add the key needed for validating the packages.
```bash
wget -qO- https://dl.packager.io/srv/inventree/InvenTree/key | sudo apt-key add -
```

Add the package list to the package manager source list.
```bash
sudo wget -O /etc/apt/sources.list.d/inventree.list https://dl.packager.io/srv/inventree/InvenTree/stable/installer/ubuntu/20.04.repo
```

Update the local package index.
```bash
sudo apt-get update
```

Install the InvenTree package itself. This step might take multiple minutes.
```bash
sudo apt-get install inventree
```

### Options

#### Debug Outputs

Extra debug messages are printed if the environment variable `SETUP_DEBUG` is set. This exposes passwords.

#### External Calls

By default, a public AWS service is used to resolve the public IP address of the server. To prevent this the environment variable `SETUP_NO_CALLS` must be set to `true`.

#### Admin User

By default, an admin user is automatically generated with username `admin`, mail `admin@example.com` and a dynamic password that is saved to `/etc/inventree/admin_password`.
These values can be customised with the environment variables `INVENTREE_ADMIN_USER`, `INVENTREE_ADMIN_EMAIL` and `INVENTREE_ADMIN_PASSWORD`.
To stop the automatic generation of an admin user, generate an empty file needs to be placed at `/etc/inventree/admin_password`.

#### Webconfig

By default, InvenTree is served internally on port 6000 and then proxied via Nginx. The config is placed in `/etc/nginx/sites-enabled/inventree.conf` and overwritten on each update. The location can be set with the environment variable `SETUP_NGINX_FILE`.
This only serves an HTTP version of InvenTree, to use HTTPS (recommended for production) or customise any further an additional config file should be used.

#### Extra python packages
Extra python packages can be installed by setting the environment variable `SETUP_EXTRA_PIP`.

#### Database Options

The used database backend can be configured with environment variables (before the first setup) or in the config file after the installation. Check the [configuration section](./config.md#database-options) for more information.

## Moving Data

To change the data storage location, link the new location to `/opt/inventree/data`.
A rough outline of steps to achieve this could be:
- shut down the app service(s) `inventree` and webserver `nginx`
- copy data to the new location
- check everything was transferred successfully
- delete the old location
- create a symlink from the old location to the new one
- start up the services again

## Updating InvenTree

To update InvenTree run `apt install --only-upgrade inventree` - this might need to be run as a sudo user.

## Controlling InvenTree

### Services
InvenTree installs multiple services that can be controlled with your local system runner (`service` or `systemctl`).
The service `inventree` controls everything, `inventree-web` the (internal) webserver and `inventree-worker` the background worker(s).

More instances of the worker can be instantiated from the command line. This is only meant for advanced users.
This sample script launches 3 services. By default, 1 is launched.
```bash
inventree scale worker=3
```

### Environment Variables

The CLI can be used to permanently modify the environment variables used while executing the app server or workers.

To set variables use
```bash
inventree config:set ENV_VAR=123
```

To read out all variables use
```bash
inventree config
```

!!! warning "Keep things repeatable"
    All CLI settings are lost when the package is uninstalled.
    Use the config file where possible as it is kept on uninstall and can easily be synced across instances. Environment variables are a good place for passwords (but not the secret_key).

## Architecture

The packages are provided by [packager.io](https://packager.io/). They are built each time updates are pushed to GitHub and released about 10 minutes later. The local package index must be updated to see the new release in the package manager.

The package sets up [services](#controlling-inventree) that run the needed processes as the unprivileged user `inventree`. This keeps the privileges of InvenTree as low as possible.

A CLI is provided to interface with low-level management functions like [variable management](#enviroment-variables), log access, commands, process scaling, etc.
