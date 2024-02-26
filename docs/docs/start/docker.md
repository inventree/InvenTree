---
title: Docker Setup
---

## Docker Installation Guide

The information on this page serves as useful theory and background information for setting up InvenTree using docker.

!!! tip "Docker Install"
    To jump right into the installation process, refer to the [docker installation guide](./docker_install.md)

## Docker Theory

The most convenient method of installing and running InvenTree is to use the official [docker image](https://hub.docker.com/r/inventree/inventree), available from docker-hub.

The InvenTree docker image contains all the required system packages, python modules, and configuration files for running a containerized InvenTree production installation.

!!! tip "Docker Compose"
    The InvenTree container requires linking with other docker containers (such as a database backend, and a file server) for complete operation. Refer to the [docker compose](#docker-compose) instructions to get up and running

!!! warning "Check the version"
    Please make sure you are reading the [STABLE](https://docs.inventree.org/en/stable/start/docker/) documentation when using the stable docker image tags.

!!! warning "Assumed Knowledge"
    A very basic understanding of [Docker](https://www.docker.com/) and [docker compose](https://docs.docker.com/compose/) is assumed, for the following setup guides.

### Tagged Images

Pre-built Docker images are available from [dockerhub](https://hub.docker.com/r/inventree/inventree) with the following tags:

| Tag | Description | Relevant documentation to follow |
| --- | --- | --- |
| **inventree:stable** | The most recent *stable* release version of InvenTree | [stable docs](https://docs.inventree.org/en/stable/start/docker/) |
| **inventree:latest** | The most up-to-date *development* version of InvenTree. | [latest docs](https://docs.inventree.org/en/latest/start/docker/) |
| **inventree:_tag_** | Specific tagged images are built for each tagged release of InvenTree, e.g. `inventree:0.7.3`| *Refer to specific InvenTree version* |

### Docker Compose

The InvenTree docker image provides a containerized webserver, however it *must* be connected with other containers to function.

### Environment Variables

InvenTree run-time configuration options described in the [configuration documentation](./config.md) can be passed to the InvenTree container as environment variables. Using environment variables simplifies setup and improves portability.

### Persistent Data

As docker containers are ephemeral, any *persistent* data must be stored in an external [volume](https://docs.docker.com/storage/volumes/). To simplify installation / implementation, all external data are stored in a single volume, arranged as follows:

#### Media FIles

Uploaded media files are stored in the `media/` subdirectory of the external data volume.

#### Static Files

Static files required by the webserver are stored in the `static/` subdirectory of the external data volume.

#### Configuration File

As discussed in the [configuration documentation](./config.md), InvenTree run-time settings can be provided in a configuration file.

By default, this file will be created as `config.yaml` in the external data volume.

#### Secret Key

InvenTree uses a secret key to provide cryptographic signing for the application.

As specified in the [configuration documentation](./config.md#secret-key) this can be passed to the InvenTree application directly as an environment variable, or provided via a file.

By default, the InvenTree container expects the secret key file to exist as `secret_key.txt` (within the external data volume). If this file does not exist, it will be created and a new key will be randomly generated.

!!! warning "Same Key"
    Each InvenTree container instance must use the same secret key value, otherwise unexpected behavior will occur.

#### Plugins

Plugins are supported natively when running under docker. There are two ways to [install plugins](../extend/plugins/install.md) when using docker:

- Install via the `plugins.txt` file provided in the external data directory
- Install into the `plugins/` subdirectory in the external data directory

## Docker Compose

[docker compose](https://docs.docker.com/compose/) is used to sequence all the required containerized processes.

### Static and Media Files

The production docker compose configuration outlined on this page uses [Caddy](https://caddyserver.com/) to serve static files and media files. If you change this configuration, you will need to ensure that static and media files are served correctly.

!!! info "Read More"
    Refer to the [Serving Files](./serving_files.md) section for more details

### Containers

The example docker compose file launches the following containers:

| Container | Description |
| --- | --- |
| inventree-db | PostgreSQL database |
| inventree-server | Gunicorn web server |
| inventree-worker | django-q background worker |
| inventree-proxy | Caddy file server and reverse proxy |
| *inventree-cache* | *redis cache (optional)* |

#### PostgreSQL Database

A PostgreSQL database container which requires a username:password combination (which can be changed). This uses the official [PostgreSQL image](https://hub.docker.com/_/postgres).

#### Web Server

Runs an InvenTree web server instance, powered by a Gunicorn web server.

#### Background Worker

Runs the InvenTree background worker process. This spins up a second instance of the *inventree* container, with a different entrypoint command.

#### File Server

Caddy working as a reverse proxy, separating requests for static and media files, and directing everything else to Gunicorn.

This container uses the official [caddy image](https://hub.docker.com/_/caddy).

#### Redis Cache

Redis is used as cache storage for the InvenTree server. This provides a more performant caching system which can useful in larger installations.

This container uses the official [redis image](https://hub.docker.com/_/redis).

!!! info "Redis on Docker"
    Docker adds an additional network layer - that might lead to lower performance than bare metal.
    To optimize and configure your redis deployment follow the [official docker guide](https://redis.io/docs/getting-started/install-stack/docker/#configuration).

!!! warning "Disabled by default"
    The *redis* container is not enabled in the default configuration. This is provided as an example for users wishing to use redis.
    To enable the *redis* container, run any `docker compose` commands with the `--profile redis` flag.
    You will also need to un-comment the `INVENTREE_CACHE_<...>` variables in the `.env` file.

### Data Volume

InvenTree stores any persistent data (e.g. uploaded media files, database data, etc) in a [volume](https://docs.docker.com/storage/volumes/) which is mapped to a local system directory. The location of this directory must be configured in the `.env` file, specified using the `INVENTREE_EXT_VOLUME` variable.

!!! info "Data Directory"
    Make sure you change the path to the local directory where you want persistent data to be stored.

## Common Issues

### Volume Mapping

When configuring a docker install, sometimes a misconfiguration can cause peculiar issues where it seems that the installation is functioning correctly, but uploaded files and plugins do not "persist" across sessions. In such cases, the "mounted" volume has not mapped to a directory on your local filesystem. This may occur if you have tried multiple setup options without clearing existing volume bindings.

!!! tip "Start with a clean slate"
    To prevent such issues, it is recommended that you start with a "clean slate" if you have previously configured an InvenTree installation under docker.

If you have previously setup InvenTree, remove existing volume bindings using the following command:

```docker volume rm -f inventree-production_inventree_data```
