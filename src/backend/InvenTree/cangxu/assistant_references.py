"""Resolve explicit chat references through their original current-user APIs."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from .assistant_business_tools import RESOURCES, _original_api

REFERENCE_TYPES = {
    'part': ('parts', '/part/{id}/', '物料'),
    'stock': ('stock', '/stock/item/{id}/', '库存实物'),
    'location': ('locations', '/stock/location/{id}/', '库位'),
    'purchase_order': ('purchase_orders', '/purchasing/purchase-order/{id}/', '采购单'),
    'build': ('builds', '/manufacturing/build-order/{id}/', '工单'),
    'sales_order': ('sales_orders', '/sales/sales-order/{id}/', '销售单'),
    'shipment': ('shipments', '/sales/shipment/{id}/', '发运单'),
    'configuration': ('configurations', '/cangxu/', '实装配置'),
    'purchase_receipt': ('purchase_receipts', '/cangxu/', '收货记录'),
}


def validate_references(user, references):
    """Pin IDs and trusted labels; a page visit never grants execution authority.

    Normalized entries can be passed again by the trusted queue worker, which
    rechecks the original API before dispatch. Client serializers only accept
    object_type/object_id, never caller-provided labels or navigation URLs.
    """
    if not isinstance(references, list) or len(references) > 8:
        raise ValidationError('Provide at most eight business references')
    user = get_user_model().objects.get(pk=user.pk)
    if not user.is_active:
        raise PermissionDenied('Current application user is disabled')
    result = []
    seen = set()
    for reference in references:
        if not isinstance(reference, dict):
            raise ValidationError('Invalid business reference')
        object_type = reference.get('object_type')
        object_id = str(reference.get('object_id', ''))
        if (
            object_type not in REFERENCE_TYPES
            or not object_id.isascii()
            or not object_id.isdigit()
            or not 1 <= len(object_id) <= 12
            or int(object_id) < 1
        ):
            raise ValidationError('Unknown business reference type or ID')
        object_id = str(int(object_id))
        identity = (object_type, object_id)
        if identity in seen:
            raise ValidationError('Duplicate business reference')
        seen.add(identity)
        resource, page, title = REFERENCE_TYPES[object_type]
        record = _original_api(user, 'GET', f'{RESOURCES[resource]}{object_id}/', {})
        label = next(
            (
                record[key]
                for key in ('reference', 'IPN', 'name', 'serial')
                if isinstance(record.get(key), str) and record[key].strip()
            ),
            object_id,
        )
        result.append({
            'object_type': object_type,
            'object_id': object_id,
            'label': f'{title} · {label[:120]}',
            'page_url': page.format(id=object_id),
        })
    return result
