---
title: Data Backup
---

## Data Backup

Backup functionality is provided natively using the [django-dbbackup library](https://django-dbbackup.readthedocs.io/en/master/). This library provides multiple options for creating backups of your InvenTree database and media files. In addition to local storage backup, multiple external storage solutions are supported (such as Amazon S3 or Dropbox).

Note that a *backup* operation is not the same as [migrating data](./migrate.md). While data *migration* exports data into a database-agnostic JSON file, *backup* exports a native database file and media file archive.

!!! warning "Database Version"
    When performing backup and restore operations, it is *imperative* that you are running from the same installed version of InvenTree. Different InvenTree versions may have different database schemas, which render backup / restore operations incompatible.

## Configuration

The following configuration options are available for backup:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_BACKUP_STORAGE | backup_storage | Backup storage backend | django.core.files.storage.FileSystemStorage |
| INVENTREE_BACKUP_DIR | backup_dir | Backup storage directory | *No default* |
| INVENTREE_BACKUP_OPTIONS | backup_options | Specific backup options (dict) | *No default* |

### Storage Providers

If you want to use an external storage provider, extra configuration is required. As a starting point, refer to the [django-dbbackup documentation](https://django-dbbackup.readthedocs.io/en/master/storage.html).

Specific storage configuration options are specified using the `backup_options` dict (in the [configuration file](./config.md#backup-file-storage)).

## Perform Backup

#### Manual Backup

To perform a basic manual backup operation, run the following command from the shell:

```
invoke backup
```

This will perform backup operation with the default parameters. To see all available backup options, run:

```
invoke backup --help
```

### Backup During Update

When performing an update of your InvenTree installation - via either [docker](./docker.md) or [bare metal](./install.md) - a backup operation is automatically performed.

!!! info "Skip Backup Step"
    You can opt to skip the backup step during the update process by adding the `--skip-backup` option.

### Daily Backup

If desired, InvenTree can be configured to perform automated daily backups. The run-time setting to control this is found in the *Server Configuration* tab.

{% with id="auto-backup", url="start/auto-backup.png", description="Automatic daily backup" %}
{% include 'img.html' %}
{% endwith %}

!!! tip "Optional Feature"
    Automated backup is disabled by default, and must be enabled by an admin user

## Restore from Backup

To restore from a previous backup, run the following command from the shell (within virtual environment if configured):

```
invoke restore
```

To see all available options for restore, run:

```
invoke restore --help
```

## Advanced Usage

Not all functionality of the db-backup library is exposed by default. For advanced usage (not covered by the documentation above), refer to the [django-dbbackup commands documentation](https://django-dbbackup.readthedocs.io/en/master/commands.html).

!!! warning "Advanced Users Only"
    Any advanced usage assumes some underlying knowledge of django, and is not documented here.
