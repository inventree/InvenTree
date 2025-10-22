---
title: FAQ
---

## Frequently Asked Questions

Below is a list of frequently asked questions. If you are having issues with InvenTree please consult this list first!

Also, you can refer to our [GitHub page](https://github.com/inventree/inventree/issues) for known issues and bug reports - perhaps your issue has already been reported!

If you cannot resolve the issue, please refer to the [troubleshooting guide](#troubleshooting-guide).

## Installation Issues

### Installing on Windows

InvenTree installation is not officially supported natively on Windows. However you can run on a Windows platform using [docker](./start/docker.md).

### Command 'invoke' not found

If the `invoke` command does not work, it means that the invoke tool has not been correctly installed.

Refer to the [invoke installation guide](./start/invoke.md#installation) for more information.

### Can't find any collection named tasks

Refer to the [invoke guide](./start/invoke.md#cant-find-any-collection-named-tasks) for more information.

### Invoke Version

If the installed version of invoke is too old, users may see error messages during the installation procedure. Refer to the [invoke guide](./start/invoke.md#minimum-version) for more information.

### INVE-E1 - No frontend included

Make sure you are running a stable or production release of InvenTree. The frontend panel is not included in development releases.
More Information: [Error Codes - INVE-E1](./settings/error_codes.md#inve-e1)

### No module named <xxx>

During the install or update process, you may be presented with an error like:

```
ModuleNotFoundError: No module named 'django'
```

Either the named modules are not installed, or the virtual environment is not correctly activated.

**Check Virtual Environment**

Ensure that the virtual environment is correctly activated before running any InvenTree commands.

**Check Invoke Tool**

Ensure that the invoke tool is correctly installed inside the virtual environment, with:

```bash
pip install --upgrade --ignore-installed invoke
```

**Install Required Python Packages**

Ensure that all required python packages are installed by running:

```bash
invoke install
```

### 'str' object has no attribute 'removeSuffix'

This error occurs because your installed python version is not up to date. We [require Python {{ config.extra.min_python_version }} or newer](./start/index.md#python-requirements)

You (or your system administrator) needs to update python to meet the minimum requirements for InvenTree.

### InvenTree Site URL

During the installation or update process, you may see an error similar to:

```
'No CSRF_TRUSTED_ORIGINS specified. Please provide a list of trusted origins, or specify INVENTREE_SITE_URL'
```

If you see this error, it means that the `INVENTREE_SITE_URL` environment variable has not correctly specified. Refer to the [configuration documentation](./start/config.md#site-url) for more information.

### Login Issues

If you have successfully started the InvenTree server, but are experiencing issues logging in, it may be due to the security interactions between your web browser and the server. While the default configuration should work for most users, if you do experience login issues, ensure that your [server access settings](./start/config.md#server-access) are correctly configured.

### Session Cookies

The [0.17.0 release](https://github.com/inventree/InvenTree/releases/tag/0.17.0) included [a change to the way that session cookies were handled](https://github.com/inventree/InvenTree/pull/8269). This change may cause login issues for existing InvenTree installs which are upgraded from an older version. System administrators should refer to the [server access settings](./start/config.md#server-access) and ensure that the following settings are correctly configured:

- **INVENTREE_SESSION_COOKIE_SECURE**: `False`
- **INVENTREE_COOKIE_SAMESITE**: `False`

## Update Issues

Sometimes, users may encounter unexpected error messages when updating their InvenTree installation to a newer version.

The most common problem here is that the correct sequence of steps has not been followed:

1. Ensure that the InvenTree web server and background worker processes are *halted*
1. Update the InvenTree software (e.g. using git or docker, depending on installation method)
1. Run the `invoke update` command
1. Restart the web server and background worker processes

For more information, refer to the installation guides:

- [Docker Installation](./start/docker_install.md#updating-inventree)
- [Bare Metal Installation](./start/install.md#updating-inventree)

!!! warning "Invoke Update"
    You must ensure that the `invoke update` command is performed *every time* you update InvenTree

### Breaking Changes

Before performing an update, check the release notes! Any *breaking changes* (changes which require user intervention) will be clearly noted.

### Cannot import name get_storage_class

When running an install or update, you may see an error similar to:

```python
ImportError: cannot import name 'get_storage_class' from 'django.core.files.storage'
```

In such a situation, it is likely that the automatic backup procedure is unable to run, as the required python packages are not yet installed or are unavailable.

To proceed in this case, you can skip the backup procedure by running the `invoke update` command with the `--skip-backup` flag:

```bash
invoke update --skip-backup
```

### Feature *x* does not work after update

If a particular menu / item is not visible after updating InvenTree, or a certain function no longer seems to work, it may be due to your internet browser caching old versions of CSS and JavaScript files.

Before [raising an issue](https://github.com/inventree/inventree/issues), try hard-refreshing the browser cache:

<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>R</kbd>

or

<kbd>Ctrl</kbd> + <kbd>F5</kbd>

!!! tip "A Refreshing Solution"
    Performing a hard page refresh will remove old javascript files from your browser's cache

## Background Worker Issues

### Background Worker "Not Running"

The background worker process must be started separately to the web-server application.

From the top-level source directory, run the following command from a separate terminal, while the server is already running:

```
invoke worker
```

!!! info "Supervisor"
    A better option is to manage the background worker process using a process manager such as supervisor. Refer to the [production server guide](./start/bare_prod.md).

## Docker Issues

### File Sync Issues - Docker

When installing under [Docker](./start/docker.md), sometimes issues may arise keeping [persistent data](./start/docker.md#persistent-data) in sync. Refer to the [common issues](./start/docker.md#common-issues) section in the docker setup guide for further details.

### Permission denied for mkdir: /home/inventree

If you see an error message like this:

```
Permission denied for mkdir: /home/inventree/data/static
```

It means that the user running the InvenTree server does not have permission to create the required directories.

Ensure that the user running the InvenTree server has permission to create the required directories. For example, if running the server as the `inventree` user, ensure that the `inventree` user has permission to create the required directories.

If you are using Docker to run the InvenTree server, ensure that the user that runs the docker daemon has permission to create the required directories in the volume.

### Failed to mount local volume

If, when running InvenTree setup using docker, you see an error message like this:

```
Error response from daemon: failed to mount local volume:
```

This means that either:

- The specified directory does not exist on your local machine
- The docker user does not have write permission to the specified directory

In either case, ensure that the directory is available *on your local machine* and the user account has the required permissions.

## Troubleshooting Guide

If you are struggling with an issue which is not covered in the FAQ above, please refer to the following troubleshooting steps.

Even if you cannot immediately resolve the issue, the information below will be very useful when reporting the issue on GitHub.

### Run Update Step

If you have recently installed or updated your InvenTree instance, make sure that you have run the `invoke update` command, which will perform any required database migrations and other update tasks. This is a *critical step* after any system update.

#### Docker

If you are have installed InvenTree via Docker:

```bash
docker-compose exec inventree-server invoke update
```
#### Installer

If you have installed InvenTree via the installer script:

```bash
inventree run invoke update
```

### Logged Errors

Look at the logged error reports in the admin section - you will need to be an administrator to access this section. If a critical error has occurred, it may be logged here.

### GitHub Issues

Before raising a new issue, please check the [GitHub issues page](https://github.com/inventree/inventree) for reported issues. If your issue is a common one, it may already have been reported - and perhaps even resolved!

### Web Browser Console

If you are experiencing issues with the web interface, you can open the developer console in your web browser to check for error messages. This may vary slightly between web browsers, but there is a wealth of information available online if you need help.

Once the developer console is open, there are two places to check for error messages:

#### Console Tab

Navigate to the *Console* tab in the developer tools. Any error messages will be highlighted in red. They may indicate either a rendering issue, or a problem with a network request.

#### Network Tab

Navigate to the *Network* tab in the developer tools. Check for any requests which have a status code of 400 or greater (indicating an error). Click on the request to see more information about the error.

### Server Logs

Finally, you can check the server logs for error messages. The location of the server logs will depend on how you have installed InvenTree.

#### Docker

If you are using Docker, you can view the server logs with the following command:

To display logs for all running containers:

```bash
docker compose logs
```

Refer to the [docker documentation](./start/docker_install.md#viewing-logs) for more information.

#### Installer

If you are using the installer script, you can view the server logs with the following command:

```bash
inventree logs
```

Refer to the [installer documentation](./start/installer.md#viewing-logs) for more information.
