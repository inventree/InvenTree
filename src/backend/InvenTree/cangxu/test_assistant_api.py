"""Gateway acceptance, durable ordering, schedule fan-out and stop semantics."""

import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from rest_framework.test import APIRequestFactory, force_authenticate

from .assistant_api import (
    AssistantBindingViewSet,
    AssistantControlViewSet,
    AssistantMessageViewSet,
    AssistantReceiptFollowupViewSet,
)
from .assistant_business_models import AssistantRunStop
from .assistant_delivery_models import AssistantDutySlot, AssistantGatewayDelivery
from .assistant_gateway import (
    RuntimeTransport,
    RuntimeUnavailableError,
    ensure_partner_binding,
    queue_message_delivery,
    register_command_duty,
    runtime_config,
    submit_delivery,
)
from .assistant_models import AssistantDuty, AssistantGrant, AssistantOutboxEvent
from .assistant_tasks import (
    PERIODIC_DISPATCH_FUNC,
    attempt_pending_deliveries,
    enqueue_due_duties,
    enqueue_undelivered_events,
    ensure_schedules,
)
from .models import PurchaseReceipt
from .test_assistant_tools import DEPLOYMENT, SERVICE_TOKEN, ReceiptToolFixture


class RecordingTransport:
    """Record acceptance only; actual HTTP and business writes have separate tests."""

    def __init__(self, fail_first=False):
        """Optionally simulate one ambiguous network failure."""
        self.calls = []
        self.fail_first = fail_first

    def submit_message(self, partner, key, text, references):
        """Record the exact partner-scoped message submission."""
        self.calls.append(('message', str(partner), key, text))
        if self.fail_first:
            self.fail_first = False
            raise RuntimeUnavailableError('network_unreachable')
        return {'response_id': '42'}

    def submit_event(self, partner, key, source, due_at, work=None):
        """Keep the pinned task context visible for assertions."""
        self.calls.append(('event', str(partner), key, work))
        return {'response_id': '43'}

    def submit_control(self, partner, key, scope, task_id=None):
        """Record independently scoped control forwarding."""
        self.calls.append(('control', str(partner), key, scope))
        return {'response_id': '44'}

    def list_messages(self, partner, **kwargs):
        """Only the bound owner may reach this method through the gateway."""
        self.calls.append(('history', str(partner)))
        return {'items': [], 'next_before': None, 'has_more': False}


@override_settings(USE_TZ=True)
class AssistantGatewayTests(ReceiptToolFixture, TestCase):
    """No model/provider data or real enterprise records are used."""

    def setUp(self):
        """Configure a fictional service and native receipt fixture."""
        self.env = patch.dict(
            os.environ,
            {
                'ASSISTANT_DEPLOYMENT_ID': DEPLOYMENT,
                'ASSISTANT_RUNTIME_TOKEN': SERVICE_TOKEN,
                'ASSISTANT_RUNTIME_URL': 'http://127.0.0.1:8789',
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        self.build_fixture()
        self.factory = APIRequestFactory()

    def api(self, view, action, data=None, user=None, method='post'):
        """Invoke the real authenticated DRF action under the selected owner."""
        request = getattr(self.factory, method)('/', data or {}, format='json')
        if user is not False:
            force_authenticate(request, user=user or self.user)
        return view.as_view({method: action})(request)

    def duty(self, **overrides):
        """Register task provenance as trusted gateway code would."""
        options = {
            'binding': self.binding,
            'object_ids': [self.receipt.pk],
            'actions': ['receipt.read'],
            'authorization_reference': 'fictional-user-task',
            'name': 'Fictional follow-up',
            'goal': 'Follow the fictional receipt',
            'interval_seconds': 300,
        }
        options.update(overrides)
        return register_command_duty(**options)

    def test_authentication_and_identity_claim_rejection(self):
        """Anonymous requests and user/partner override fields cannot enter the queue."""
        response = self.api(AssistantBindingViewSet, 'list', user=False, method='get')
        self.assertIn(response.status_code, [401, 403])
        response = self.api(
            AssistantMessageViewSet,
            'create',
            {'client_request_id': 'spoof', 'text': 'Fictional query', 'user_id': 99},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AssistantGatewayDelivery.objects.exists())

    def test_internal_service_transport_bypasses_system_proxy_discovery(self):
        """Fork workers use the direct configured service instead of host proxies."""
        transport = RuntimeTransport(runtime_config())
        self.assertFalse(transport._session.trust_env)

    def test_message_acceptance_conflict_and_automatic_binding(self):
        """User commands provision the partner without a second permission step."""
        other = get_user_model().objects.create_user(username='fictional-message-owner')
        payload = {'client_request_id': 'message-1', 'text': 'Fictional query'}
        first = self.api(AssistantMessageViewSet, 'create', payload, user=other)
        self.assertEqual(first.status_code, 201)
        binding = ensure_partner_binding(other)
        self.assertTrue(binding.enabled)
        self.assertTrue(binding.write_enabled)
        self.assertEqual(
            self.api(
                AssistantMessageViewSet, 'create', payload, user=other
            ).status_code,
            200,
        )
        self.assertEqual(AssistantGatewayDelivery.objects.count(), 1)
        self.assertEqual(
            self.api(
                AssistantMessageViewSet,
                'create',
                {**payload, 'text': 'Different intent'},
                user=other,
            ).status_code,
            409,
        )
        self.assertEqual(AssistantGrant.objects.filter(binding=binding).count(), 0)

    def test_history_uses_only_the_callers_bound_partner(self):
        """Cross-user partner IDs cannot be supplied to the history proxy."""
        transport = RecordingTransport()
        with patch(
            'cangxu.assistant_api.get_runtime_transport', return_value=transport
        ):
            result = self.api(AssistantMessageViewSet, 'list', method='get')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(
                transport.calls[0], ('history', str(self.binding.partner_id))
            )
            result = self.api(
                AssistantMessageViewSet, 'list', {'partner_id': 'another'}, method='get'
            )
            self.assertEqual(result.status_code, 400)
            other = get_user_model().objects.create_user(
                username='fictional-unbound-owner'
            )
            result = self.api(AssistantMessageViewSet, 'list', user=other, method='get')
            self.assertEqual(result.data['items'], [])
            self.assertEqual(len(transport.calls), 1)

    def test_pending_message_order_backoff_and_ack_clears_body(self):
        """A deferred earlier input cannot be overtaken and ack removes the copy."""
        first, _ = queue_message_delivery(
            binding=self.binding,
            client_request_id='first',
            text='first text',
            references=[],
        )
        second, _ = queue_message_delivery(
            binding=self.binding,
            client_request_id='second',
            text='second text',
            references=[],
        )
        now = timezone.now()
        transport = RecordingTransport(fail_first=True)
        self.assertEqual(attempt_pending_deliveries(now=now, transport=transport), 0)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertGreater(first.available_at, now)
        self.assertEqual(second.attempts, 0)
        self.assertEqual(attempt_pending_deliveries(now=now, transport=transport), 0)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(
            attempt_pending_deliveries(
                now=now + timedelta(minutes=2), transport=transport
            ),
            2,
        )
        first.refresh_from_db()
        self.assertEqual(first.payload, {'cleared': True})
        self.assertEqual(
            [call[2] for call in transport.calls], ['first', 'first', 'second']
        )

    def test_binding_lease_excludes_another_dispatcher(self):
        """A live transport owner prevents overlapping acceptance of this queue."""
        queue_message_delivery(
            binding=self.binding,
            client_request_id='lease',
            text='Fictional text',
            references=[],
        )
        self.binding.dispatch_until = timezone.now() + timedelta(seconds=90)
        self.binding.save()
        transport = RecordingTransport()
        self.assertEqual(attempt_pending_deliveries(transport=transport), 0)
        self.assertEqual(transport.calls, [])
        self.binding.dispatch_until = timezone.now() - timedelta(seconds=1)
        self.binding.save()
        self.assertEqual(attempt_pending_deliveries(transport=transport), 1)

    def test_multi_receipt_slots_pin_authority_and_deduplicate(self):
        """Every target gets real receipt work, never synthetic fallback acknowledgement."""
        import uuid

        second = PurchaseReceipt.objects.create(
            idempotency_key=uuid.uuid4(),
            request_hash='b' * 64,
            purchase_order_line=self.receipt.purchase_order_line,
            location=self.receipt.location,
            quantity=1,
            received_by=self.user,
        )
        duty = self.duty(object_ids=[self.receipt.pk, second.pk])
        now = timezone.now()
        self.assertEqual(enqueue_due_duties(now=now), 2)
        self.assertEqual(enqueue_due_duties(now=now), 0)
        self.assertEqual(AssistantDutySlot.objects.count(), 2)
        deliveries = list(AssistantGatewayDelivery.objects.order_by('pk'))
        self.assertEqual(
            {row.payload['work']['receipt_id'] for row in deliveries},
            {str(self.receipt.pk), str(second.pk)},
        )
        AssistantGrant.objects.filter(pk=duty.grant_id).update(version=2)
        transport = RecordingTransport()
        submit_delivery(transport, deliveries[0])
        self.assertEqual(transport.calls[0][3]['grant_version'], 1)
        self.assertEqual(attempt_pending_deliveries(transport=transport), 0)

    def test_event_fanout_requires_ack_and_is_stable(self):
        """Duplicate scans retain one subscriber delivery and defer the outbox ack."""
        AssistantOutboxEvent.objects.all().delete()
        self.duty(interval_seconds=None)
        event = AssistantOutboxEvent.objects.create(
            object_type='purchase_receipt',
            object_id=str(self.receipt.pk),
            object_version=1,
            event_type='receipt.changed',
        )
        self.assertEqual(enqueue_undelivered_events(), 1)
        self.assertEqual(enqueue_undelivered_events(), 0)
        event.refresh_from_db()
        self.assertIsNone(event.delivered_at)
        self.assertEqual(attempt_pending_deliveries(transport=RecordingTransport()), 1)
        event.refresh_from_db()
        self.assertIsNotNone(event.delivered_at)

    def test_task_stop_and_all_writes_are_independent_of_read_checks(self):
        """Persistent write stops do not revoke read authority or pause the duty."""
        from django.core.exceptions import PermissionDenied

        duty = self.duty()
        result = self.api(
            AssistantControlViewSet,
            'create',
            {'client_request_id': 'stop-task', 'scope': 'task', 'task_id': 42},
        )
        self.assertEqual(result.status_code, 201)
        self.assertTrue(
            AssistantRunStop.objects.filter(binding=self.binding, run_id='42').exists()
        )
        with self.assertRaises(PermissionDenied):
            self.link(run_id='42')
        committed = self.link()
        result = self.api(
            AssistantControlViewSet,
            'create',
            {'client_request_id': 'stop-writes', 'scope': 'all-writes'},
        )
        self.assertEqual(result.status_code, 201)
        self.assertFalse(result.data['write_enabled'])
        self.assertEqual(self.link().pk, committed.pk)
        with self.assertRaises(PermissionDenied):
            self.link(key='new-after-stop')
        self.assertEqual(self.query()['receipt_id'], self.receipt.pk)
        duty.refresh_from_db()
        self.assertFalse(duty.paused)
        transport = RecordingTransport()
        attempt_pending_deliveries(transport=transport)
        self.assertIn(
            ('control', str(self.binding.partner_id), 'stop-writes', 'all-writes'),
            transport.calls,
        )

    def test_followup_command_automatically_registers_and_queues_real_scope(self):
        """One user command starts a bounded duty, without a grant-configuration flow."""
        payload = {
            'client_request_id': 'follow-1',
            'text': '跟进这笔虚构收货的归档',
            'receipt_id': self.receipt.pk,
            'attachments': [{'id': self.attachment.pk, 'kind': 'photo'}],
        }
        result = self.api(AssistantReceiptFollowupViewSet, 'create', payload)
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(
            self.api(AssistantReceiptFollowupViewSet, 'create', payload).status_code,
            200,
        )
        self.assertEqual(AssistantDuty.objects.count(), 1)
        duty = AssistantDuty.objects.get()
        self.assertEqual(duty.grant.object_ids, [str(self.receipt.pk)])
        self.assertIn('receipt.link_archive', duty.grant.actions)
        work = AssistantGatewayDelivery.objects.get(kind='duty_check').payload['work']
        self.assertEqual(work['attachments'], payload['attachments'])
        self.assertEqual(work['grant_id'], duty.grant_id)

    def test_periodic_schedule_is_persistent_and_unique(self):
        """Django-Q2 owns the recurring wakeup, independent of browser traffic."""
        from django_q.models import Schedule

        ensure_schedules()
        ensure_schedules()
        self.assertEqual(
            Schedule.objects.filter(func=PERIODIC_DISPATCH_FUNC).count(), 1
        )
