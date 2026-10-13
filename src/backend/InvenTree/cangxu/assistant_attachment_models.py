"""Private chat uploads, separate from formally archived business attachments."""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

from InvenTree.config import get_setting


class PrivateChatStorage(FileSystemStorage):
    """Never produce an unauthenticated media URL for a conversation file."""

    def url(self, name):
        """All reads must pass the authenticated chat endpoint."""
        raise ValueError('Private assistant files have no public URL')


def private_chat_storage():
    """Keep uploads outside the public MEDIA_ROOT by default."""
    root = get_setting(
        'ASSISTANT_ATTACHMENT_ROOT', 'assistant_attachment_root', '', typecast=str
    )
    return PrivateChatStorage(
        location=root or Path(settings.MEDIA_ROOT).parent / 'assistant-private',
        file_permissions_mode=0o600,
        directory_permissions_mode=0o700,
    )


def private_chat_path(instance, filename):
    """Client filenames never participate in filesystem paths."""
    return (
        f'{instance.binding.deployment_id}/{instance.binding.partner_id}/{instance.id}'
    )


class AssistantChatAttachment(models.Model):
    """A per-partner private upload with content digest and stable upload identity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    binding = models.ForeignKey(
        'cangxu.PartnerBinding',
        on_delete=models.CASCADE,
        related_name='chat_attachments',
    )
    client_upload_id = models.CharField(max_length=200)
    file = models.FileField(storage=private_chat_storage, upload_to=private_chat_path)
    name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    kind = models.CharField(max_length=20)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Retry keys are unique only within their owner's deployment binding."""

        constraints = [
            models.UniqueConstraint(
                fields=['binding', 'client_upload_id'],
                name='assistant_upload_key_unique',
            )
        ]
