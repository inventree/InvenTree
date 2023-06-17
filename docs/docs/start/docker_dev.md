---
title: Docker Development Server
---

## Docker Development Server

You can use docker to launch and manage a development server, in a similar fashion to managing a production server.

The InvenTree dockerfile (`./Dockerfile`) uses a [multi-stage build](https://docs.docker.com/develop/develop-images/multistage-build/) process to allow both production and development setups from the same image.

There are some key differences compared to the [docker production setup](./docker_prod.md):

- The docker image is built locally, rather than being downloaded from DockerHub
- The docker image points to the source code on your local machine (mounted as a 'volume' in the docker container)
- The django webserver is used, instead of running behind Gunicorn
- The server will automatically reload when code changes are detected

!!! info "Static and Media Files"
    The development server runs in DEBUG mode, and serves static and media files natively.

!!! info "Hacker Mode"
    The following setup guide starts a development server which will reload "on the fly" as changes are made to the source code. This is designed for programmers and developers who wish to add and test new InvenTree features.

### Data Directory

Persistent data (such as the stored database, media files, configuration files, etc) will be stored in the `./data` directory (relative to the InvenTree source code directory).

- This directory is automatically created when you launch InvenTree via docker
- This directory is excluded from git version tracking

## Quickstart Guide

To get "up and running" with a development environment, complete with a set of [demo data](https://github.com/inventree/demo-dataset) to work with, run the following commands:

```bash
git clone https://github.com/inventree/InvenTree.git && cd InvenTree
docker compose run --rm inventree-dev-server invoke install
docker compose run --rm inventree-dev-server invoke setup-test --dev
docker compose up -d
```

!!! tip "Development Server"
    You can then view the development server at [http://localhost:8000](http://localhost:8000)

!!! info "Details, details"
    For a more in-depth setup guide, continue reading below!

## Development Setup Guide

To get started with an InvenTree development setup, follow the simple steps outlined below. Before continuing, ensure that you have completed the following steps:

- Downloaded the InvenTree source code to your local machine
- Installed docker on your local machine (install *Docker Desktop* on Windows)
- Have a terminal open to the root directory of the InvenTree source code

### Edit Environment Variables (Optional)

If desired, the user may edit the environment variables, located in the `.env` file.

!!! success "This step is optional"
    This step can be skipped, as the default variables will work just fine!

!!! info "Database Credentials"
    You may also wish to change the database username (`INVENTREE_DB_USER`) and password (`INVENTREE_DB_PASSWORD`) from their default values

### Perform Initial Setup

Perform the initial database setup by running the following command:

```bash
docker compose run --rm inventree-dev-server invoke update
```

If this is the first time you are configuring the development server, this command will build a development version of the inventree docker image.

This command also performs the following steps:

- Ensure required python packages are installed
- Perform the required schema updates to create the required database tables
- Update translation files
- Collect all required static files into a directory where they can be served by nginx

!!! info "Grab a coffee"
    This initial build process may take a few minutes!

### Create Admin Account

If you are creating the initial database, you need to create an admin (superuser) account for the database. Run the command below, and follow the prompts:

```
docker compose run  -rm inventree-dev-server invoke superuser
```

### Import Demo Data

To fill the database with a demo dataset, run the following command:

```
docker compose run --rm inventree-dev-server invoke setup-test --dev
```

### Start Docker Containers

Now that the database has been created, migrations applied, and you have created an admin account, we are ready to launch the InvenTree containers:

```
docker compose up -d
```

This command launches the remaining containers:

- `inventree-dev-server` - InvenTree web server
- `inventree-dev-worker` - Background worker

!!! success "Check Connection"
    Check that the server is running at [http://localhost:8000](http://localhost:8000). The server may take a few minutes to be ready.

## Restarting Services

Once initial setup is complete, stopping and restarting the services is much simpler:

### Stop InvenTree Services

To stop the InvenTree development server, simply run the following command:

```
docker compose down
```

### Start InvenTree Services

To start the InvenTree development server, simply run the following command:

```
docker compose up -d
```

### Restart InvenTree Services

A restart cycle is as simple as:

```
docker compose restart
```

## Editing InvenTree Source

Any changes made to the InvenTree source code are automatically detected by the services running under docker.

Thus, you can freely edit the InvenTree source files in your editor of choice.

### Database Updates

Any updates which require a database schema change must be reflected in the database itself.

To run database migrations inside the docker container, run the following command:

```
docker compose run --rm inventree-dev-server invoke update
```

### Docker Image Updates

Occasionally, the docker image itself may receive some updates. In these cases, it may be required that the image is rebuilt. To perform a complete rebuild of the InvenTree development image from local source, run the following command:

```
docker compose build --no-cache
```
