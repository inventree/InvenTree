"""Configuration options for InvenTree backup / restore functionality.

We use the django-dbbackup library to handle backup and restore operations.

Ref: https://archmonger.github.io/django-dbbackup/latest/configuration/
"""

from datetime import datetime, timedelta

from django.conf import settings

import structlog

import InvenTree.config
import InvenTree.version

logger = structlog.get_logger('inventree')


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


# schema for backup metadata
InvenTreeBackupMetadata = dict[str, str | int | bool | None]


def _gather_environment_metadata() -> InvenTreeBackupMetadata:
    """Gather metadata about the current environment to be stored with the backup."""
    import plugin.installer

    new_data: InvenTreeBackupMetadata = {}

    new_data['ivt_1_debug'] = settings.DEBUG
    new_data['ivt_1_version'] = InvenTree.version.inventreeVersion()
    new_data['ivt_1_version_api'] = InvenTree.version.inventreeApiVersion()
    new_data['ivt_1_plugins_enabled'] = settings.PLUGINS_ENABLED
    new_data['ivt_1_plugins_file_hash'] = plugin.installer.plugins_file_hash()
    new_data['ivt_1_installer'] = InvenTree.config.inventreeInstaller()
    new_data['ivt_1_backup_time'] = datetime.now().isoformat()

    return new_data


def _parse_environment_metadata(metadata: InvenTreeBackupMetadata) -> dict[str, str]:
    """Parse backup metadata to extract environment information."""
    data = {}

    data['debug'] = metadata.get('ivt_1_debug', False)
    data['version'] = metadata.get('ivt_1_version', 'unknown')
    data['version_api'] = metadata.get('ivt_1_version_api', 'unknown')
    data['plugins_enabled'] = metadata.get('ivt_1_plugins_enabled', False)
    data['plugins_file_hash'] = metadata.get('ivt_1_plugins_file_hash', 'unknown')
    data['installer'] = metadata.get('ivt_1_installer', 'unknown')
    data['backup_time'] = metadata.get('ivt_1_backup_time', 'unknown')

    return data


def metadata_set(metadata) -> InvenTreeBackupMetadata:
    """Set backup metadata for the current backup operation."""
    return _gather_environment_metadata()


def validate_restore(metadata: InvenTreeBackupMetadata) -> bool | None:
    """Validate whether a backup restore operation should proceed, based on the provided metadata."""
    if metadata.get('ivt_1_version') is None:
        logger.warning(
            'INVE-W13: Backup metadata does not contain version information',
            error_code='INVE-W13',
        )
        return True

    current_environment = _parse_environment_metadata(_gather_environment_metadata())
    backup_environment = _parse_environment_metadata(metadata)

    # Version mismatch
    if backup_environment['version'] != current_environment['version']:
        logger.warning(
            f'INVE-W13: Backup being restored was created with InvenTree version {backup_environment["version"]}, but current version is {current_environment["version"]}',
            error_code='INVE-W13',
        )

        # Backup is from newer version - fail
        try:
            if int(backup_environment['version_api']) > int(
                str(current_environment['version_api'])
            ):
                logger.error(
                    'INVE-E16: Backup being restored was created with a newer version of InvenTree - restore cannot proceed. If you are using the invoke task for your restore this warning might be overridden once with `--restore-allow-newer-version`',
                    error_code='INVE-E16',
                )
                # Check for pass flag to allow restore
                if not settings.BACKUP_RESTORE_ALLOW_NEWER_VERSION:  # defaults to False
                    return False
                else:
                    logger.warning(
                        'INVE-W13: Backup restore is allowing a restore from a newer version of InvenTree - this can lead to data loss or corruption',
                        error_code='INVE-W13',
                    )
        except ValueError:  # pragma: no cover
            logger.warning(
                'INVE-W13: Could not parse API version from backup metadata - cannot determine if backup is from newer version',
                error_code='INVE-W13',
            )

    # Plugins enabled on backup but not restore environment - warn
    if (
        backup_environment['plugins_enabled']
        and not current_environment['plugins_enabled']
    ):
        logger.warning(
            'INVE-W13: Backup being restored was created with plugins enabled, but current environment has plugins disabled - this can lead to data loss',
            error_code='INVE-W13',
        )

    # Plugins file hash mismatch - warn
    if pg_hash := backup_environment['plugins_file_hash']:
        if pg_hash != current_environment['plugins_file_hash']:
            logger.warning(
                'INVE-W13: Backup being restored has a different plugins file hash to the current environment - this can lead to data loss or corruption',
                error_code='INVE-W13',
            )

    # Installer mismatch - warn
    if installer := backup_environment['installer']:
        if installer != current_environment['installer']:
            logger.warning(
                f"INVE-W13: Backup being restored was created with installer '{installer}', but current environment has installer '{current_environment['installer']}'",
                error_code='INVE-W13',
            )

    # Age of backup
    last_backup_time = backup_environment.get('backup_time')
    if datetime.now() - datetime.fromisoformat(last_backup_time) > timedelta(days=120):
        logger.warning(
            f'INVE-W13: Backup being restored is over 120 days old (last backup time: {last_backup_time})',
            error_code='INVE-W13',
        )

    if settings.DEBUG:  # pragma: no cover
        logger.info(
            f'INVE-I3: Backup environment: {backup_environment}', error_code='INVE-I3'
        )
        logger.info(
            f'INVE-I3: Current environment: {current_environment}', error_code='INVE-I3'
        )

    return True
