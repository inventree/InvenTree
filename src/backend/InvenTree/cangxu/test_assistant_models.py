"""Verify fail-closed authority and durable assistant metadata constraints."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import (
    AssistantCommand,
    AssistantDuty,
    AssistantGrant,
    AssistantOutboxEvent,
    PartnerBinding,
)


@override_settings(USE_TZ=True)
class AssistantModelTests(TestCase):
    """Use fictional identities and references; no business data is imported."""

    def setUp(self):
        """Create isolated partner identities and an explicitly limited grant."""
        self.user = get_user_model().objects.create_user(username='partner-model-test')
        self.other_user = get_user_model().objects.create_user(
            username='partner-other-test'
        )
        self.binding = PartnerBinding.objects.create(
            deployment_id='fictional-test', user=self.user
        )
        self.grant = AssistantGrant.objects.create(
            binding=self.binding,
            subject=self.user,
            object_type='purchase_receipt',
            object_ids=['42'],
            actions=['read'],
            expires_at=timezone.now() + timedelta(days=1),
            authorization_reference='fictional-user-request-1',
        )

    def command(self, **overrides):
        """Build one valid command for constraint checks."""
        fields = {
            'binding': self.binding,
            'grant': self.grant,
            'grant_version': 1,
            'key': 'request-1',
            'request_hash': 'a' * 64,
            'object_type': 'purchase_receipt',
            'object_id': '42',
            'action': 'read',
            'run_id': 'fictional-run',
            'step_id': 'step-1',
        }
        fields.update(overrides)
        return AssistantCommand(**fields)

    def test_binding_defaults_disabled_and_unique_default_per_deployment_user(self):
        """Creating records alone must not enable autonomous actions."""
        self.assertFalse(self.binding.enabled)
        self.assertFalse(self.binding.write_enabled)
        self.assertFalse(self.binding.is_default)
        self.assertEqual(self.binding.display_name, '工作伙伴')
        extra = PartnerBinding.objects.create(
            deployment_id='fictional-test', user=self.user, display_name='第二伙伴'
        )
        self.assertFalse(extra.is_default)
        self.binding.is_default = True
        self.binding.save()
        with self.assertRaises(ValidationError):
            PartnerBinding.objects.create(
                deployment_id='fictional-test', user=self.user, is_default=True
            )
        PartnerBinding.objects.create(
            deployment_id='other-deployment', user=self.user, is_default=True
        )

    def test_grants_require_explicit_scope_subject_and_lifetime(self):
        """Reject implicit or cross-user authority before storing it."""
        for changes in (
            {'object_ids': []},
            {'object_ids': ['*']},
            {'actions': ['read', 'read']},
            {'actions': ['*']},
            {'subject': self.other_user},
            {'expires_at': None},
            {'limits': []},
            {'object_type': '*'},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                for key, value in changes.items():
                    setattr(self.grant, key, value)
                self.grant.save()
            self.grant.refresh_from_db()

    def test_grant_current_state_and_expiry(self):
        """Logout is irrelevant; disablement, expiry and revocation deny work."""
        self.assertFalse(self.grant.is_active())
        self.binding.enabled = True
        self.binding.save()
        self.assertTrue(self.grant.is_active())
        self.assertFalse(self.grant.is_active(self.grant.expires_at))
        self.user.is_active = False
        self.user.save()
        self.assertFalse(self.grant.is_active())
        self.user.is_active = True
        self.user.save()
        self.grant.revoked_at = timezone.now()
        self.grant.save()
        self.assertFalse(self.grant.is_active())

    def test_continuous_lifetime_is_explicit_and_can_still_expire(self):
        """Continuous authority is deliberate and does not override an expiry."""
        self.binding.enabled = True
        self.binding.save()
        self.grant.continuous = True
        self.grant.expires_at = None
        self.grant.save()
        self.assertTrue(self.grant.is_active())
        self.grant.expires_at = timezone.now() - timedelta(seconds=1)
        self.grant.save()
        self.assertFalse(self.grant.is_active())

    def test_duty_persists_pause_cursor_timezone_and_schedule(self):
        """A restarted scheduler can recover its exact next check and stop state."""
        due = timezone.now() + timedelta(hours=1)
        duty = AssistantDuty.objects.create(
            binding=self.binding,
            grant=self.grant,
            name='Fictional receipt follow-up',
            goal='Check archive completeness',
            interval_seconds=3600,
            next_run_at=due,
            cursor={'last_object_id': '42'},
        )
        duty.refresh_from_db()
        self.assertTrue(duty.paused)
        self.assertEqual(duty.time_zone, 'Asia/Shanghai')
        self.assertEqual(duty.next_run_at, due)
        self.assertEqual(duty.cursor, {'last_object_id': '42'})
        for changes in (
            {'time_zone': 'Invalid/Zone'},
            {'next_run_at': None},
            {'interval_seconds': 0},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                for key, value in changes.items():
                    setattr(duty, key, value)
                duty.save()
            duty.refresh_from_db()

    def test_cross_partner_duty_and_command_rejected(self):
        """A valid foreign grant must not leak into another partner's records."""
        other = PartnerBinding.objects.create(
            deployment_id='fictional-test', user=self.other_user
        )
        with self.assertRaises(ValidationError):
            AssistantDuty.objects.create(
                binding=other, grant=self.grant, name='Other', goal='Check'
            )
        with self.assertRaises(ValidationError):
            self.command(binding=other).save()

    def test_command_database_key_deduplicates_across_runs(self):
        """Even a write bypassing model validation cannot duplicate a partner key."""
        self.command().save()
        duplicate = self.command(run_id='restarted-run')
        with self.assertRaises(IntegrityError), transaction.atomic():
            AssistantCommand.objects.bulk_create([duplicate])
        with self.assertRaises(ValidationError):
            self.command(key='other-key', request_hash='not-a-digest').save()

    def test_outbox_event_identity_and_retry_metadata_survive_reload(self):
        """Retries retain the same event ID and only business references."""
        command = self.command()
        command.save()
        event = AssistantOutboxEvent.objects.create(
            object_type='purchase_receipt',
            object_id='42',
            object_version=1,
            event_type='archive.updated',
            command=command,
            attempts=2,
            last_error='Fictional downstream unavailable',
        )
        original_id = event.event_id
        event.refresh_from_db()
        self.assertEqual(event.event_id, original_id)
        self.assertEqual(event.attempts, 2)
        self.assertIsNone(event.delivered_at)
        self.assertEqual(event.command_id, command.pk)
