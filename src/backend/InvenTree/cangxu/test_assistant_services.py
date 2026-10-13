"""Synthetic command-boundary tests; these are not business tool acceptance."""

from dataclasses import replace
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from django.utils import timezone

from stock.models import StockLocation
from users.models import RuleSet

from .assistant_models import (
    AssistantCommand,
    AssistantGrant,
    AssistantOutboxEvent,
    PartnerBinding,
)
from .assistant_services import CommandConflictError, ToolDefinition, execute_command


@override_settings(USE_TZ=True)
class AssistantCommandBoundaryTests(TestCase):
    """Verify authority, atomic rollback and lost-response retry behavior."""

    def setUp(self):
        """Create a fictional owner and a bounded location adapter."""
        self.user = get_user_model().objects.create_user(
            username='fictional-partner-owner'
        )
        self.group = Group.objects.create(name='Fictional stock operators')
        self.user.groups.add(self.group)
        self.rule = RuleSet.objects.get(group=self.group, name='stock')
        self.rule.can_change = True
        self.rule.save()
        self.location = StockLocation.objects.create(name='Fictional staging')
        self.binding = PartnerBinding.objects.create(
            deployment_id='fictional-test',
            user=self.user,
            enabled=True,
            write_enabled=True,
        )
        self.grant = AssistantGrant.objects.create(
            binding=self.binding,
            subject=self.user,
            object_type='stocklocation',
            object_ids=[str(self.location.pk)],
            actions=['test.rename'],
            continuous=True,
            authorization_reference='fictional-explicit-command',
        )
        self.tool = ToolDefinition(
            action='test.rename',
            object_type='stocklocation',
            permission_role='stock',
            permission='change',
            execute=self.rename_location,
            event_type='test.changed',
        )

    @staticmethod
    def rename_location(user, object_id, arguments):
        """Use a real database write to prove the boundary shares its transaction."""
        location = StockLocation.objects.select_for_update().get(pk=object_id)
        location.name = arguments['name']
        location.save()
        return {'location_id': location.pk, 'name': location.name}, 1

    def execute(self, **overrides):
        """Submit the same logical command unless a test overrides its intent."""
        options = {
            'binding_id': self.binding.pk,
            'grant_id': self.grant.pk,
            'grant_version': 1,
            'key': 'fictional-command-1',
            'object_id': str(self.location.pk),
            'run_id': 'fictional-run',
            'step_id': 'rename',
            'arguments': {'name': 'Fictional verified'},
            'tool': self.tool,
        }
        options.update(overrides)
        return execute_command(**options)

    def test_response_loss_returns_same_receipt_without_repeating_effect(self):
        """A retry returns the committed outcome without calling the adapter again."""
        receipt = self.execute()
        retry = self.execute(
            run_id='recovered-run',
            step_id='recovered-step',
            tool=replace(self.tool, execute=lambda *_: self.fail('replayed')),
        )
        self.assertEqual(receipt.pk, retry.pk)
        self.assertEqual(retry.status, AssistantCommand.Status.SUCCEEDED)
        self.assertEqual(AssistantOutboxEvent.objects.count(), 1)
        self.location.refresh_from_db()
        self.assertEqual(self.location.name, 'Fictional verified')
        self.assertEqual(retry.result_reference['location_id'], self.location.pk)

    def test_same_key_changed_intent_conflicts(self):
        """Different arguments cannot silently reuse the original success."""
        self.execute()
        with self.assertRaises(CommandConflictError):
            self.execute(arguments={'name': 'Another value'})
        self.assertEqual(AssistantCommand.objects.count(), 1)

    def test_failure_rolls_back_domain_receipt_and_event(self):
        """An exception after a domain write leaves no committed partial effect."""

        def failing_adapter(*args):
            self.rename_location(*args)
            raise RuntimeError('Synthetic failure after domain write')

        with self.assertRaises(RuntimeError):
            self.execute(tool=replace(self.tool, execute=failing_adapter))
        self.location.refresh_from_db()
        self.assertEqual(self.location.name, 'Fictional staging')
        self.assertFalse(AssistantCommand.objects.exists())
        self.assertFalse(AssistantOutboxEvent.objects.exists())

    def test_revocation_and_stale_grant_block_execution_and_replay(self):
        """Persisted revocation is checked even if the caller holds an old object."""
        self.execute()
        AssistantGrant.objects.filter(pk=self.grant.pk).update(
            revoked_at=timezone.now()
        )
        with self.assertRaises(PermissionDenied):
            self.execute()
        AssistantGrant.objects.filter(pk=self.grant.pk).update(
            revoked_at=None, version=2
        )
        with self.assertRaises(PermissionDenied):
            self.execute(key='new-command')

    def test_permission_removal_is_seen_between_commands(self):
        """Worker lifetime does not keep stale role grants alive."""
        self.execute()
        self.user.groups.clear()
        with self.assertRaises(PermissionDenied):
            self.execute(key='after-role-removal')

    def test_disabled_user_binding_or_writes_block_new_actions(self):
        """Independent persistent controls all stop new effects."""
        for field in ('enabled', 'write_enabled'):
            PartnerBinding.objects.filter(pk=self.binding.pk).update(**{field: False})
            with self.assertRaises(PermissionDenied):
                self.execute()
            PartnerBinding.objects.filter(pk=self.binding.pk).update(**{field: True})
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        with self.assertRaises(PermissionDenied):
            self.execute()

    def test_scope_expiry_and_unsupported_limits_are_not_ignored(self):
        """No broad authority is inferred from a valid but mismatched grant."""
        with self.assertRaises(PermissionDenied):
            self.execute(object_id='999999')
        AssistantGrant.objects.filter(pk=self.grant.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        with self.assertRaises(PermissionDenied):
            self.execute()
        AssistantGrant.objects.filter(pk=self.grant.pk).update(
            expires_at=None, limits={'quantity': 1}
        )
        with self.assertRaises(PermissionDenied):
            self.execute()

    def test_cross_partner_grant_is_rejected(self):
        """Caller cannot combine its binding with another owner's authority."""
        other = get_user_model().objects.create_user(username='fictional-other-owner')
        binding = PartnerBinding.objects.create(
            deployment_id='fictional-test', user=other, enabled=True, write_enabled=True
        )
        with self.assertRaises(PermissionDenied):
            self.execute(binding_id=binding.pk)
