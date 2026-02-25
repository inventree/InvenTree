---
title: Migrating Data
---

## Migrating Data to a Different Database

In the case that data needs to be migrated from one database installation to another, the following procedure can be used to export data, initialize the new database, and re-import the data. The following instructions apply to bare-metal and docker installations, although the particular commands required may vary slightly in each case.

!!! warning "Backup Database"
	Ensure that the original database is securely backed up first!

!!! danger "Database Versions"
    It is *crucial* that both InvenTree database installations are running the same version of InvenTree software! If this is not the case, data migration may fail, and there is a possibility that data corruption can occur. Ensure that the original database is up to date, by running `invoke update`.

### Export Data

Export the database contents to a JSON file using the following command:

```
invoke export-records -f data.json
```

When using docker the command above would produce output inside the ephemeral container. To make sure your JSON file persists in the docker volume used for backups use the following command:

```
docker compose run inventree-server invoke export-records -f data/backup/data.json
```

This will create JSON file at the specified location which contains all database records.

!!! info "Specifying filename"
    The filename of the exported file can be specified using the `-f` option. To see all available options, run `invoke export-records --help`

```
{{ invoke_commands('export-records --help') }}
```

### Initialize New Database

Configure the new database using the normal processes (see [Configuration](./config.md))

!!! warning "InvenTree Version"
    Ensure that the *new* installation is running *exactly* the same version of InvenTree as the installation from which you exported the data.

Then, ensure that the database schema are correctly initialized in the new database:

```
invoke update
```

This step ensures that the required database tables exist, and are at the correct schema version, which must be the case before data can be imported.

### Import Data

The new database should now be correctly initialized with the correct table structures required to import the data. Run the following command to load the database dump file into the new database.

!!! warning "Empty Database"
    If the database is not *empty* (i.e. it contains data records) then the data import process will fail. If errors occur during the import process, run `invoke import-records` with the `-c` option to clear all existing data from the database.

```
invoke import-records -c -f data.json
```

!!! info "Import Filename"
    A different filename can be specified using the `-f` option

!!! warning "Character Encoding"
	If the character encoding of the data file does not exactly match the target database, the import operation may not succeed. In this case, some manual editing of the database JSON file may be required.

### Copy Media Files

Any media files (images, documents, etc) that were stored in the original database must be copied to the new database. In a typical InvenTree installation, these files are stored in the `media` subdirectory of the InvenTree data location.

Copy the entire directory tree from the original InvenTree installation to the new InvenTree installation.

!!! warning "File Ownership"
    Ensure that the file ownership and permissions are correctly set on the copied files. The InvenTree server process **must** have read / write access to these files. If not, the server will not be able to serve the media files correctly, and the user interface may not function as expected.

!!! warning "Directory Structure"
    The expected locations of each file is stored in the database, and if the file paths are not correct, the media files will not be displayed correctly in the user interface. Thus, it is important that the files are transferred across to the new installation in the same directory structure.

## Migrating Data to Newer Version

If you are updating from an older version of InvenTree to a newer version, the migration steps outlined above *do not apply*.

An update from an old version to a new one requires not only that the database *schema* are updated, but the *data* held within the database must be updated in the correct sequence.

Follow the sequence of steps below to ensure that the database records are updated correctly.

!!! warning "Backup Database"
	When updating, it is always prudent to ensure that the database records are backed up first

### Stop InvenTree

Ensure that the InvenTree server and worker processes are not running.

!!! tip "Example: Docker"
    If running under docker, run `docker compose down`

### Fetch New InvenTree Version

Download the specific version of InvenTree you wish to update to.

!!! tip "Example: Docker"
    If running under docker, edit `docker-compose.yml` and then run `docker compose pull`

### Run Update Process

Run the update and migration script using `invoke update`. This ensures that the database schema and records are updated in the correct order.

### Restart Server

Once the migration process completes, the database records are now updated! Restart the server and the process is complete.

!!! tip "Example: Docker"
    If running under docker, run `docker compose up -d`

## Migrating Between Incompatible Database Versions

There may be occasions when InvenTree data needs to be migrated between two database installations running *incompatible* versions of the database software. For example, InvenTree may be running on a Postgres database running on version 12, and the administrator wishes to migrate the data to a Postgres version {{ config.extra.docker_postgres_version }} database.

!!! warning "Advanced Procedure"
    The following procedure is *advanced*, and should only be attempted by experienced database administrators. Always ensure that database backups are made before attempting any migration procedure.

Due to inherit incompatibilities between different major versions of database software, it is not always possible to directly migrate data between two different database versions. In such cases, the following procedure can be used as a workaround.

!!! warning "InvenTree Version"
    It is *crucial* that both InvenTree database installations are running the same version of InvenTree software! If this is not the case, data migration may fail, and there is a possibility that data corruption can occur. Ensure that the original database is up to date, by running `invoke update`.

The following instructions assume that the source (old) database is Postgres version 15, and the target (new) database is Postgres version {{ config.extra.docker_postgres_version }}. Additionally, it assumes that the InvenTree installation is running under [docker / docker compose](./docker.md), for simplicity. Adjust commands as required for other InvenTree configurations or database software.

The overall procedure is as follows:

### Backup Old Database

Run the following command to create a backup dump of the old database:

```
docker compose run --rm inventree-server invoke backup
```

This will create a database backup file in the InvenTree backup directory.

!!! tip "Secondary Backup"
    It may be prudent to create a secondary backup of the database, separate to the one created by InvenTree.

### Shutdown Old Database

Stop the old InvenTree installation, to ensure that the database is not being accessed during the migration process:

```
docker compose down
```

### Remove Old Database Files

The raw database files are incompatible between different major versions of Postgres. Thus, the old database files must be removed before starting the new database. Rather than removing the database directory, we will move the database files to a temporary location, just in case we need to revert back to the old database.

!!! warning "Data Loss"
    Ensure that a complete backup of the old database has been made before proceeding! Removing the database files will result in data loss if a backup does not exist.

```
mv ./path/to/database ./path/to/database_backup
```

!!! info "Database Location"
    The location of the database files depends on how InvenTree was configured.

### Start New Database

Update the InvenTree docker configuration to use the new version of Postgres (e.g. `postgres:{{ config.extra.docker_postgres_version }}`), and then start the InvenTree installation:

```
docker compose up -d
```

This will initialize a new, empty database using the new version of Postgres.

### Run Database Migrations

Run the database migration process to ensure that the new database schema is correctly initialized:

```
docker compose run --rm inventree-server invoke update
```

### Restore Database Backup

Finally, restore the database backup created earlier into the new database:

```
docker compose run --rm inventree-server invoke restore
```

This will load the database records from the backup file into the new database.

### Caveats

The process described here is a *suggested* procedure for migrating between incompatible database versions. However, due to the complexity of database software, there may be unforeseen complications that arise during the process.
