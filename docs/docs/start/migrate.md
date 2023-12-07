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

The new database should now be correctly initialized with the correct table structures required to import the data. Run the following command to load the databased dump file into the new database.

!!! warning "Empty Database"
    If the database is not *empty* (i.e. it contains data records) then the data import process will fail. If errors occur during the import process, run `invoke import-records` with the `-c` option to clear all existing data from the database.

```
invoke import-records -c -f data.json
```

!!! info "Import Filename"
    A different filename can be specified using the `-f` option

!!! warning "Character Encoding"
	If the character encoding of the data file does not exactly match the target database, the import operation may not succeed. In this case, some manual editing of the database JSON file may be required.

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
