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
docker compose run inventree-dev-server invoke update
docker compose run inventree-dev-server invoke setup-test --dev
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
docker compose run inventree-dev-server invoke update
```

If this is the first time you are configuring the development server, this command will build a development version of the inventree docker image.

This command also performs the following steps:

- Ensure required python packages are installed
- Perform the required schema updates to create the required database tables
- Update translation files
- Collect all required static files into a directory where they can be served by nginx

!!! info "Grab a coffee"
    This initial build process may take a few minutes!

### Import Demo Data

To fill the database with a demo dataset, run the following command:

```bash
docker compose run inventree-dev-server invoke setup-test --dev
```

### Start Docker Containers

Now that the database has been created, and migrations applied, we are ready to launch the InvenTree containers:

```bash
docker compose up -d
```

### Create Admin Account

If you are creating the initial database, you need to create an admin (superuser) account for the database. Run the command below, and follow the prompts:

!!! info "Containers must be running"
    For the `invoke superuser` command to execute properly, ensure you have run the `docker compose up -d` command.

```bash
docker compose run inventree-dev-server invoke superuser
```

This command launches the remaining containers:

- `inventree-dev-server` - InvenTree web server
- `inventree-dev-worker` - Background worker

!!! success "Check Connection"
    Check that the server is running at [http://localhost:8000](http://localhost:8000). The server may take a few minutes to be ready.

## Running commands in the container

Using `docker compose run [...]` commands creates a new container to run this specific command.
This will eventually clutter your docker with many dead containers that take up space on the system.

You can access the running containers directly with the following:
```bash
docker exec -it inventree-dev-server /bin/bash
```

You then run the following to access the virtualenv:
```bash
source data/env/bin/activate
```

This sets up a bash terminal where you can run `invoke` commands directly.

!!! warning "Tests"
    Running `invoke test` in your currently active inventree-dev-server container may result in tests taking longer than usual.

### Cleaning up old containers

If you have Docker Desktop installed, you will be able to remove containers directly in the GUI.
Your active containers are grouped under "inventree" in Docker Desktop.
The main dev-server, dev-db, and dev-worker containers are all listed without the "inventree" prefix.
One time run containers, like those executed via `docker compose run [...]` are suffixed with `run-1a2b3c4d5e6f` where the hex string varies.

To remove such containers, either click the garbage bin on the end of the line, or mark the containers, and click the delete button that shows up.
This is the recommended procedure for container cleanup.

#### Advanced cleanup
!!! warning "Advanced users only"
    This section requires good knowledge of Docker and how it operates.
    Never perform these commands if you do not understand what they do

If you're running a container with the general boilerplate commands used with invoke (invoke test, invoke update, etc) and no custom parameters or execution, you can add the `--rm` flag to `docker compose run`, and the container will delete itself when it goes down.
Do note that any data not stored in a volume, i.e. only in the container, will be lost when the container stops.

To clean out old containers using the command line, follow this guide:

Run the following command:
```bash
docker ps -a --filter status=exited
```

This gives you a list of all stopped containers.
Find the containers you wish to delete, copy the container IDs and add them to this command:

```bash
docker rm [ID1] [ID2] [IDn]
```
When executed, this removes all containers whose IDs were pasted.

!!! warning "Execute at own risk"
    The command below does not forgive errors.
    Execute this only if you know what you're doing

Running this command will remove **all** stopped one-time run InvenTree containers matching parameters:
```bash
docker container prune --filter label="com.docker.compose.oneoff=True" --filter label="com.docker.compose.service=inventree-dev-server"
```

The following output will appear:
```
WARNING! This will remove all stopped containers.
Are you sure you want to continue? [y/N] y
Deleted Containers:
[IDs of any container that was deleted, one per line]
```

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
docker compose run inventree-dev-server invoke update
```

### Docker Image Updates

Occasionally, the docker image itself may receive some updates. In these cases, it may be required that the image is rebuilt. To perform a complete rebuild of the InvenTree development image from local source, run the following command:

```
docker compose build --no-cache
```
