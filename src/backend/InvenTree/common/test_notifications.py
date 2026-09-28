"""Unit tests for notification locale translations (Issue #11408)."""

from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from common.models import InvenTreeUserSetting, NotificationMessage
from common.notifications import get_user_language
from InvenTree.unit_test import InvenTreeTestCase
from plugin.builtin.integration.core_notifications import (
    InvenTreeEmailNotifications,
    InvenTreeUINotifications,
)
from plugin.models import PluginConfig

User = get_user_model()


class NotificationLocaleTest(InvenTreeTestCase):
    """Unit tests for notification locale translations."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for notification locale testing."""
        super().setUpTestData()

        # Ensure the email plugin config exists and is active
        PluginConfig.objects.get_or_create(
            key='inventree-email-notification',
            defaults={'name': 'InvenTreeEmailNotifications', 'active': True},
        )

        # Create English user
        cls.user_en = User.objects.create_user(
            username='user_en', email='user.en@example.com', password='password123'
        )
        cls.user_en.profile.language = 'en'
        cls.user_en.profile.save()

        # Create Italian user
        cls.user_it = User.objects.create_user(
            username='user_it', email='user.it@example.com', password='password123'
        )
        cls.user_it.profile.language = 'it'
        cls.user_it.profile.save()

        # Create another Italian user for batching tests
        cls.user_it2 = User.objects.create_user(
            username='user_it2', email='user.it2@example.com', password='password123'
        )
        cls.user_it2.profile.language = 'it'
        cls.user_it2.profile.save()

    def test_get_user_language(self):
        """Test resolving user language from profile, settings, and defaults."""
        self.assertEqual(get_user_language(self.user_en), 'en')
        self.assertEqual(get_user_language(self.user_it), 'it')

        # Test user without language set falls back to system default
        user_no_lang = User.objects.create_user(
            username='user_no_lang', email='no.lang@example.com', password='password123'
        )
        user_no_lang.profile.language = None
        user_no_lang.profile.save()

        self.assertEqual(
            get_user_language(user_no_lang), getattr(settings, 'LANGUAGE_CODE', 'en-us')
        )

        # Test user with InvenTreeUserSetting LANGUAGE override
        with patch.object(InvenTreeUserSetting, 'get_setting', return_value='de'):
            self.assertEqual(get_user_language(user_no_lang), 'de')

    @patch('InvenTree.helpers_email.send_email')
    def test_email_notifications_locale_translation(self, mock_send_email):
        """Test that notification emails are translated according to recipient user locale."""
        email_plugin = InvenTreeEmailNotifications()

        context = {
            'name': _('Items Received'),
            'message': _('Items have been received against a purchase order'),
            'template': {
                'html': 'email/purchase_order_received.html',
                'subject': _('Items Received'),
            },
            'link': 'http://localhost:8000/order/purchase-order/1/',
        }

        # Send notification to both English and Italian recipients
        result = email_plugin.send_notification(
            None, 'test', [self.user_en, self.user_it], context
        )
        self.assertTrue(result)

        # Expect two distinct email dispatch calls (one per locale group)
        self.assertEqual(mock_send_email.call_count, 2)

        calls = mock_send_email.call_args_list

        # Map dispatched emails by recipient email
        dispatched_by_recipient = {}
        for call in calls:
            args, kwargs = call
            subject = args[0]
            recipients = args[2]
            html_message = kwargs.get('html_message', '')
            for r in recipients:
                dispatched_by_recipient[r] = (subject, html_message)

        # Assert English recipient received English text
        self.assertIn(self.user_en.email, dispatched_by_recipient)
        subject_en, html_en = dispatched_by_recipient[self.user_en.email]
        self.assertIn('Items Received', subject_en)
        self.assertIn('Items have been received against a purchase order', html_en)
        self.assertIn('Click on the following link to view this order', html_en)

        # Assert Italian recipient received translated Italian text
        self.assertIn(self.user_it.email, dispatched_by_recipient)
        subject_it, html_it = dispatched_by_recipient[self.user_it.email]
        self.assertIn('Elemento ricevuto', subject_it)
        self.assertIn(
            'Gli elementi sono stati ricevuti a fronte di un ordine di acquisto',
            html_it,
        )
        self.assertIn("Clicca il seguente link per visualizzare quest'ordine", html_it)

    @patch('InvenTree.helpers_email.send_email')
    def test_email_notifications_single_locale_batching(self, mock_send_email):
        """Test that recipients sharing the same locale are batched into a single email."""
        email_plugin = InvenTreeEmailNotifications()

        context = {
            'template': {
                'html': 'email/purchase_order_received.html',
                'subject': _('Items Received'),
            },
            'message': _('Items have been received against a purchase order'),
        }

        result = email_plugin.send_notification(
            None, 'test', [self.user_it, self.user_it2], context
        )
        self.assertTrue(result)

        # Since both users are Italian, only a single email should be sent
        self.assertEqual(mock_send_email.call_count, 1)

        args, _kwargs = mock_send_email.call_args
        recipients = args[2]
        self.assertEqual(len(recipients), 2)
        self.assertIn(self.user_it.email, recipients)
        self.assertIn(self.user_it2.email, recipients)

    def test_ui_notifications_locale_translation(self):
        """Test that UI notification messages are saved with user-specific translations."""
        ui_plugin = InvenTreeUINotifications()

        context = {
            'name': _('Items Received'),
            'message': _('Items have been received against a purchase order'),
            'link': 'http://localhost:8000/order/purchase-order/1/',
        }

        result = ui_plugin.send_notification(
            self.user_en, 'test', [self.user_en, self.user_it], context
        )
        self.assertTrue(result)

        # Verify English UI notification
        msg_en = NotificationMessage.objects.filter(
            user=self.user_en, category='test'
        ).latest('pk')
        self.assertEqual(msg_en.name, 'Items Received')
        self.assertEqual(
            msg_en.message, 'Items have been received against a purchase order'
        )

        # Verify Italian UI notification
        msg_it = NotificationMessage.objects.filter(
            user=self.user_it, category='test'
        ).latest('pk')
        self.assertEqual(msg_it.name, 'Elemento ricevuto')
        self.assertEqual(
            msg_it.message,
            'Gli elementi sono stati ricevuti a fronte di un ordine di acquisto',
        )

    def test_email_notifications_no_recipients(self):
        """Test that email notification returns False when no valid recipients exist."""
        email_plugin = InvenTreeEmailNotifications()

        # No template in context
        self.assertFalse(
            email_plugin.send_notification(None, 'test', [self.user_en], {})
        )

        # Empty users list
        self.assertFalse(
            email_plugin.send_notification(
                None, 'test', [], {'template': {'html': 'email/test_email.html'}}
            )
        )
