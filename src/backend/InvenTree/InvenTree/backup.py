"""Configuration options for InvenTree backup / restore functionality.

We use the django-dbbackup library to handle backup and restore operations.

Ref: https://archmonger.github.io/django-dbbackup/latest/configuration/
"""

import InvenTree.config
import InvenTree.ready


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
            raise ImportError(
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
