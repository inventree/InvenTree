"""S3 Storage backends for InvenTree."""

from django.conf import settings
from django.core.files.storage import get_storage_class

from storages.backends.s3boto3 import S3Boto3Storage


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


static_storage = get_storage_class(settings.STATICFILES_STORAGE)()
public_storage = get_storage_class(settings.DEFAULT_FILE_STORAGE)()
private_storage = get_storage_class(settings.PRIVATE_FILE_STORAGE)()
