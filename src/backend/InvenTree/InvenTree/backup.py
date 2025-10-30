"""Configuration options for InvenTree backup / restore functionality.

We use the django-dbbackup library to handle backup and restore operations.

Ref: https://archmonger.github.io/django-dbbackup/latest/configuration/
"""

import InvenTree.config


def get_backup_connector_options() -> dict:
    """Options which are specific to the selected backup connector.

    These options apply to the database connector, not to the backup storage.

    Ref: https://archmonger.github.io/django-dbbackup/latest/databases/
    """
    default_options = {'EXCLUDE': ['django_session']}

    # Allow user to specify custom options here if necessary
    connector_options = InvenTree.config.get_setting(
        'INVENTREE_BACKUP_CONNECTOR_OPTIONS',
        'backup_connector_options',
        default_value={},
        typecast=dict,
    )

    return {**default_options, **connector_options}


def get_backup_storage_backend() -> str:
    """Return the backup storage backend string."""
    backend = InvenTree.config.get_setting(
        'INVENTREE_BACKUP_STORAGE',
        'backup_storage',
        'django.core.files.storage.FileSystemStorage',
    )

    # Validate that the selected backend is valid
    # It must be able to be imported, and a class must be found
    # It also must be a subclass of django.core.files.storage.Storage
    try:
        from django.core.files.storage import Storage
        from django.utils.module_loading import import_string

        backend_class = import_string(backend)

        if not issubclass(backend_class, Storage):
            raise TypeError(
                f"Backup storage backend '{backend}' is not a valid Storage class"
            )
    except Exception as e:
        raise ImportError(f"Could not load backup storage backend '{backend}': {e}")

    return backend


def get_backup_storage_options() -> dict:
    """Return the backup storage options dictionary."""
    # Default backend options which are used for FileSystemStorage
    default_options = {'location': InvenTree.config.get_backup_dir()}

    options = InvenTree.config.get_setting(
        'INVENTREE_BACKUP_OPTIONS',
        'backup_options',
        default_value=default_options,
        typecast=dict,
    )

    if not isinstance(options, dict):
        raise ValueError('Backup storage options must be a dictionary')

    return options


def backup_email_on_error() -> bool:
    """Return whether to send emails to admins on backup failure."""
    return InvenTree.config.get_setting(
        'INVENTREE_BACKUP_SEND_EMAIL',
        'backup_send_email',
        default_value=False,
        typecast=bool,
    )


def backup_email_prefix() -> str:
    """Return the email subject prefix for backup emails."""
    return InvenTree.config.get_setting(
        'INVENTREE_BACKUP_EMAIL_PREFIX',
        'backup_email_prefix',
        default_value='[InvenTree Backup]',
        typecast=str,
    )


def backup_gpg_recipient() -> str:
    """Return the GPG recipient for encrypted backups."""
    return InvenTree.config.get_setting(
        'INVENTREE_BACKUP_GPG_RECIPIENT',
        'backup_gpg_recipient',
        default_value='',
        typecast=str,
    )


def backup_date_format() -> str:
    """Return the date format string for database backups."""
    return InvenTree.config.get_setting(
        'INVENTREE_BACKUP_DATE_FORMAT',
        'backup_date_format',
        default_value='%Y-%m-%d-%H%M%S',
        typecast=str,
    )


def backup_filename_template() -> str:
    """Return the filename template for database backups."""
    return InvenTree.config.get_setting(
        'INVENTREE_BACKUP_DATABASE_FILENAME_TEMPLATE',
        'backup_database_filename_template',
        default_value='InvenTree-db-{datetime}.{extension}',
        typecast=str,
    )


def backup_media_filename_template() -> str:
    """Return the filename template for media backups."""
    return InvenTree.config.get_setting(
        'INVENTREE_BACKUP_MEDIA_FILENAME_TEMPLATE',
        'backup_media_filename_template',
        default_value='InvenTree-media-{datetime}.{extension}',
        typecast=str,
    )
