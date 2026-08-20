---
title: InvenTree Development
---

## Introduction

If you are interested in contributing to InvenTree, then this section is for you! Here you will find information about the architecture of InvenTree, how to set up a development environment, and guidelines for contributing code or documentation.

### Architecture Overview

Read the [architecture overview](./architecture.md) to understand the high-level architecture of InvenTree, including how requests are processed, the backend and frontend architecture, and various components of the system.

### Contribution Guide

Start with the [contribution guide](./contributing.md) to understand how to get involved with the InvenTree project.

### Devcontainer Setup

We provide a [devcontainer](./devcontainer.md) configuration to help you quickly set up a development environment using vscode.

### Frontend Development

For information on developing the InvenTree frontend, refer to the [frontend development guide](./react-frontend.md).

## Profiling Tools

The InvenTree project supports integrated profiling tools to help developers analyze and optimize performance. Note that the following tools are intended for development use only and should not be enabled in production environments. In fact, they are explicitly disabled unless the server is running in [debug mode](../start/index.md#debug-mode).

### Django Silk

[django-silk](https://silk.readthedocs.io/en/latest/) is a profiling tool that can be used to monitor and analyze the performance of Django applications. It provides insights into SQL queries, request/response times, and more.

To enable django-silk profiling, ensure that the `debug_silk` option is set to `True` in your [config file](../start/config.md#configuration-file). Alternative, you can set the `INVENTREE_DEBUG_SILK` environment variable to enable this feature.

Once enabled, you can access the silk interface at the `/silk/` endpoint of your InvenTree instance.

!!! tip "Run Migrations"
    If you are enabling django-silk for the first time, you may need to run database migrations to create the necessary tables. You can do this by running `invoke migrate`.

#### Detailed Profiling

To enable detailed profiling in django-silk, set the `INVENTREE_DEBUG_SILK_PROFILING` environment variable to `True`, or set the `debug_silk_profiling` option to `True` in your config file. This will enable more granular profiling features within django-silk. Refer to the [django-silk documentation](https://github.com/jazzband/django-silk#profiling) for more information.

### Django QueryCount

Enabling the `INVENTREE_DEBUG_QUERYCOUNT` setting will log (to the terminal) the number of database queries executed for each page load. This can be useful for identifying performance bottlenecks in the InvenTree server. Note that this setting is only available if `INVENTREE_DEBUG` is also enabled.

### Database Logging

Enabling the `INVENTREE_DB_LOGGING` setting will log all database queries to the terminal. This can be useful for debugging database-related issues.

### Internal Profiling Tools

In addition to the above third-party tools, InvenTree includes some internal profiling tools that can be enabled in debug mode. These tools can be used to provide additional insights into the performance of various components of the InvenTree server.

These profiling tools can be found in `./src/backend/InvenTree/profiling.py`.
