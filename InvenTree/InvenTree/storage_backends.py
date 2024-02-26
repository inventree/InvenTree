"""S3 Storage backends for InvenTree."""

from django.conf import settings
from django.core.files.storage import default_storage

from storages.backends.s3boto3 import S3Boto3Storage

if settings.USE_S3:

    class S3StaticStorage(S3Boto3Storage):
        """Static assets storage for InvenTree."""

        location = settings.STATIC_LOCATION
        default_acl = 'public-read'

    class S3PublicMediaStorage(S3Boto3Storage):
        """Public media storage for InvenTree."""

        location = settings.PUBLIC_MEDIA_LOCATION
        default_acl = 'public-read'
        file_overwrite = False

    class S3PrivateMediaStorage(S3Boto3Storage):
        """Private media storage for InvenTree."""

        location = settings.PRIVATE_MEDIA_LOCATION
        default_acl = 'private'
        file_overwrite = False
        custom_domain = False

    StaticStorage = S3StaticStorage
    PublicMediaStorage = S3PublicMediaStorage
    PrivateMediaStorage = S3PrivateMediaStorage
else:
    StaticStorage = default_storage
    PublicMediaStorage = default_storage
    PrivateMediaStorage = default_storage
