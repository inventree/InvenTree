---
title: Docker Setup
---

## Docker Image

The most convenient method of installing and running InvenTree is to use the official [docker image](https://hub.docker.com/r/inventree/inventree), available from docker-hub.

The InvenTree docker image contains all the required system packages, python modules, and configuration files for running a containerised InvenTree web server.

!!! tip "Compose Yourself"
    The InvenTree container requires linking with other docker containers (such as a database backend) for complete operation. Sample [docker compose](#docker-compose) scripts are provided to get you up and running


!!! warning "Check the version"
    Please make sure you are reading the [STABLE](https://docs.inventree.org/en/stable/start/docker_prod/) documentation when using the stable docker image tags.

!!! warning "Assumed Knowledge"
    A very basic understanding of [Docker](https://www.docker.com/) and [docker compose](https://docs.docker.com/compose/) is assumed, for the following setup guides.

### Tagged Images

Pre-built Docker images are available from [dockerhub](https://hub.docker.com/r/inventree/inventree) with the following tags:

| Tag | Description | Relevant documentation to follow |
| --- | --- | --- |
| **inventree:stable** | The most recent *stable* release version of InvenTree | [stable docs](https://docs.inventree.org/en/stable/start/docker/) |
| **inventree:latest** | The most up-to-date *development* version of InvenTree. | [latest docs](https://docs.inventree.org/en/latest/start/docker/) |
| **inventree:_tag_** | Specific tagged images are built for each tagged release of InvenTree, e.g. `inventree:0.7.3`| https://docs.inventree.org/en/INSERT_YOUR_TAG_HERE/start/docker/ |

### Docker Compose

The InvenTree docker image provides a containerized webserver, however it *must* be connected with other containers (at the very least, a database backend).

InvenTree provides sample docker compose files to get you up and running:

- A [development](#development-server) compose file provides a simple way to spin up a development environment
- A [production](#production-server) compose file is intended to be used in a production environment, running the web server behind a nginx proxy.

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

## Docker Setup Guides

With these basics in mind, refer to the following installation guides:

### Production Server

Refer to the [docker production server setup guide](./docker_prod.md) for instructions on configuring a production server using docker.

### Development Server

Refer to the [docker development server setup guide](./docker_dev.md) for instructions on configuring a development server using docker.
