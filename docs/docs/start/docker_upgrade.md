---
title: Docker Deployment: Upgrade
---

## Updating InvenTree

Upgrading a Docker deployment consists of three basic steps: stop, pull, update.

!!! info "Working Directory"
    Unless otherwise stated, all docker commands must be run from the directory containing the [docker-compose.yml file](./docker_install.md#required-files).

### Stop Containers

Stop all running InvenTree processes.

``` bash
docker-user@localhost:~/docker-apps/InvenTree$ docker compose down
```

### Pull Latest Images

Pull down the latest version of the InvenTree docker image.

``` bash
docker-user@localhost:~/docker-apps/InvenTree$ docker compose pull
```

This will retrieve any updates on the chosen InvenTree deployment branch. Refer to [Docker Deployment: Overview - Tagged Images](./docker.md#tagged-images) for a list of available deployments. The tag can be changed to select a different deployment branch by modifying the Docker config files.

### Update the Deployment

After pulling the latest Docker images, the final step is to synchronize the local deployment with the latest InvenTree application. This step will apply any changes to the database, migrate existing data, upgrade the static files, and perform any additional steps required to complete the update. This can take several minutes - be patient and wait for the process to finish.

!!! info "Skip Backup"
    By default, the `invoke update` command performs a database backup. To skip this step, add the `--skip-backup` flag

``` bash
docker-user@localhost:~/docker-apps/InvenTree$ docker compose run --rm inventree-server invoke update
```

Note any warnings which may provide useful information, but should not affect operation. Conversely, errors require further investigation and must be remedied before proceeding.

### Start Containers

The InvenTree Docker processes can be restarted after the update process successfully completes.

!!! tip "First Run in Foreground"
    It's recommended to run in the foreground the first time after an update by omitting the '-d' option. Adding '-d' to the Docker command will 'daemonize" the process, which will start InvenTree in the background. Omitting this flag will allow important messages to be seen in case something doesn't work as expected. After verifying InvenTree is working normally, you can stop the foreground process by pressing 'ctrl+c' and restarting with the '-d' option.

``` bash
docker-user@localhost:~/docker-apps/InvenTree$ docker compose up -d
```
