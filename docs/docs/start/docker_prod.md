---
title: Docker Production Server
---

## Docker Production Server

The following guide provides a streamlined production InvenTree installation, with minimal configuration required.

!!! info "Starting Point"
    This setup guide should be considered a *starting point*. It is likely that your particular production requirements will vary from the example shown here.

### Before You Start

!!! warning "Check the version"
    Please make sure you are reading the [STABLE](https://docs.inventree.org/en/stable/start/docker_prod/) documentation when using the stable docker image tags.

!!! warning "Docker Skills Required"
    This guide assumes that you are reasonably comfortable with the basic concepts of docker and docker compose.

#### Docker Image

This production setup guide uses the official InvenTree docker image, available from dockerhub.

!!! info "Stable Version"
    The provided docker compose file targets `inventree:stable` by default.

#### Docker Compose

A sample [docker compose file](https://github.com/inventree/InvenTree/blob/master/docker/production/docker-compose.yml) is provided to sequence all the required processes.

!!! tip "Starting Point"
    If you require a different configuration, use this docker compose file as a starting point.

#### Static and Media Files

The sample docker compose configuration outlined on this page uses nginx to serve static files and media files. If you change this configuration, you will need to ensure that static and media files are served correctly.

!!! info "Read More"
    Refer to the [Serving Files](./serving_files.md) section for more details

#### Required Files

The following files required for this setup are provided with the InvenTree source, located in the `./docker/production` directory of the [InvenTree source code](https://github.com/inventree/InvenTree/tree/master/docker/production):

| Filename | Description |
| --- | --- |
| [docker-compose.yml](https://github.com/inventree/InvenTree/blob/master/docker/production/docker-compose.yml) | The docker compose script |
| [.env](https://github.com/inventree/InvenTree/blob/master/docker/production/.env) | Environment variables |
| [nginx.prod.conf](https://github.com/inventree/InvenTree/blob/master/docker/production/nginx.prod.conf) | nginx proxy configuration file |

This tutorial assumes you are working from the `./docker/production` directory. If this is not the case, ensure that these required files are all located in your working directory.

!!! tip "No Source Required"
    For a production setup you do not need the InvenTree source code. Simply download the three required files from the links above!

### Containers

The example docker compose file launches the following containers:

| Container | Description |
| --- | --- |
| inventree-db | PostgreSQL database |
| inventree-server | Gunicorn web server |
| inventree-worker | django-q background worker |
| inventree-proxy | nginx proxy server |
| *inventree-cache* | *redis cache (optional)* |

#### PostgreSQL Database

A PostgreSQL database container which requires a username:password combination (which can be changed). This uses the official [PostgreSQL image](https://hub.docker.com/_/postgres).

#### Web Server

Runs an InvenTree web server instance, powered by a Gunicorn web server.

#### Background Worker

Runs the InvenTree background worker process. This spins up a second instance of the *inventree* container, with a different entrypoint command.

#### Nginx Proxy

Nginx working as a reverse proxy, separating requests for static and media files, and directing everything else to Gunicorn.

This container uses the official [nginx image](https://hub.docker.com/_/nginx).

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

#### Common Issues

When configuring a docker install, sometimes a misconfiguration can cause peculiar issues where it seems that the installation is functioning correctly, but uploaded files and plugins do not "persist" across sessions. In such cases, the "mounted" volume has not mapped to a directory on your local filesystem. This may occur if you have tried multiple setup options without clearing existing volume bindings.

!!! tip "Start with a clean slate"
    To prevent such issues, it is recommended that you start with a "clean slate" if you have previously configured an InvenTree installation under docker.

If you have previously setup InvenTree, remove existing volume bindings using the following command:

```docker volume rm -f inventree-production_inventree_data```


## Production Setup Guide

### Edit Environment Variables

The first step is to edit the environment variables, located in the `.env` file.

!!! warning "External Volume"
    You must define the `INVENTREE_EXT_VOLUME` variable - this must point to a directory *on your local machine* where persistent data is to be stored.

!!! warning "Database Credentials"
    You must also define the database username (`INVENTREE_DB_USER`) and password (`INVENTREE_DB_PASSWORD`). You should ensure they are changed from the default values for added security


### Initial Database Setup

Perform the initial database setup by running the following command:

```bash
docker compose run inventree-server invoke update
```

This command performs the following steps:

- Ensure required python packages are installed
- Create a new (empty) database
- Perform the required schema updates to create the required database tables
- Update translation files
- Collect all required static files into a directory where they can be served by nginx

### Create Administrator Account

If you are creating the initial database, you need to create an admin (superuser) account for the database. Run the command below, and follow the prompts:

```
docker compose run inventree-server invoke superuser
```

Alternatively, admin account details can be specified in the `.env` file, removing the need for this manual step:

| Variable | Description |
| --- | --- |
| INVENTREE_ADMIN_USER | Admin account username |
| INVENTREE_ADMIN_PASSWORD | Admin account password |
| INVENTREE_ADMIN_EMAIL | Admin account email address |

!!! warning "Scrub Account Data"
    Ensure that the admin account credentials are removed from the `.env` file after the first run, for security.

### Start Docker Containers

Now that the database has been created, migrations applied, and you have created an admin account, we are ready to launch the InvenTree containers:

```
docker compose up -d
```

This command launches the following containers:

- `inventree-db` - PostgreSQL database
- `inventree-server` - InvenTree web server
- `inventree-worker` - Background worker
- `inventree-nginx` - Nginx reverse proxy

!!! success "Up and Running!"
    You should now be able to view the InvenTree login screen at [http://localhost:1337](http://localhost:1337)

## Updating InvenTree

To update your InvenTree installation to the latest version, follow these steps:

### Stop Containers

Stop all running containers as below:

```
docker compose down
```

### Update Images

Pull down the latest version of the InvenTree docker image

```
docker compose pull
```

This ensures that the InvenTree containers will be running the latest version of the InvenTree source code.

!!! tip "Docker Directory"
    All `docker compose` commands must be performed in the same directory as the [docker-compose.yml file](#required-files)

!!! info "Tagged Version"
    If you are targeting a particular "tagged" version of InvenTree, you may wish to edit the `INVENTREE_TAG` variable in the `.env` file before issuing the `docker compose pull` command

### Update Database

Run the following command to ensure that the InvenTree database is updated:

```
docker compose run inventree-server invoke update
```

!!! info "Skip Backup"
    By default, the `invoke update` command performs a database backup. To skip this step, add the `--skip-backup` flag

### Start Containers

Now restart the docker containers:

```
docker compose up -d
```

## Data Backup

Database and media files are stored external to the container, in the volume location specified in the `docker-compose.yml` file. It is strongly recommended that a backup of the files in this volume is performed on a regular basis.

Read more about [data backup](./backup.md).

### Exporting Database as JSON

To export the database to an agnostic JSON file, perform the following command:

```
docker compose run inventree-server invoke export-records -f /home/inventree/data/data.json
```

This will export database records to the file `data.json` in your mounted volume directory.
