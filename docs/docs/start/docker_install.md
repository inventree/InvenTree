---
title: Docker Production Server
---

## Docker Production Server

The following guide provides a streamlined production InvenTree installation, with minimal configuration required.

!!! tip "Docker Installation"
    This guide assumes that you have already installed [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/). If you have not yet installed Docker, please refer to the [official installation guide](https://docs.docker.com/get-docker/).

!!! info "Starting Point"
    This setup guide should be considered a *starting point* - your particular production requirements vary from the example shown here.

!!! tip "Docker Theory"
    Refer to the [docker theory section](./docker.md) for more information about how our docker installation works under the hood.

### Before You Start

!!! warning "Check the version"
    Please make sure you are reading the [STABLE](https://docs.inventree.org/en/stable/start/docker/) documentation when using the stable docker image tags.

!!! warning "Docker Knowledge Required"
    This guide assumes that you are reasonably comfortable with the basic concepts of docker and docker compose.

### Frequently Asked Questions

If you encounter any issues during the installation process, please refer first to the [FAQ](../faq.md) for common problems and solutions.

## Docker Installation

### Required Files

The following files required for this setup are provided with the InvenTree source, located in the `contrib/container/` directory of the [InvenTree source code]({{ sourcedir("/contrib/container/") }}):

| Filename | Description |
| --- | --- |
| [docker-compose.yml]({{ sourcefile("contrib/container/docker-compose.yml", raw=True) }}) | The docker compose script |
| [.env]({{ sourcefile("contrib/container/.env", raw=True) }}) | Environment variables |
| [Caddyfile]({{ sourcefile("contrib/container/Caddyfile", raw=True) }}) | Caddy configuration file |

Download these files to a directory on your local machine.

!!! warning "File Extensions"
    If your computer adds *.txt* extensions to any of the downloaded files, rename the file and remove the added extension before continuing!

!!! success "Working Directory"
    This tutorial assumes you are working from a directory where all of these files are located.

!!! tip "No Source Required"
    For a production setup you do not need the InvenTree source code. Simply download the three required files from the links above!

### Edit Environment Variables

The first step is to edit the environment variables, located in the `.env` file.

!!! warning "External Volume"
    You must define the `INVENTREE_EXT_VOLUME` variable - this must point to a directory *on your local machine* where persistent data is to be stored.

!!! warning "Database Credentials"
    You must also define the database username (`INVENTREE_DB_USER`) and password (`INVENTREE_DB_PASSWORD`). You should ensure they are changed from the default values for added security

!!! info "Other Variables"
    There are a number of other environment variables which can be set to customize the InvenTree installation. Refer to the [environment variables](./config.md) documentation for more information.

### Initial Database Setup

Perform the initial database setup by running the following command:

```bash
docker compose run --rm inventree-server invoke update
```

This command performs the following steps:

- Ensure required python packages are installed
- Create a new (empty) database
- Perform the required schema updates to create the required database tables
- Update translation files
- Update required static files

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

- `inventree-db` - [PostgreSQL database](./processes.md#database)
- `inventree-server` - [InvenTree web server](./processes.md#web-server)
- `inventree-worker` - [Background worker](./processes.md#background-worker)
- `inventree-proxy` - [Caddy reverse proxy](./processes.md#proxy-server)
- `inventree-cache` - [Redis cache](./processes.md#cache-server)

!!! success "Up and Running!"
    You should now be able to view the InvenTree login screen at [http://inventree.localhost](http://inventree.localhost) (or whatever custom domain you have configured in the `.env` file).

!!! tip "External Access"
    Note that `http://inventree.localhost` will only be available from the machine you are running the code on. To make it accessible externally, change `INVENTREE_SITE_URL` to a host address which can be accessed by other computers on your network.

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
docker compose run --rm inventree-server invoke update
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
docker compose run --rm inventree-server invoke export-records -f /home/inventree/data/data.json
```

This will export database records to the file `data.json` in your mounted volume directory.

## Viewing Logs

To view the logs for the InvenTree container(s), use the following command:

```bash
docker compose logs
```

To view the logs for a specific container, use the following command:

```bash
docker compose logs <container-name>
```

e.g.

```bash
docker compose logs inventree-server
```

You can also "follow" the logs in real time, using the `-f` flag:

```bash
docker compose logs -f
```

## Further Configuration

### Check your security posture

It is recommended to check the [threat modelling inputs](../concepts/threat_model.md) to ensure that your InvenTree installation is set up in the way that it is assumed in the software design.

### Custom Domain

By default, the InvenTree server is accessible at [http://inventree.localhost](http://inventree.localhost). If you wish to use a custom domain, you can edit the `.env` environment file to specify the domain name.

Look for the `INVENTREE_SITE_URL` variable, and set it to the desired domain name.

!!! tip "Configuration Options"
    There are a number of other environment variables which can be set to customize the InvenTree installation. Refer to the [configuration documentation](./config.md) for more information.

### SSL Configuration

The provided `Caddyfile` configuration file is setup to enable [Automatic HTTPS](https://caddyserver.com/docs/automatic-https) "out of the box". All you have to do is specify a `https://` URL in the `INVENTREE_SITE_URL` variable.


The [Caddy](./docker.md#ssl-certificates) container will automatically generate SSL certificates for your domain.

#### Persistent Files

Any persistent files generated by the Caddy container (such as certificates, etc) will be stored in the `caddy` directory within the external volume.

### Web Server Bind Address

By default, the Dockerized InvenTree web server binds to all available network interfaces and listens for IPv4 traffic on port 8000.
This can be adjusted using the following environment variables:

| Environment Variable | Default |
| --- | --- | --- | --- |
| INVENTREE_WEB_ADDR | 0.0.0.0 |
| INVENTREE_WEB_PORT | 8000 |

These variables are combined in the [Dockerfile]({{ sourcefile("contrib/container/Dockerfile") }}) to build the bind string passed to the InvenTree server on startup.

!!! tip "IPv6 Support"
    To enable IPv6/Dual Stack support, set `INVENTREE_WEB_ADDR` to `[::]` when you create/start the container.

### Demo Dataset

To quickly get started with a [demo dataset](../demo.md), you can run the following command:

```
docker compose run --rm inventree-server invoke dev.setup-test -i
```

This will install the InvenTree demo dataset into your instance.

To start afresh (and completely remove the existing database), run the following command:

```
docker compose run --rm inventree-server invoke dev.delete-data
```

## Install custom packages

To install custom packages to your docker image, a custom docker image can be built and used automatically each time when updating. The following changes need to be applied to the docker compose file:

<details><summary>docker-compose.yml changes</summary>

```diff
diff --git a/docker-compose.yml b/docker-compose.yml
index 8adee63..dc3993c 100644
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -69,7 +69,14 @@ services:
     # Uses gunicorn as the web server
     inventree-server:
         # If you wish to specify a particular InvenTree version, do so here
-        image: inventree/inventree:${INVENTREE_TAG:-stable}
+        image: inventree/inventree:${INVENTREE_TAG:-stable}-custom
+        pull_policy: never
+        build:
+          context: .
+          dockerfile: Dockerfile
+          target: production
+          args:
+            INVENTREE_TAG: ${INVENTREE_TAG:-stable}
         # Only change this port if you understand the stack.
         # If you change this you have to change:
         # - the proxy settings (on two lines)
@@ -88,7 +95,8 @@ services:
     # Background worker process handles long-running or periodic tasks
     inventree-worker:
         # If you wish to specify a particular InvenTree version, do so here
-        image: inventree/inventree:${INVENTREE_TAG:-stable}
+        image: inventree/inventree:${INVENTREE_TAG:-stable}-custom
+        pull_policy: never
         command: invoke worker
         depends_on:
             - inventree-server
```

</details>

And the following `Dockerfile` needs to be created:

<details><summary>Dockerfile</summary>

```dockerfile
ARG INVENTREE_TAG

FROM inventree/inventree:${INVENTREE_TAG} as production

# Install whatever dependency is needed here (e.g. git)
RUN apk add --no-cache git
```

</details>

And if additional, development packages are needed e.g. just for building a wheel for a pip package, a multi stage build can be used with the following `Dockerfile`:

<details><summary>Dockerfile</summary>

```dockerfile
ARG INVENTREE_TAG

# prebuild stage - needs a lot of build dependencies
# make sure, the alpine and python version matches the version used in the inventree base image
FROM python:3.11-alpine3.18 as prebuild

# Install whatever development dependency is needed (e.g. cups-dev, gcc, the musl-dev build tools and the pip pycups package)
RUN apk add --no-cache cups-dev gcc musl-dev && \
    pip install --user --no-cache-dir pycups

# production image - only install the cups shared library
FROM inventree/inventree:${INVENTREE_TAG} as production

# Install e.g. shared library later available in the final image
RUN apk add --no-cache cups-libs

# Copy the pip wheels from the build stage in the production stage
COPY --from=prebuild /root/.local /root/.local
```

</details>
