"""Explicitly copy a private chat upload into the native business attachment API."""

import hashlib
import json
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import resolve
from django.utils import timezone

from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.test import APIRequestFactory, force_authenticate

from common.serializers import check_model_change_permission
from common.validators import attachment_model_class_from_label
from InvenTree.models import InvenTreeAttachmentMixin

from .assistant_attachment_models import AssistantChatAttachment
from .assistant_attachments import FILE_LIMIT

TARGETS = {
    'part': ('part', 'parts'),
    'stock': ('stockitem', 'stock'),
    'purchase_order': ('purchaseorder', 'purchase_orders'),
    'purchase_receipt': ('purchasereceipt', 'purchase_receipts'),
    'build': ('build', 'builds'),
    'sales_order': ('salesorder', 'sales_orders'),
    'shipment': ('salesordershipment', 'shipments'),
}


def promotion_target(user, data):
    """Resolve one finite native target and its existing change/read permissions."""
    from .assistant_business_tools import RESOURCES, _original_api

    object_type, object_id = data.get('object_type'), data.get('object_id')
    if (
        not isinstance(object_type, str)
        or object_type not in TARGETS
        or type(object_id) is not int
        or object_id < 1
    ):
        raise ValidationError(
            'Choose an explicit supported business object type and positive ID'
        )
    label, resource = TARGETS[object_type]
    model = attachment_model_class_from_label(label)
    try:
        check_model_change_permission(
            user,
            model,
            InvenTreeAttachmentMixin,
            'This business object does not support attachments',
            'Current business role cannot attach files to this object',
        )
    except DRFPermissionDenied as exc:
        raise PermissionDenied(
            'Current business role cannot attach files to this object'
        ) from exc
    _original_api(user, 'GET', f'{RESOURCES[resource]}{object_id}/', {})
    return label, object_id


def promote_chat_attachment(binding, user, data, created_files):
    """Use native multipart API, preserving the private chat source and original actor."""
    label, object_id = promotion_target(user, data)
    try:
        identifier = uuid.UUID(str(data.get('chat_attachment_id')))
        source = AssistantChatAttachment.objects.get(pk=identifier, binding=binding)
    except (ValueError, AssistantChatAttachment.DoesNotExist) as exc:
        raise ValidationError(
            'Chat attachment is unavailable for this partner'
        ) from exc
    comment = data.get('comment', '')
    if not isinstance(comment, str) or len(comment) > 500:
        raise ValidationError('Attachment comment must contain at most 500 characters')
    with source.file.open('rb') as original:
        contents = original.read(FILE_LIMIT + 1)
    if (
        len(contents) != source.size
        or hashlib.sha256(contents).hexdigest() != source.sha256
    ):
        raise ValidationError('Chat attachment failed integrity verification')
    match = resolve('/api/attachment/')
    request = APIRequestFactory().post(
        '/api/attachment/',
        {
            'model_type': label,
            'model_id': object_id,
            'comment': comment,
            'attachment': SimpleUploadedFile(
                source.name, contents, content_type=source.mime_type
            ),
        },
        format='multipart',
    )
    force_authenticate(request, user=user)
    response = match.func(request, *match.args, **match.kwargs)
    if response.status_code in {401, 403}:
        raise PermissionDenied(
            'Original attachment API rejected current business permission'
        )
    if response.status_code >= 400:
        raise ValidationError(
            json.dumps(
                {'http_status': response.status_code, 'details': response.data},
                cls=DjangoJSONEncoder,
            )
        )
    from common.models import Attachment

    native = Attachment.objects.get(pk=response.data['pk'])
    if native.attachment:
        created_files.append((native.attachment.storage, native.attachment.name))
    if native.thumbnail:
        created_files.append((native.thumbnail.storage, native.thumbnail.name))
    AssistantChatAttachment.objects.filter(
        pk=source.pk, submitted_at__isnull=True
    ).update(submitted_at=timezone.now())
    return {
        'pk': native.pk,
        'attachment_id': native.pk,
        'chat_attachment_id': str(source.pk),
        'model_type': label,
        'model_id': object_id,
        'filename': source.name,
        'sha256': source.sha256,
        'upload_user': user.pk,
        'note': 'Copied to the native business attachment record. Formal receipt evidence association requires link_receipt_archive; this does not sign, inspect or approve.',
    }
