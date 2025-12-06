---
title: Data Backup
---

## Data Backup

Backup functionality is provided natively using the [django-dbbackup library](https://archmonger.github.io/django-dbbackup/5.0.0/). This library provides multiple options for creating backups of your InvenTree database and media files. In addition to local storage backup, multiple external storage solutions are supported (such as Amazon S3 or Dropbox).

Note that a *backup* operation is not the same as [migrating data](./migrate.md). While data *migration* exports data into a database-agnostic JSON file, *backup* exports a native database file and media file archive.

!!! warning "Database Version"
    When performing backup and restore operations, it is *imperative* that you are running from the same installed version of InvenTree. Different InvenTree versions may have different database schemas, which render backup / restore operations incompatible.

## Configuration

The django-dbbackup library provides [multiple configuration options](https://archmonger.github.io/django-dbbackup/5.0.0/configuration/), a subset of which are exposed via InvenTree.

The following configuration options are available for backup:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_BACKUP_STORAGE | backup_storage | Backup storage backend. Refer to the [storage backend documentation](#storage-backend). | django.core.files.storage.FileSystemStorage |
| INVENTREE_BACKUP_DIR | backup_dir | Backup storage directory. | *No default* |
| INVENTREE_BACKUP_OPTIONS | backup_options | Specific options for the selected storage backend (dict) | *No default* |
| INVENTREE_BACKUP_CONNECTOR_OPTIONS | backup_connector_options | Specific options for the database connector (dict). Refer to the [database connector options](#database-connector). | *No default* |
| INVENTREE_BACKUP_SEND_EMAIL | backup_send_email | If True, an email is sent to the site admin when an error occurs during a backup or restore procedure. | False |
| INVENTREE_BACKUP_EMAIL_PREFIX | backup_email_prefix | Prefix for the subject line of backup-related emails. | `[InvenTree Backup]` |
| INVENTREE_BACKUP_GPG_RECIPIENT | backup_gpg_recipient | Specify GPG recipient if using encryption for backups. | *No default* |
| INVENTREE_BACKUP_DATE_FORMAT | backup_date_format | Date format string used to format timestamps in backup filenames. | `%Y-%m-%d-%H%M%S` |
| INVENTREE_BACKUP_DATABASE_FILENAME_TEMPLATE | backup_database_filename_template | Template string used to generate database backup filenames. | `InvenTree-db-{datetime}.{extension}` |
| INVENTREE_BACKUP_MEDIA_FILENAME_TEMPLATE | backup_media_filename_template | Template string used to generate media backup filenames. | `InvenTree-media-{datetime}.{extension}` |

### Storage Backend

There are multiple backends available for storing and retrieving backup files. The default option is to use the local filesystem. Integration of other storage backends is provided by the django-storages library (which needs to be installed separately).

If you want to use an external storage provider, extra configuration is required. As a starting point, refer to the [django-dbbackup documentation](https://archmonger.github.io/django-dbbackup/5.0.0/storage/).

Each storage backend may have its own specific configuration options and package requirements. Specific storage configuration options are specified using the `backup_options` dict (in the [configuration file](./config.md#backup-file-storage)), and passed through to the storage backend.

### Database Connector

Different database connection options are available, depending on the database backend in use.

These options can be passed through via the `INVENTREE_BACKUP_CONNECTOR_OPTIONS` environment variable, or via the `backup_connector_options` value in the configuration file.

Refer to the [database connector documentation](https://archmonger.github.io/django-dbbackup/5.0.0/databases/) for more information on the available options.

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

```
{{ invoke_commands('backup --help') }}
```

### Backup During Update

When performing an update of your InvenTree installation - via either [docker](./docker.md) or [bare metal](./install.md) - a backup operation is automatically performed.

!!! info "Skip Backup Step"
    You can opt to skip the backup step during the update process by adding the `--skip-backup` option.

### Daily Backup

If desired, InvenTree can be configured to perform automated daily backups. The run-time setting to control this is found in the *Server Configuration* tab.

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

```
{{ invoke_commands('restore --help') }}
```

## View Backups

To view a list of available backups, run the following command from the shell:

```
invoke listbackups
```

## Backup Filename Formatting

There are multiple configuration options available to control the formatting of backup filenames. These options are described in the [configuration section](#configuration) above.

For more information about the available formatting options, refer to the [django-dbbackup documentation](https://archmonger.github.io/django-dbbackup/latest/configuration/#dbbackup_filename_template).

## Advanced Usage

Not all functionality of the db-backup library is exposed by default. For advanced usage (not covered by the documentation above), refer to the [django-dbbackup commands documentation](https://archmonger.github.io/django-dbbackup/5.0.0/commands/).

!!! warning "Advanced Users Only"
    Any advanced usage assumes some underlying knowledge of django, and is not documented here.

## Example: Google Cloud Storage

By default, InvenTree backups are stored on the local filesystem. However, it is possible to configure remote storage backends, such as Google Cloud Storage (GCS). Below is a *brief* example of how you might configure GCS for backup storage. However, please note that this is for informational purposes only - the InvenTree project does not provide direct support for third-party storage backends.

### External Documentation

As a starting point, refer to the external documentation for django-dbbackup: https://archmonger.github.io/django-dbbackup/latest/storage/#google-cloud-storage

### Install Dependencies

You will need to install an additional package to enable GCS support:

```bash
pip install django-storages[google]
```

!!! tip "Python Environment"
    Ensure you install the package into the same Python environment that InvenTree is installed in (e.g. virtual environment).

### Select Storage Backend

You will need to change the storage backend, which is set via the `INVENTREE_BACKUP_STORAGE` environment variable, or via `backup_storage` in the configuration file:

```yaml
backup_storage: storages.backends.gcloud.GoogleCloudStorage
```

### Configure Backend Options

You will need to also specify the required options for the GCS backend. This is done via the `INVENTREE_BACKUP_OPTIONS` environment variable, or via `backup_options` in the configuration file. An example configuration might look like:

```yaml
backup_options:
  bucket_name: 'your_bucket_name'
  project_id: 'your_project_id'
```

### Advanced Configuration

There are other options available for the GCS storage backend - refer to the [GCS documentation](https://django-storages.readthedocs.io/en/latest/backends/gcloud.html) for more information.

### Other Backends

Other storage backends are also supported via the django-storages library, such as Amazon S3, Dropbox, and more. This is outside the scope of this documentation - refer to the external documentation links on this page for more information.
