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

## Docker Installation

### Required Files

The following files required for this setup are provided with the InvenTree source, located in the `./docker/` directory of the [InvenTree source code](https://github.com/inventree/InvenTree/tree/master/docker/production):

| Filename | Description |
| --- | --- |
| [docker-compose.yml](https://github.com/inventree/InvenTree/blob/master/docker/docker-compose.yml) | The docker compose script |
| [.env](https://github.com/inventree/InvenTree/blob/master/docker/.env) | Environment variables |
| [Caddyfile](https://github.com/inventree/InvenTree/blob/master/docker/Caddyfile) | Caddy configuration file |

Download these files to a directory on your local machine.

!!! success "Working Directory"
    This tutorial assumes you are working from a direction where all of these files are located.

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

- `inventree-db` - PostgreSQL database
- `inventree-server` - InvenTree web server
- `inventree-worker` - Background worker
- `inventree-proxy` - Caddy reverse proxy

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

## Further Configuration

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

### Demo Dataset

To quickly get started with a demo dataset, you can run the following command:

```
docker compose run --rm inventree-server invoke setup-test -i
```

This will install the InvenTree demo dataset into your instance.

To start afresh (and completely remove the existing database), run the following command:

```
docker compose run --rm inventree-server invoke delete-data
```
