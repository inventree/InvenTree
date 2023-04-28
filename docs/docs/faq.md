---
title: FAQ
---

## Frequently Asked Questions

### Errors during InvenTree update

Sometimes, users may encounter unexpected error messages when updating their InvenTree installation to a newer version.

The most common problem here is that the correct sequenct of steps has not been followed:

1. Ensure that the InvenTree web server and background worker processes are *halted*
1. Update the InvenTree software (e.g. using git or docker, depending on installation method)
1. Run the `invoke update` command
1. Restart the web server and background worker processes

For more information, refer to the installation guides:

- [Docker Installation](./start/docker_prod.md#updating-inventree)
- [Bare Metal Installation](./start/install.md#updating-inventree)

!!! warning "Invoke Update"
    You must ensure that the `invoke update` command is perfomed *every time* you update InvenTree

### Feature *x* does not work after update

If a particular menu / item is not visible after updating InvenTree, or a certain function no longer seems to work, it may be due to your internet browser caching old versions of CSS and JavaScript files.

Before [raising an issue](https://github.com/inventree/inventree/issues), try hard-refreshing the browser cache:

<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>R</kbd>

or

<kbd>Ctrl</kbd> + <kbd>F5</kbd>

!!! tip "A Refreshing Solution"
    Performing a hard page refresh will remove old javascript files from your browser's cache

### Problems installing on Windows

InvenTree installation is not officially supported natively on Windows. Install using the WSL framework.

### Command 'invoke' not found

If the `invoke` command does not work, it means that the [invoke](https://pypi.org/project/invoke/) python library has not been correctly installed.

Update the installed python packages with PIP:

```
pip3 install -U -r requirements.txt
```

### Invoke Version

If the installed version of invoke is too old, users may see error messages during the installation procedure, such as *"'update' did not receive all required positional arguments!"* (or similar).

As per the [invoke guide](./start/intro.md#invoke), the minimum required version of Invoke is `1.4.0`.

To determine the version of invoke you have installed, run either:

```
invoke --version
```
```
python -m invoke --version
```

If you are running an older version of invoke, ensure it is updated to the latest version.

### ModuleNotFoundError: No module named 'django'

Most likely you are trying to run the InvenTree server from outside the context of the virtual environment where the required python libraries are installed.

Always activate the virtual environment before running server commands!

### Background Worker "Not Running"

The background worker process must be started separately to the web-server application.

From the top-level source directory, run the following command from a separate terminal, while the server is already running:

```
invoke worker
```

!!! info "Supervisor"
    A better option is to manage the background worker process using a process manager such as supervisor. Refer to the [production server guide](./start/production.md).

### File Sync Issues - Docker

When installing under [Docker](./start/docker.md), sometimes issues may arise keeping [persistent data](./start/docker.md#persistent-data) in sync. Refer to the [common issues](./start/docker_prod.md#common-issues) section in the docker setup guide for further details.
