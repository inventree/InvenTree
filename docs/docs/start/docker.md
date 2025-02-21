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

#### Media Files

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
    Refer to the [proxy server documentation](./processes.md#proxy-server) for more details

### SSL Certificates

The provided `Caddyfile` configuration file is setup to enable [Automatic HTTPS](https://caddyserver.com/docs/automatic-https) by default! All you have to do is specify a `https://` URL in the `INVENTREE_SITE_URL` variable.

### Containers

The example docker compose file launches the following containers:

| Container | Description |
| --- | --- |
| inventree-db | [PostgreSQL database](./processes.md#database) |
| inventree-server | [InvenTree web server](./processes.md#web-server) |
| inventree-worker | [django-q background worker](./processes.md#background-worker) |
| inventree-proxy | [Caddy file server and reverse proxy](./processes.md#proxy-server) |
| *inventree-cache* | [*redis cache (optional)*](./processes.md#cache-server) |

### Data Volume

InvenTree stores any persistent data (e.g. uploaded media files, database data, etc) in a [volume](https://docs.docker.com/storage/volumes/) which is mapped to a local system directory. The location of this directory must be configured in the `.env` file, specified using the `INVENTREE_EXT_VOLUME` variable.

!!! info "Data Directory"
    Make sure you change the path to the local directory where you want persistent data to be stored.

### Database Connection

The `inventree-db` container is configured to use the `postgres:{{ config.extra.docker_postgres_version }}` docker image.

Connecting to a different database container is entirely possible, but requires modification of the `docker-compose.yml` file. This is outside the scope of this documentation.

#### Postgres Version

The `inventree-server` and `inventree-worker` containers support connection to a postgres database up to (and including) version {{ config.extra.docker_postgres_version }}.

!!! warning "Newer Postgres Versions"
    The InvenTree docker image supports connection to a postgres database up to version {{ config.extra.docker_postgres_version }}. Connecting to a database using a newer version of postgres is not guaranteed.

#### Bypassing Backup Procedure

If you are connecting the docker container to a postgresql database newer than version `{{ config.extra.docker_postgres_version }}`, the [backup and restore commands](../start/backup.md) will fail due to a version mismatch. To bypass this issue when performing the `invoke update` command, add the `--skip-backup` flag.

## Common Issues

### Volume Mapping

When configuring a docker install, sometimes a misconfiguration can cause peculiar issues where it seems that the installation is functioning correctly, but uploaded files and plugins do not "persist" across sessions. In such cases, the "mounted" volume has not mapped to a directory on your local filesystem. This may occur if you have tried multiple setup options without clearing existing volume bindings.

!!! tip "Start with a clean slate"
    To prevent such issues, it is recommended that you start with a "clean slate" if you have previously configured an InvenTree installation under docker.

If you have previously setup InvenTree, remove existing volume bindings using the following command:

```docker volume rm -f inventree-production_inventree_data```
