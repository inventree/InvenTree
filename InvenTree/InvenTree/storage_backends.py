"""S3 Storage backends for InvenTree."""

from django.conf import settings

from storages.backends.s3boto3 import S3Boto3Storage


class S3StaticStorage(S3Boto3Storage):
    """Static assets storage for InvenTree."""

    location = settings.STATIC_LOCATION
    default_acl = 'public-read'


class S3PrivateMediaStorage(S3Boto3Storage):
    """Private media storage for InvenTree."""

    location = settings.PRIVATE_MEDIA_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False
