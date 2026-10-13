"""Authenticated conversation endpoints for the resident work partner.

The gateway never trusts client claims about identity or partners: every
request resolves the caller's own binding. Submissions are durably accepted
first; a background worker performs the runtime transport so no request
transaction blocks on the network.
"""

import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from InvenTree.tasks import offload_task
from users.authentication import ApiTokenAuthentication

from .assistant_business_models import AssistantRunStop
from .assistant_delivery_models import AssistantGatewayDelivery
from .assistant_gateway import (
    AssistantRuntimeNotConfiguredError,
    DeliveryConflictError,
    RuntimeProtocolError,
    RuntimeRejectedError,
    RuntimeUnavailableError,
    ensure_partner_binding,
    get_runtime_transport,
    queue_control_delivery,
    queue_message_delivery,
    runtime_config,
)
from .assistant_models import AssistantDuty, PartnerBinding
from .assistant_tasks import DELIVER_ONE_FUNC, LAST_DISPATCH_SETTING, TASK_GROUP

MESSAGE_TEXT_MAX_LENGTH = 16000
REFERENCE_LIMIT = 8
HISTORY_LIMIT_DEFAULT = 50
HISTORY_LIMIT_MAX = 100
CONTROL_SCOPES = ('reply', 'task', 'all-writes', 'all-background')


class AssistantServiceUnavailable(APIException):
    """The runtime endpoint is missing, misconfigured or unreachable."""

    status_code = 503
    default_detail = 'The assistant runtime is unavailable.'
    default_code = 'assistant_runtime_unavailable'


class AssistantUpstreamError(APIException):
    """The runtime answered with a structured rejection or invalid payload."""

    status_code = 502
    default_detail = 'The assistant runtime rejected the request.'
    default_code = 'assistant_runtime_error'


class AssistantRequestConflict(APIException):
    """A stable client request key was reused with different content."""

    status_code = 409
    default_detail = 'The request key already identifies different content.'
    default_code = 'assistant_request_conflict'


class StrictSerializer(serializers.Serializer):
    """Reject unknown fields; clients cannot smuggle identity or scope claims."""

    def to_internal_value(self, data):
        """Refuse anything outside the declared contract before validation."""
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({
                    'unknown_fields': f'Unexpected fields: {sorted(unknown)}'
                })
        return super().to_internal_value(data)


def _no_wildcard(value):
    """Keep references and request keys explicit and stable."""
    if '*' in value or not value.strip():
        raise serializers.ValidationError(
            'Provide an explicit value without wildcards.'
        )
    return value


class ReferenceSerializer(serializers.Serializer):
    """One explicit business object reference attached to a message."""

    object_type = serializers.CharField(max_length=100, validators=[_no_wildcard])
    object_id = serializers.CharField(max_length=100, validators=[_no_wildcard])


class MessageRequestSerializer(StrictSerializer):
    """Persist one explicit user command under a stable idempotency key."""

    client_request_id = serializers.CharField(
        max_length=200, trim_whitespace=True, validators=[_no_wildcard]
    )
    text = serializers.CharField(
        max_length=MESSAGE_TEXT_MAX_LENGTH,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default='',
    )
    references = serializers.ListField(
        child=ReferenceSerializer(),
        required=False,
        allow_empty=True,
        max_length=REFERENCE_LIMIT,
        default=list,
    )

    retry = serializers.BooleanField(default=False, required=False)

    attachments = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list, max_length=8
    )

    def validate(self, attrs):
        """Accept text or files and verify current business-reference permissions."""
        if not attrs.get('text', '').strip() and not attrs.get('attachments'):
            raise serializers.ValidationError('Provide text or attachments')
        from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
        from django.core.exceptions import ValidationError as DjangoValidationError

        from .assistant_references import validate_references

        try:
            attrs['references'] = validate_references(
                self.context['request'].user, attrs.get('references') or []
            )
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(
                'Business reference is unavailable for the current role'
            ) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return attrs


class ControlRequestSerializer(StrictSerializer):
    """Persist one explicitly scoped stop or pause control."""

    client_request_id = serializers.CharField(
        max_length=200, trim_whitespace=True, validators=[_no_wildcard]
    )
    scope = serializers.ChoiceField(choices=CONTROL_SCOPES)
    task_id = serializers.IntegerField(min_value=1, required=False)

    def validate(self, attrs):
        """A task-scoped stop must name its task; other scopes must not."""
        if attrs['scope'] == 'task' and 'task_id' not in attrs:
            raise serializers.ValidationError({
                'task_id': 'Stopping one task requires its identifier.'
            })
        if attrs['scope'] != 'task' and 'task_id' in attrs:
            raise serializers.ValidationError({
                'task_id': 'Only task-scoped controls accept a task identifier.'
            })
        return attrs


class HistoryRequestSerializer(StrictSerializer):
    """Bound one history read to a small page."""

    before = serializers.IntegerField(min_value=1, required=False)
    limit = serializers.IntegerField(
        min_value=1, max_value=HISTORY_LIMIT_MAX, default=HISTORY_LIMIT_DEFAULT
    )


def _runtime_or_503():
    """Require a configured deployment identity before touching bindings."""
    config = runtime_config()
    if config is None:
        raise AssistantServiceUnavailable()
    return config


def _selected_partner_id(request):
    """Parse the optional ?partner_id selector; malformed values are rejected."""
    raw = request.query_params.get('partner_id')
    if raw is None:
        return None
    try:
        return uuid.UUID(raw)
    except (ValueError, AttributeError, TypeError) as exc:
        raise serializers.ValidationError({
            'partner_id': 'Provide a valid partner UUID.'
        }) from exc


def _current_binding(user, partner_id=None):
    """Return the caller's binding for the configured deployment only.

    Without a selector only the unique default binding qualifies. An explicit
    partner identifier selects the caller's own binding in this deployment;
    unknown or foreign identifiers are rejected, never provisioned.
    """
    config = _runtime_or_503()
    bindings = PartnerBinding.objects.filter(
        deployment_id=config.deployment_id, user=user
    )
    if partner_id is None:
        return bindings.filter(is_default=True).first()
    try:
        return bindings.get(partner_id=partner_id)
    except PartnerBinding.DoesNotExist as exc:
        raise NotFound('This partner is unavailable for the current account.') from exc


def _selected_binding(request):
    """Resolve an optional selector for read endpoints without provisioning."""
    return _current_binding(request.user, _selected_partner_id(request))


def _ensure_selected_binding(request):
    """Provision the default partner or select an existing owned one."""
    try:
        return ensure_partner_binding(request.user, _selected_partner_id(request))
    except PartnerBinding.DoesNotExist as exc:
        raise NotFound('This partner is unavailable for the current account.') from exc


def _offload_delivery(delivery_id):
    """Hand one fresh delivery to the worker after the write commits."""
    offload_task(DELIVER_ONE_FUNC, delivery_id, group=TASK_GROUP, force_async=True)


class AssistantBindingViewSet(viewsets.ViewSet):
    """Report the caller's partner binding and real service availability."""

    # Browser sessions and existing native tokens retain normal user rights.
    # OAuth delegation is not exposed until its scopes survive background execution.
    authentication_classes = [
        ApiTokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=dict)
    def list(self, request):
        """Return one honest snapshot; availability is worker-heartbeat based."""
        data = {
            'bound': False,
            'partner_id': None,
            'conversation_id': None,
            'enabled': False,
            'write_enabled': False,
            'runtime_configured': False,
            'last_dispatch_at': None,
        }
        config = runtime_config()
        data['runtime_configured'] = config is not None
        if config is not None:
            binding = _current_binding(request.user, _selected_partner_id(request))
            if binding is not None:
                data.update(
                    bound=True,
                    partner_id=binding.partner_id,
                    conversation_id=binding.conversation_id,
                    enabled=binding.enabled,
                    write_enabled=binding.write_enabled,
                )
        try:
            from common.settings import get_global_setting

            last_dispatch = get_global_setting(LAST_DISPATCH_SETTING, '', cache=False)
        except Exception:  # pragma: no cover - status stays honest without it
            last_dispatch = ''
        data['last_dispatch_at'] = last_dispatch or None
        return Response(data)


class AssistantMessageViewSet(viewsets.ViewSet):
    """Durably accept explicit commands and read bounded transcript history."""

    # Browser sessions and existing native tokens retain normal user rights.
    # OAuth delegation is not exposed until its scopes survive background execution.
    authentication_classes = [
        ApiTokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    @extend_schema(request=MessageRequestSerializer, responses={201: dict, 200: dict})
    def create(self, request):
        """Persist first, transport later; identical retries return one record."""
        serializer = MessageRequestSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _runtime_or_503()
        try:
            binding = _ensure_selected_binding(request)
        except AssistantRuntimeNotConfiguredError as exc:
            raise AssistantServiceUnavailable() from exc
        if not binding.enabled or not request.user.is_active:
            raise PermissionDenied('This partner is disabled.')
        from django.core.exceptions import ValidationError as DjangoValidationError

        from .assistant_attachments import message_attachments

        try:
            attachments = message_attachments(binding, data['attachments'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        with transaction.atomic():
            PartnerBinding.objects.select_for_update().get(pk=binding.pk)
            try:
                attachments = message_attachments(binding, data['attachments'])
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages) from exc
            try:
                delivery, created = queue_message_delivery(
                    binding=binding,
                    client_request_id=data['client_request_id'],
                    text=data['text'],
                    references=data['references'],
                    attachments=attachments,
                )
            except DeliveryConflictError as exc:
                raise AssistantRequestConflict() from exc
            from django.utils import timezone

            from .assistant_attachment_models import AssistantChatAttachment

            AssistantChatAttachment.objects.filter(
                binding=binding, pk__in=data['attachments'], submitted_at__isnull=True
            ).update(submitted_at=timezone.now())
            if (
                data['retry']
                and delivery.status == AssistantGatewayDelivery.Status.FAILED
            ):
                delivery.status = AssistantGatewayDelivery.Status.PENDING
                delivery.attempts = 0
                delivery.last_error = ''
                delivery.available_at = timezone.now()
                delivery.save(
                    update_fields=[
                        'status',
                        'attempts',
                        'last_error',
                        'available_at',
                        'updated_at',
                    ]
                )
            if delivery.status == AssistantGatewayDelivery.Status.PENDING:
                transaction.on_commit(lambda: _offload_delivery(delivery.pk))
        return Response(
            _delivery_receipt(delivery, data['client_request_id']),
            status=201 if created else 200,
        )

    @extend_schema(parameters=[HistoryRequestSerializer], responses=dict)
    def list(self, request):
        """Proxy one bounded history page for the caller's own partner."""
        query = {
            key: value
            for key, value in request.query_params.items()
            if key != 'partner_id'
        }
        serializer = HistoryRequestSerializer(data=query)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        binding = _selected_binding(request)
        if binding is None:
            return Response({'items': [], 'next_before': None, 'has_more': False})
        if not binding.enabled or not request.user.is_active:
            raise PermissionDenied('This partner is disabled')
        try:
            transport = get_runtime_transport()
            page = transport.list_messages(
                binding.partner_id, before=data.get('before'), limit=data['limit']
            )
        except (RuntimeUnavailableError, RuntimeRejectedError, RuntimeProtocolError):
            return Response({
                'items': [],
                'next_before': None,
                'has_more': False,
                'runtime_unavailable': True,
                'pending': _pending_messages(binding),
            })
        from .assistant_attachments import message_attachments

        for item in page['items']:
            identifiers = [
                entry.get('id')
                for entry in item.get('attachments', [])
                if isinstance(entry, dict)
            ]
            try:
                trusted = message_attachments(binding, identifiers)
                extraction = {
                    entry.get('id'): entry
                    for entry in item.get('attachments', [])
                    if isinstance(entry, dict)
                }
                for attachment in trusted:
                    metadata = extraction.get(attachment['id'], {})
                    if metadata.get('extraction_status') in {
                        'parsed',
                        'unsupported',
                        'failed',
                        'truncated',
                    }:
                        attachment['extraction_status'] = metadata['extraction_status']
                    if isinstance(metadata.get('extraction_note'), str):
                        attachment['extraction_note'] = metadata['extraction_note'][
                            :1000
                        ]
                item['attachments'] = trusted
            except Exception:
                item['attachments'] = []
        return Response({**page, 'pending': _pending_messages(binding)})


class AssistantControlViewSet(viewsets.ViewSet):
    """Persist explicitly scoped control commands before forwarding them."""

    # Browser sessions and existing native tokens retain normal user rights.
    # OAuth delegation is not exposed until its scopes survive background execution.
    authentication_classes = [
        ApiTokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ControlRequestSerializer, responses={201: dict, 200: dict})
    def create(self, request):
        """Freeze write authority immediately when all writes are stopped."""
        serializer = ControlRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _runtime_or_503()
        try:
            binding = _ensure_selected_binding(request)
        except AssistantRuntimeNotConfiguredError as exc:
            raise AssistantServiceUnavailable() from exc
        with transaction.atomic():
            PartnerBinding.objects.select_for_update().get(pk=binding.pk)
            if data['scope'] == 'task':
                AssistantRunStop.objects.get_or_create(
                    binding=binding, run_id=str(data['task_id'])
                )
            if data['scope'] == 'all-background':
                AssistantDuty.objects.filter(binding=binding).update(paused=True)
            if data['scope'] in {'all-writes', 'all-background'}:
                # Stop new autonomous writes before anything is forwarded.
                PartnerBinding.objects.filter(pk=binding.pk).update(write_enabled=False)
            try:
                delivery, created = queue_control_delivery(
                    binding=binding,
                    client_request_id=data['client_request_id'],
                    scope=data['scope'],
                    task_id=data.get('task_id'),
                )
            except DeliveryConflictError as exc:
                raise AssistantRequestConflict() from exc
            if delivery.status == AssistantGatewayDelivery.Status.PENDING:
                transaction.on_commit(lambda: _offload_delivery(delivery.pk))
        binding.refresh_from_db()
        return Response(
            {
                **_delivery_receipt(delivery, data['client_request_id']),
                'write_enabled': binding.write_enabled,
            },
            status=201 if created else 200,
        )


def _delivery_receipt(delivery, client_request_id):
    """Describe durable state only; accepted text lives with the runtime."""
    return {
        'client_request_id': client_request_id,
        'status': delivery.status,
        'acknowledged': delivery.status == AssistantGatewayDelivery.Status.ACKNOWLEDGED,
        'submission_id': delivery.response_id or None,
        'accepted_at': delivery.created_at,
    }


class ReceiptEvidenceRequestSerializer(StrictSerializer):
    """Explicit source-to-receipt association, without guessing photo ownership."""

    id = serializers.IntegerField(min_value=1)
    kind = serializers.ChoiceField(choices=['photo', 'report'])


class ReceiptFollowupRequestSerializer(StrictSerializer):
    """One user task; system records its execution authority automatically."""

    client_request_id = serializers.CharField(max_length=200, validators=[_no_wildcard])
    text = serializers.CharField(max_length=16000, allow_blank=False)
    receipt_id = serializers.IntegerField(min_value=1)
    attachments = ReceiptEvidenceRequestSerializer(
        many=True, required=False, default=list
    )
    interval_seconds = serializers.IntegerField(
        min_value=60, max_value=86400, default=300
    )

    def validate_attachments(self, value):
        """Keep the pinned work bounded and its file identities unambiguous."""
        if len(value) > 20 or len({item['id'] for item in value}) != len(value):
            raise serializers.ValidationError(
                'Provide at most 20 distinct evidence files'
            )
        return value


class AssistantReceiptFollowupViewSet(viewsets.ViewSet):
    """Accept a receipt task and start it, with no separate grant-creation flow."""

    # Browser sessions and existing native tokens retain normal user rights.
    # OAuth delegation is not exposed until its scopes survive background execution.
    authentication_classes = [
        ApiTokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ReceiptFollowupRequestSerializer, responses={201: dict, 200: dict}
    )
    def create(self, request):
        """Persist the user command, its exact scope and first check atomically."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        from common.models import Attachment

        from .assistant_business_models import ReceiptArchiveEvidence
        from .assistant_gateway import _queue_delivery, register_command_duty
        from .assistant_services import _check_role
        from .assistant_tasks import enqueue_due_duties
        from .assistant_tools import LINK_ARCHIVE, READ_RECEIPT
        from .models import PurchaseReceipt

        serializer = ReceiptFollowupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not request.user.is_active or not _check_role(request.user, READ_RECEIPT):
            raise PermissionDenied(
                'Current purchase-order permission does not allow this task'
            )
        if data['attachments'] and not _check_role(request.user, LINK_ARCHIVE):
            raise PermissionDenied(
                'Current purchase-order permission does not allow archive association'
            )
        try:
            receipt = PurchaseReceipt.objects.get(pk=data['receipt_id'])
            for item in data['attachments']:
                source = Attachment.objects.get(pk=item['id'])
                ReceiptArchiveEvidence(
                    receipt=receipt,
                    attachment=source,
                    kind=item['kind'],
                    linked_by=request.user,
                ).clean()
        except (
            PurchaseReceipt.DoesNotExist,
            Attachment.DoesNotExist,
            DjangoValidationError,
        ) as exc:
            raise serializers.ValidationError(
                'Receipt or archive source is unavailable for this task'
            ) from exc
        binding = _ensure_selected_binding(request)
        if not binding.enabled:
            raise PermissionDenied('This partner is disabled')
        with transaction.atomic():
            PartnerBinding.objects.select_for_update().get(pk=binding.pk)
            try:
                delivery, created = _queue_delivery(
                    binding=binding,
                    kind=AssistantGatewayDelivery.Kind.MESSAGE,
                    request_key=data['client_request_id'],
                    intent={'kind': 'receipt_followup', **data},
                    payload={'text': data['text'], 'references': []},
                )
            except DeliveryConflictError as exc:
                raise AssistantRequestConflict() from exc
            if created:
                register_command_duty(
                    binding=binding,
                    object_ids=[receipt.pk],
                    actions=['receipt.read']
                    + (['receipt.link_archive'] if data['attachments'] else []),
                    authorization_reference=f'message:{data["client_request_id"]}',
                    name=f'Receipt {receipt.pk} archive follow-up',
                    goal=data['text'],
                    interval_seconds=data['interval_seconds'],
                    trigger_filter={'attachments': data['attachments']},
                    limits={
                        'attachment_ids': [item['id'] for item in data['attachments']]
                    }
                    if data['attachments']
                    else {},
                )
                enqueue_due_duties()
            if delivery.status == AssistantGatewayDelivery.Status.PENDING:
                transaction.on_commit(lambda: _offload_delivery(delivery.pk))
        return Response(
            _delivery_receipt(delivery, data['client_request_id']),
            status=201 if created else 200,
        )


def _pending_messages(binding):
    """Show durable pending and failed submissions until Pi has acknowledged them."""
    return [
        {
            'request_id': delivery.request_key,
            'text': delivery.payload.get('text', ''),
            'attachments': delivery.payload.get('attachments', []),
            'references': delivery.payload.get('references', []),
            'status': delivery.status,
            'last_error': delivery.last_error or None,
            'accepted_at': delivery.created_at,
        }
        for delivery in AssistantGatewayDelivery.objects
        .filter(binding=binding, kind='message')
        .exclude(status='acknowledged')
        .order_by('-created_at')[:100]
    ]


class AssistantStatusViewSet(AssistantBindingViewSet):
    """Report durable work state and transport status for the current partner."""

    @extend_schema(responses=dict)
    def list(self, request):
        """Do not disguise runtime failure as idle or an accepted response."""
        binding = _selected_binding(request)
        if binding is None:
            return Response({'status': 'unbound', 'is_running': False, 'pending': []})
        if not binding.enabled or not request.user.is_active:
            raise PermissionDenied('This partner is disabled')
        try:
            status = get_runtime_transport().partner_status(binding.partner_id)
        except (
            AssistantRuntimeNotConfiguredError,
            RuntimeUnavailableError,
            RuntimeRejectedError,
            RuntimeProtocolError,
        ):
            status = {'status': 'unavailable', 'is_running': False}
        return Response({**status, 'pending': _pending_messages(binding)})


class PartnerRequestSerializer(StrictSerializer):
    """The only client-writable partner metadata is its display name."""

    display_name = serializers.CharField(max_length=80, trim_whitespace=True)

    def validate_display_name(self, value):
        """Reject blank names so the sidebar never renders an empty partner."""
        if not value.strip():
            raise serializers.ValidationError('Provide a nonempty display name.')
        return value.strip()


def _partner_summary(binding):
    """Serialize sidebar metadata from the caller's own bindings only.

    The preview is derived from this user's durable gateway queue; the payload
    text of acknowledged deliveries is already cleared, so it may be absent.
    """
    last_message = getattr(binding, 'last_message_text', None)
    if not isinstance(last_message, str) or not last_message:
        last_message = None
    return {
        'partner_id': binding.partner_id,
        'conversation_id': binding.conversation_id,
        'display_name': binding.display_name,
        'is_default': binding.is_default,
        'enabled': binding.enabled,
        'write_enabled': binding.write_enabled,
        'created_at': binding.created_at,
        'updated_at': binding.updated_at,
        'last_message': last_message[:200] if last_message else None,
        'last_message_at': getattr(binding, 'last_message_at', None),
    }


class AssistantPartnerViewSet(viewsets.ViewSet):
    """List, create and rename the caller's partners within one deployment.

    There is no delete, disable or reset endpoint: partners accumulate as
    durable conversation identity and are retired by policy, not by clients.
    """

    # Browser sessions and existing native tokens retain normal user rights.
    # OAuth delegation is not exposed until its scopes survive background execution.
    authentication_classes = [
        ApiTokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [IsAuthenticated]
    lookup_value_regex = '[0-9a-f-]{36}'

    def _owned(self, request, pk):
        """Resolve one partner the caller owns in the configured deployment."""
        config = _runtime_or_503()
        try:
            partner_id = uuid.UUID(str(pk))
        except (ValueError, AttributeError, TypeError) as exc:
            raise NotFound(
                'This partner is unavailable for the current account.'
            ) from exc
        return get_object_or_404(
            PartnerBinding,
            deployment_id=config.deployment_id,
            user=request.user,
            partner_id=partner_id,
        )

    @extend_schema(responses=dict)
    def list(self, request):
        """Return the caller's partners, default first then most recent.

        Opening the workbench provisions the default partner through the same
        race-safe path as a first message; this authorized read side effect is
        the one place a GET may create a binding.
        """
        from django.db.models import OuterRef, Subquery

        config = _runtime_or_503()
        try:
            ensure_partner_binding(request.user)
        except AssistantRuntimeNotConfiguredError as exc:
            raise AssistantServiceUnavailable() from exc
        latest = AssistantGatewayDelivery.objects.filter(
            binding=OuterRef('pk'), kind=AssistantGatewayDelivery.Kind.MESSAGE
        ).order_by('-created_at')
        bindings = (
            PartnerBinding.objects
            .filter(deployment_id=config.deployment_id, user=request.user)
            .annotate(
                last_message_text=Subquery(latest.values('payload__text')[:1]),
                last_message_at=Subquery(latest.values('created_at')[:1]),
            )
            .order_by('-is_default', '-updated_at')
        )
        return Response({'results': [_partner_summary(row) for row in bindings]})

    @extend_schema(request=PartnerRequestSerializer, responses={201: dict})
    def create(self, request):
        """Create an enabled non-default partner with server-owned identifiers."""
        config = _runtime_or_503()
        serializer = PartnerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        binding = PartnerBinding.objects.create(
            deployment_id=config.deployment_id,
            user=request.user,
            display_name=serializer.validated_data['display_name'],
            enabled=True,
            write_enabled=True,
        )
        return Response(_partner_summary(binding), status=201)

    @extend_schema(request=PartnerRequestSerializer, responses={200: dict})
    def partial_update(self, request, pk=None):
        """Rename one of the caller's own partners; other fields are read-only."""
        serializer = PartnerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        binding = self._owned(request, pk)
        binding.display_name = serializer.validated_data['display_name']
        binding.save(update_fields=['display_name', 'updated_at'])
        return Response(_partner_summary(binding))
