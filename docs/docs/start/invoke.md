---
title: Invoke Tool
---

## Invoke Tool

InvenTree uses the [invoke](https://www.pyinvoke.org/) tool to manage various system administration tasks. Invoke is a powerful python-based task execution tool, which allows for the creation of custom tasks and command-line utilities.

### Installation

InvenTree setup and administration requires that the invoke tool is installed. This is usually installed automatically as part of the InvenTree installation process - however (if you are configuring InvenTree from source) you may need to install it manually.

To install the invoke tool, run the following command:

```
pip install -U invoke
```

### Minimum Version

The minimum required version of the invoke tool is `{{ config.extra.min_invoke_version }}`.

To determine the version of invoke you have installed, run either:

```
invoke --version
```
```
python -m invoke --version
```

If you are running an older version of invoke, ensure it is updated to the latest version:

```
pip install -U invoke
```

### Running from Command Line

To run the `invoke` tool from the command line, you must be in the top-level InvenTree source directory. This is the directory that contains the [tasks.py]({{ sourcefile("tasks.py") }}) file.

### Running in Docker Mode

If you have installed InvenTree via [docker](./docker_install.md), then you need to ensure that the `invoke` commands are called from within the docker container context.

For example, to run the `update` task, you might use the following command to run the `invoke` command - using the `docker compose` tool.

```
docker compose run --rm inventree-server invoke update
```

!!! note "Docker Compose Directory"
    The `docker compose` command should be run from the directory where the `docker-compose.yml` file is located.

Alternatively, to manually run the command within the environment of the running docker container:

```
docker exec -it inventree-server invoke update
```

!!! note "Container Name"
    The container name may be different depending on how you have configured the docker environment.

### Running in Installer Mode

If you have installed InvenTree using the [package installer](./installer.md), then you need to prefix all `invoke` commands with `inventree run`.

For example, to run the `update` task, use:

```
inventree run invoke update
```

## Available Tasks

To display a list of the available InvenTree administration actions, run the following commands from the top level source directory:

```
invoke --list
```

This provides a list of the available invoke commands - also displayed below:

```
{{ invoke_commands() }}
```

### Task Information

Each task has a brief description of its purpose, which is displayed when running the `invoke --list` command. To find more detailed information about a specific task, run the command with the `--help` flag.

For example, to find more information about the `update` task, run:

```
invoke update --help
```

### Internal Tasks

Tasks with the `int.` prefix are internal tasks, and are not intended for general use. These are called by other tasks, and should generally not be called directly.

### Developer Tasks

Tasks with the `dev.` prefix are tasks intended for InvenTree developers, and are also not intended for general use.

## Common Issues

Below are some common issues that users may encounter when using the `invoke` tool, and how to resolve them.

### Command 'invoke' not found

If the `invoke` command does not work, it means that the invoke tool has not been [installed correctly](#installation).

### Invoke Version

If the installed version of invoke is too old, users may see error messages during the installation procedure, such as:

- *'update' did not receive all required positional arguments!*
- *Function has keyword-only arguments or annotations*

Ensure that the installed version of invoke is [up to date](#minimum-version).

### Can't find any collection named 'tasks'

It means that the `invoke` tool is not able to locate the InvenTree task collection.

- If running in docker, ensure that you are running the `invoke` command from within the [docker container](#running-in-docker-mode)
- If running in installer mode, ensure that you are running the `invoke` command with the [correct prefix](#running-in-installer-mode)
- If running via command line, ensure that you are running the `invoke` command from the [correct directory](#running-from-command-line)
