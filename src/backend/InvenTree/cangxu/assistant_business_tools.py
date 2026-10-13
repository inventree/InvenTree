"""Model tools reuse existing authenticated APIs, serializers and business transactions.

The service credential selects a server-owned partner binding. Every original API
is invoked as that binding's current user; no model-supplied user, URL or grant is
accepted. A command receipt deduplicates effects and is not an authorization layer.
"""

import json
import uuid
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.urls import resolve
from django.utils import timezone

from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.test import APIRequestFactory, force_authenticate

from . import serializers as domain
from .assistant_business_models import AssistantRunStop
from .assistant_models import AssistantCommand, AssistantOutboxEvent, PartnerBinding
from .assistant_services import (
    CommandConflictError,
    _check_role,
    canonical_request_hash,
)
from .assistant_tools import LINK_ARCHIVE

# Every route below exists in the current application's URL configuration.
RESOURCES = {
    'parts': '/api/part/',
    'stock': '/api/stock/',
    'locations': '/api/stock/location/',
    'purchase_orders': '/api/order/po/',
    'purchase_lines': '/api/order/po-line/',
    'purchase_receipts': '/api/cangxu/purchase-receipts/',
    'receipt_inspections': '/api/cangxu/receipt-inspections/',
    'receipt_dispositions': '/api/cangxu/receipt-dispositions/',
    'builds': '/api/build/',
    'build_lines': '/api/build/line/',
    'bom': '/api/bom/',
    'configurations': '/api/cangxu/configurations/',
    'configuration_items': '/api/cangxu/configuration-items/',
    'quality_issues': '/api/cangxu/quality-issues/',
    'rework_tasks': '/api/cangxu/rework-tasks/',
    'service_cases': '/api/cangxu/service-cases/',
    'service_lines': '/api/cangxu/service-lines/',
    'service_events': '/api/cangxu/service-events/',
    'sales_orders': '/api/order/so/',
    'shipments': '/api/order/so/shipment/',
    'shipment_receipts': '/api/cangxu/shipment-receipts/',
    'count_sessions': '/api/cangxu/count-sessions/',
    'count_lines': '/api/cangxu/count-lines/',
    'attachments': '/api/attachment/',
}
# Reject unsupported filters instead of silently performing a broader query.
FILTERS = {
    'parts': {'IPN', 'name', 'category', 'active', 'assembly', 'trackable', 'virtual'},
    'stock': {
        'part',
        'serial',
        'location',
        'status',
        'batch',
        'in_stock',
        'belongs_to',
        'supplier_part',
    },
    'locations': {'parent', 'name', 'structural', 'external'},
    'purchase_orders': {'supplier', 'status', 'reference'},
    'purchase_lines': {'order', 'part'},
    'purchase_receipts': {'purchase_order_line', 'location', 'received_by'},
    'receipt_inspections': {'receipt', 'state', 'model_result', 'quantity_result'},
    'receipt_dispositions': {'inspection', 'state', 'outcome'},
    'builds': {'part', 'status', 'reference'},
    'build_lines': {'build', 'bom_item'},
    'bom': {'part', 'sub_part'},
    'configurations': {'unit', 'state', 'revision'},
    'configuration_items': {'configuration', 'component', 'position'},
    'quality_issues': {'unit', 'component', 'state', 'severity'},
    'rework_tasks': {'issue', 'state', 'assigned_to'},
    'service_cases': {'kind', 'state', 'company', 'reference'},
    'service_lines': {'case', 'stock_item', 'outcome'},
    'service_events': {'line', 'event_type', 'stock_item'},
    'sales_orders': {'customer', 'status', 'reference'},
    'shipments': {'order', 'shipment_date'},
    'shipment_receipts': {'manifest', 'is_final'},
    'count_sessions': {'location', 'state', 'reference'},
    'count_lines': {'session', 'stock_item', 'part', 'reviewed'},
    'attachments': {'model_type', 'model_id'},
}


@dataclass(frozen=True)
class BusinessAction:
    """A finite business operation, never an arbitrary model-field update."""

    path: str
    serializer: type | None
    fields: frozenset
    needs_id: bool = False
    native_key: bool = False


def _action(path, serializer, fields, *, needs_id=False, native_key=False):
    """Keep the advertised fields and original API route in one definition."""
    return BusinessAction(
        path, serializer, frozenset(fields.split()), needs_id, native_key
    )


ACTIONS = {
    'receive_purchase': _action(
        '/api/cangxu/purchase-receipts/',
        domain.PurchaseReceiptRequestSerializer,
        'purchase_order_line quantity location status batch_code expiry_date serial_numbers packaging barcode note',
        native_key=True,
    ),
    'issue_material': _action(
        '/api/cangxu/material-issues/',
        domain.MaterialIssueRequestSerializer,
        'build_line stock_item quantity notes',
        native_key=True,
    ),
    'return_material': _action(
        '/api/cangxu/material-issues/{id}/return_stock/',
        domain.MaterialReturnRequestSerializer,
        'quantity location notes',
        needs_id=True,
        native_key=True,
    ),
    'install_component': _action(
        '/api/cangxu/configuration-items/',
        domain.ConfigurationItemSerializer,
        'configuration component position quantity source_build_line rework_task',
    ),
    'remove_component': _action(
        '/api/cangxu/configuration-items/{id}/remove/',
        domain.ComponentRemovalRequestSerializer,
        'location reason removal_kind',
        needs_id=True,
    ),
    'replace_component': _action(
        '/api/cangxu/configuration-items/{id}/replace/',
        domain.ComponentReplacementRequestSerializer,
        'replacement_item destination_location reason rework_task',
        needs_id=True,
    ),
    'record_quality_issue': _action(
        '/api/cangxu/quality-issues/',
        domain.QualityIssueSerializer,
        'reference unit component title description severity containment root_cause corrective_action',
    ),
    'create_rework_task': _action(
        '/api/cangxu/rework-tasks/',
        domain.ReworkTaskSerializer,
        'issue title instructions assigned_to',
    ),
    'record_repair_movement': _action(
        '/api/cangxu/service-events/',
        domain.ServiceCaseEventSerializer,
        'line stock_item event_type company from_location to_location quantity tracking_reference occurred_at notes',
        native_key=True,
    ),
    'register_shipment_receipt': _action(
        '/api/cangxu/shipment-receipts/',
        domain.ShipmentReceiptRequestSerializer,
        'manifest recipient_name is_final notes lines',
        native_key=True,
    ),
    'prepare_count': _action(
        '/api/cangxu/count-sessions/',
        domain.CountSessionSerializer,
        'reference location',
    ),
    'link_receipt_archive': _action('', None, 'receipt_id attachment_id kind'),
    'attach_chat_file': _action(
        '/api/attachment/', None, 'chat_attachment_id object_type object_id comment'
    ),
}


def _original_api(user, method, path, data):
    """Run the owning DRF view and its current permission/serializer policy."""
    match = resolve(path)
    request = getattr(APIRequestFactory(), method.lower())(path, data, format='json')
    force_authenticate(request, user=user)
    response = match.func(request, *match.args, **match.kwargs)
    if response.status_code in {401, 403}:
        raise PermissionDenied(
            'The original business API rejected current user permissions'
        )
    if response.status_code >= 400:
        raise ValidationError(
            json.dumps(
                {'http_status': response.status_code, 'details': response.data},
                cls=DjangoJSONEncoder,
            )
        )
    return json.loads(json.dumps(response.data, cls=DjangoJSONEncoder))


def _user(binding):
    """Read the actual application user afresh; model input cannot select one."""
    user = get_user_model().objects.get(pk=binding.user_id)
    if not binding.enabled or not user.is_active:
        raise PermissionDenied('This assistant or application user is disabled')
    return user


def _valid_filters(resource):
    """Do not advertise a field that the original API would silently ignore."""
    view = resolve(RESOURCES[resource]).func.cls
    filterset = getattr(view, 'filterset_class', None)
    actual = set(getattr(filterset, 'base_filters', {}))
    actual.update(getattr(view, 'filterset_fields', []) or [])
    return FILTERS[resource] & actual


def business_query(binding, arguments):
    """Query existing APIs with bounded pages and exact SN filters when supplied."""
    if set(arguments) - {'resource', 'id', 'search', 'filters', 'offset', 'limit'}:
        raise ValidationError('Unsupported business query fields')
    resource = arguments.get('resource')
    if resource not in RESOURCES:
        raise ValidationError('Unknown business resource')
    filters = arguments.get('filters', {})
    if (
        not isinstance(filters, dict)
        or len(filters) > 12
        or set(filters) - _valid_filters(resource)
    ):
        raise ValidationError(
            'Unsupported filters; inspect business_capabilities for valid fields'
        )
    if any(
        not isinstance(v, (str, int, bool)) or len(str(v)) > 200
        for v in filters.values()
    ):
        raise ValidationError('Filters must be bounded primitive values')
    limit, offset = arguments.get('limit', 20), arguments.get('offset', 0)
    if (
        type(limit) is not int
        or not 1 <= limit <= 100
        or type(offset) is not int
        or not 0 <= offset <= 100000
    ):
        raise ValidationError('Invalid query page')
    data = {**filters, 'limit': limit, 'offset': offset}
    if 'search' in arguments:
        if (
            not isinstance(arguments['search'], str)
            or not 1 <= len(arguments['search']) <= 200
        ):
            raise ValidationError('Search must contain 1 to 200 characters')
        data['search'] = arguments['search']
    object_id = arguments.get('id')
    path = RESOURCES[resource]
    if object_id is not None:
        if type(object_id) is not int or object_id < 1:
            raise ValidationError('Object ID must be a positive integer')
        path += f'{object_id}/'
    result = _original_api(_user(binding), 'GET', path, data)
    # Native serializers include rich nested details. Fit a whole-record page
    # inside the model bridge's 32 KiB envelope without losing the total count.
    page_limited = False
    if isinstance(result, dict) and isinstance(result.get('results'), list):
        rows = result['results']
        while rows and len(json.dumps(result, ensure_ascii=False).encode()) > 24000:
            rows.pop()
            page_limited = True
        if page_limited:
            if not rows:
                raise ValidationError(
                    'A single result exceeds the model query limit; use the business page'
                )
            next_url = result.get('next') or path
            parsed = urlsplit(next_url)
            query = dict(parse_qsl(parsed.query))
            query.update({**data, 'offset': offset + len(rows)})
            result['next'] = urlunsplit(parsed._replace(query=urlencode(query)))
    if len(json.dumps(result, ensure_ascii=False).encode()) > 24000:
        raise ValidationError(
            'Query result exceeds the model query limit; use narrower filters or the business page'
        )
    return {
        'status': 'ok',
        'resource': resource,
        'data': result,
        'queried_at': timezone.now().isoformat(),
        'record_url': path,
        'page_limited': page_limited,
        'next_offset': offset + len(result['results']) if page_limited else None,
    }


def business_capabilities(binding):
    """Expose the actual bounded tool contract and original serializer field hints."""
    _user(binding)
    operations = []
    for name, action in ACTIONS.items():
        fields = {}
        if action.serializer:
            for key, field in action.serializer().fields.items():
                if key in action.fields:
                    fields[key] = {
                        'type': type(field).__name__,
                        'required': field.required,
                        'allow_null': field.allow_null,
                    }
                    if hasattr(field, 'choices'):
                        fields[key]['choices'] = list(field.choices)
        elif name == 'attach_chat_file':
            from .assistant_attachment_business import TARGETS

            fields = {
                'chat_attachment_id': {'type': 'UUIDField', 'required': True},
                'object_type': {'choices': list(TARGETS), 'required': True},
                'object_id': {'type': 'IntegerField', 'required': True},
                'comment': {'type': 'CharField', 'required': False, 'max_length': 500},
            }
        else:
            fields = {
                'receipt_id': {'type': 'IntegerField', 'required': True},
                'attachment_id': {'type': 'IntegerField', 'required': True},
                'kind': {'choices': ['photo', 'report'], 'required': True},
            }
        try:
            _check_action_permission(_user(binding), action, name)
            allowed = True
        except PermissionDenied:
            allowed = False
        operations.append({
            'operation': name,
            'id_required': action.needs_id,
            'fields': fields,
            'allowed_by_current_role': allowed,
        })
    return {
        'status': 'ok',
        'queries': [
            {'resource': name, 'filters': sorted(_valid_filters(name))}
            for name in RESOURCES
        ],
        'operations': operations,
        'human_actions': 'Inspection, personal signatures, approvals, actual count and final release remain in the existing human workflow.',
    }


def business_action(binding, payload):
    """Roll back native file copies if the enclosing database command fails."""
    created_files = []
    try:
        return _business_action(binding, payload, created_files)
    except Exception:
        for storage, name in created_files:
            storage.delete(name)
        raise


@transaction.atomic
def _business_action(binding, payload, created_files):
    """Commit the original business action and replay receipt in one transaction."""
    binding = PartnerBinding.objects.select_for_update().get(pk=binding.pk)
    user = _user(binding)
    arguments = payload['arguments']
    if set(arguments) - {'operation', 'id', 'data'}:
        raise ValidationError('Unsupported business action fields')
    operation = arguments.get('operation')
    if operation not in ACTIONS:
        raise ValidationError('Unknown business operation')
    action = ACTIONS[operation]
    data = arguments.get('data', {})
    if not isinstance(data, dict) or set(data) - action.fields:
        raise ValidationError('Unsupported business action data fields')
    object_id = arguments.get('id')
    if action.needs_id and (type(object_id) is not int or object_id < 1):
        raise ValidationError('This business action requires an explicit object ID')
    if not action.needs_id and object_id is not None:
        raise ValidationError('This business action does not accept an object ID')
    if operation == 'record_repair_movement' and data.get('event_type') not in {
        'received',
        'sent',
        'external_received',
        'returned',
        'note',
    }:
        raise ValidationError(
            'Inspection, disposal and reinstall decisions remain in their existing workflows'
        )
    key = payload['command_id']
    digest = canonical_request_hash({'tool': 'business_action', 'arguments': arguments})
    existing = AssistantCommand.objects.filter(binding=binding, key=key).first()
    if existing:
        if existing.request_hash != digest:
            raise CommandConflictError(
                'Command key already identifies a different business action'
            )
        if existing.status != AssistantCommand.Status.SUCCEEDED:
            raise CommandConflictError('Reconcile this command before retrying')
        # Recheck the original API's write permission on replay, without executing it.
        _check_action_permission(user, action, operation, data)
        return {
            **existing.result_reference,
            'command_receipt_id': existing.pk,
            'replayed': True,
        }
    if (
        not binding.write_enabled
        or AssistantRunStop.objects.filter(
            binding=binding, run_id=payload['run_id']
        ).exists()
    ):
        raise PermissionDenied('Autonomous writes have been stopped')
    if operation == 'attach_chat_file':
        from .assistant_attachment_business import promote_chat_attachment

        result = promote_chat_attachment(binding, user, data, created_files)
    elif operation == 'link_receipt_archive':
        if set(data) != {'receipt_id', 'attachment_id', 'kind'} or any(
            type(data.get(field)) is not int or data[field] < 1
            for field in ('receipt_id', 'attachment_id')
        ):
            raise ValidationError(
                'Provide positive receipt_id, attachment_id and evidence kind'
            )
        if not _check_role(user, LINK_ARCHIVE):
            raise PermissionDenied(
                'Current purchase-order rights do not allow this association'
            )
        result, _ = LINK_ARCHIVE.execute(
            user,
            str(data['receipt_id']),
            {'attachment_id': data['attachment_id'], 'kind': data['kind']},
        )
    else:
        if action.native_key:
            data = {
                **data,
                'idempotency_key': str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f'{binding.partner_id}:{key}')
                ),
            }
        result = _original_api(user, 'POST', action.path.format(id=object_id), data)
    receipt = AssistantCommand.objects.create(
        binding=binding,
        grant=None,
        grant_version=1,
        key=key,
        request_hash=digest,
        object_type=operation,
        object_id=str(
            object_id
            or (
                result.get('pk')
                or result.get('id')
                or result.get('receipt_id')
                or 'created'
            )
        ),
        action=operation,
        run_id=payload['run_id'],
        step_id=payload['step_id'],
        status=AssistantCommand.Status.SUCCEEDED,
        result_reference={
            'status': 'succeeded',
            'operation': operation,
            'data': result,
        },
        completed_at=timezone.now(),
    )
    AssistantOutboxEvent.objects.create(
        object_type=operation,
        object_id=receipt.object_id,
        object_version=1,
        event_type='assistant.business_action',
        command=receipt,
        correlation_id=payload['run_id'],
        causation_id=key,
    )
    return {
        **receipt.result_reference,
        'command_receipt_id': receipt.pk,
        'replayed': False,
    }


def _check_action_permission(user, action, operation, data=None):
    """Reuse the original API permission classes when returning an old write receipt."""
    if operation == 'attach_chat_file':
        from .assistant_attachment_business import TARGETS, promotion_target

        if data is not None:
            promotion_target(user, data)
        else:
            from common.serializers import check_model_change_permission
            from common.validators import attachment_model_class_from_label
            from InvenTree.models import InvenTreeAttachmentMixin

            for label, _ in TARGETS.values():
                try:
                    check_model_change_permission(
                        user,
                        attachment_model_class_from_label(label),
                        InvenTreeAttachmentMixin,
                        'Unsupported attachment target',
                        'Attachment permission denied',
                    )
                    return
                except (DRFPermissionDenied, ValidationError):
                    continue
            raise PermissionDenied(
                'Current role cannot attach files to the supported business objects'
            )
        return
    if operation == 'link_receipt_archive':
        if not _check_role(user, LINK_ARCHIVE):
            raise PermissionDenied(
                'Current purchase-order rights do not allow this association'
            )
        return
    match = resolve(action.path.format(id=1))
    view = match.func.cls(**getattr(match.func, 'initkwargs', {}))
    request = APIRequestFactory().post(action.path, {}, format='json')
    force_authenticate(request, user=user)
    view.args = match.args
    view.kwargs = match.kwargs
    # ViewSet action must exist before initialize_request resolves its policy.
    if hasattr(match.func, 'actions'):
        view.action_map = match.func.actions
    view.request = view.initialize_request(request)
    try:
        view.check_permissions(view.request)
    except DRFPermissionDenied as exc:
        raise PermissionDenied(
            'The original business API rejected current permissions'
        ) from exc
