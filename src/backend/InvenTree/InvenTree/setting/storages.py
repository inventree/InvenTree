"""Settings for storage backends."""

from enum import Enum
from typing import Optional

from InvenTree.config import get_boolean_setting, get_setting


class StorageBackends(str, Enum):
    """Enumeration of available storage backends."""

    LOCAL = 'local'
    S3 = 's3'
    SFTP = 'sftp'


STORAGE_BACKEND_MAPPING = {
    StorageBackends.LOCAL: 'django.core.files.storage.FileSystemStorage',
    StorageBackends.S3: 'storages.backends.s3.S3Storage',
    StorageBackends.SFTP: 'storages.backends.sftpstorage.SFTPStorage',
}


def init_storages() -> tuple[str, dict, Optional[str]]:
    """Initialize storage backend settings."""
    target = get_setting(
        'INVENTREE_STORAGE_TARGET',
        'storage.target',
        StorageBackends.LOCAL.value,
        typecast=str,
    )

    # Check that the target is valid
    if target not in STORAGE_BACKEND_MAPPING:
        raise ValueError(f"Invalid storage target: '{target}'")

    options = {}
    media_url: Optional[str] = None
    if target == StorageBackends.S3:
        s3_bucket = get_setting(
            'INVENTREE_S3_BUCKET_NAME', 'storage.s3.bucket_name', None, typecast=str
        )
        s3_acl = get_setting(
            'INVENTREE_S3_DEFAULT_ACL', 'storage.s3.default_acl', None, typecast=str
        )
        s3_endpoint = get_setting(
            'INVENTREE_S3_ENDPOINT_URL', 'storage.s3.endpoint_url', None, typecast=str
        )
        s3_location = get_setting(
            'INVENTREE_S3_LOCATION',
            'storage.s3.location',
            'inventree-server',
            typecast=str,
        )

        media_url = f'{s3_endpoint}/{s3_bucket}/{s3_location}/'
        options = {
            'access_key': get_setting(
                'INVENTREE_S3_ACCESS_KEY', 'storage.s3.access_key', None, typecast=str
            ),
            'secret_key': get_setting(
                'INVENTREE_S3_SECRET_KEY', 'storage.s3.secret_key', None, typecast=str
            ),
            'bucket_name': s3_bucket,
            'default_acl': s3_acl,
            'region_name': get_setting(
                'INVENTREE_S3_REGION_NAME', 'storage.s3.region_name', None, typecast=str
            ),
            'endpoint_url': s3_endpoint,
            'verify': get_boolean_setting(
                'INVENTREE_S3_VERIFY_SSL', 'storage.s3.verify_ssl', True
            ),
            'location': s3_location,
            'file_overwrite': get_boolean_setting(
                'INVENTREE_S3_OVERWRITE', 'storage.s3.overwrite', True
            ),
            'addressing_style': 'virtual'
            if get_boolean_setting('INVENTREE_S3_VIRTUAL', 'storage.s3.virtual', False)
            else 'path',
            'object_parameters': {'CacheControl': 'public,max-age=86400'},
        }
    elif target == StorageBackends.STFP:
        options = {
            'host': get_setting('INVENTREE_SFTP_HOST', 'sftp.host', None, typecast=str),
            'uid': get_setting('INVENTREE_SFTP_UID', 'sftp.uid', None, typecast=int),
            'gid': get_setting('INVENTREE_SFTP_GID', 'sftp.gid', None, typecast=int),
            'location': get_setting(
                'INVENTREE_SFTP_LOCATION',
                'sftp.location',
                'inventree-server',
                typecast=str,
            ),
            'params': get_setting(
                'INVENTREE_SFTP_PARAMS', 'sftp.params', {}, typecast=dict
            ),
        }
    return (
        target,
        {
            'default': {
                'BACKEND': STORAGE_BACKEND_MAPPING.get(
                    target, STORAGE_BACKEND_MAPPING[StorageBackends.LOCAL]
                ),
                'OPTIONS': options,
            },
            'staticfiles': {
                'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'
            },
        },
        media_url,
    )
