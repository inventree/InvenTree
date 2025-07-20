"""Tests for the custom email backend and models."""

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from anymail.inbound import AnymailInboundMessage
from anymail.signals import AnymailInboundEvent, AnymailTrackingEvent, inbound, tracking

from common.models import EmailMessage, Priority
from InvenTree.helpers_email import send_email
from InvenTree.unit_test import InvenTreeAPITestCase


class EmailTests(InvenTreeAPITestCase):
    """Unit tests for the custom email backend and models."""

    superuser = True
    fixtures = ['users']

    def _mail_test(self):
        self.assertEqual(len(mail.outbox), 0)

        mail.send_mail(
            'test sub',
            'test msg',
            'from@example.org',
            ['to@example.org'],
            html_message='<p>test html msg</p>',
        )

        self.assertEqual(len(mail.outbox), 1)

    def test_email_send_dummy(self):
        """Test that normal django send_mail still works."""
        self._mail_test()

    def test_email_send(self):
        """Test the custom send_email command."""
        resp = send_email(
            subject='test sub',
            body='test msg',
            recipients='to@example.org',
            prio=Priority.VERY_HIGH,
            headers={'X-My-Header': 'my value'},
        )
        self.assertTrue(resp[0])

    # This is needed because django overrides the mail backend during tests
    @override_settings(
        EMAIL_BACKEND='InvenTree.backends.InvenTreeMailLoggingBackend',
        INTERNAL_EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_email_send_custom(self):
        """Theat that normal django send_mail still works."""
        self._mail_test()

        # Check using contexts
        with mail.get_connection() as connection:
            message = mail.EmailMessage(
                subject='test sub',
                body='test msg',
                to=['to@example.org'],
                connection=connection,
                headers={'X-My-Header': 'my value'},
            )
            message.send()

        self.assertEqual(len(mail.outbox), 2)

    @override_settings(
        EMAIL_BACKEND='InvenTree.backends.InvenTreeMailLoggingBackend',
        INTERNAL_EMAIL_BACKEND='anymail.backends.test.EmailBackend',
    )
    def test_email_send_anymail(self):
        """Theat that normal django send_mail still works with anymal."""
        self._mail_test()

        send_email(
            subject='test sub',
            body='test msg',
            recipients=['to@example.org'],
            prio=Priority.VERY_HIGH,
            headers={'X-My-Header': 'my value'},
        )

        self.assertEqual(len(mail.outbox), 2)
        response = self.get(reverse('api-email-list'), expected_code=200)
        self.assertEqual(len(response.data), 2)
        """
        self.assertEqual(response.data[1]['priority'], Priority.VERY_HIGH)
        headers = response.data[1]['headers']
        self.assertIn('X-My-Header', headers)
        self.assertEqual(headers['X-My-Header'], 'my value')
        """

    @override_settings(
        EMAIL_BACKEND='InvenTree.backends.InvenTreeMailLoggingBackend',
        INTERNAL_EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_email_api(self):
        """Test that the email api endpoints work."""
        self.post(reverse('api-email-test'), {'email': 'test@example.org'})

        response = self.get(reverse('api-email-list'), expected_code=200)
        self.assertIn('subject', response.data[0])
        self.assertIn('message_id_key', response.data[0])

        response1 = self.get(
            reverse('api-email-detail', kwargs={'pk': response.data[0]['pk']}),
            expected_code=200,
        )
        self.assertIn('subject', response1.data)
        self.assertIn('message_id_key', response1.data)

    @override_settings(
        EMAIL_BACKEND='InvenTree.backends.InvenTreeMailLoggingBackend',
        INTERNAL_EMAIL_BACKEND='InvenTree.backends.InvenTreeErrorMailBackend',
    )
    def test_backend_error_handling(self):
        """Test that the custom email backend handles errors correctly."""
        with self.assertRaises(ValidationError):
            self._mail_test()

        # There should be an error logged on the message
        msg = EmailMessage.objects.first()
        self.assertEqual(msg.status, EmailMessage.EmailStatus.FAILED)
        self.assertEqual(msg.error_message, 'Test error sending email')


class EmailEventsTests(TestCase):
    """Unit tests for anymail events."""

    def do_send(self, event_type, status):
        """Helper to simulate an email event."""
        # Create email message in db
        msg_key = 'test-message-id' + event_type
        EmailMessage.objects.create(
            subject='test sub',
            body='test msg',
            to=['to@example.com'],
            message_id_key=msg_key,
            priority=Priority.NORMAL,
        )

        # Create a test event
        event = AnymailTrackingEvent(
            event_type=event_type,
            esp_event={'sample': 'data'},
            recipient='to@example.com',
            message_id=msg_key,
        )
        tracking.send(sender=object(), event=event, esp_name='TestESP')

        msg = EmailMessage.objects.filter(
            to=['to@example.com'], message_id_key=msg_key, status=status
        )
        self.assertTrue(msg.exists())
        return msg

    def test_unknown_mail(self):
        """Test that unknown mail is ignored."""
        event = AnymailTrackingEvent(
            event_type='delivered',
            recipient='to@example.com',
            message_id='test-message-id',
        )
        rslt = tracking.send(sender=object(), event=event, esp_name='TestESP')

        self.assertFalse(rslt[0][1])
        self.assertEqual(EmailMessage.objects.all().count(), 0)

    def test_unknown_event(self):
        """Test the unknown event."""
        msg = self.do_send(event_type='unknown', status=None)
        self.assertEqual(msg[0].error_message, "{'sample': 'data'}")

    def test_delivered_event(self):
        """Test the delivered event."""
        self.do_send(event_type='delivered', status=EmailMessage.EmailStatus.DELIVERED)

    def test_opened_event(self):
        """Test the opened event."""
        self.do_send(event_type='opened', status=EmailMessage.EmailStatus.READ)

    def test_clicked_event(self):
        """Test the clicked event."""
        self.do_send(event_type='clicked', status=EmailMessage.EmailStatus.CONFIRMED)

    def test_send_event(self):
        """Test the send event."""
        self.do_send(event_type='sent', status=EmailMessage.EmailStatus.SENT)

    def test_queued_event(self):
        """Test the queued event."""
        msg = self.do_send(event_type='queued', status=None)
        self.assertEqual(msg[0].error_message, None)

    def test_bounced_event(self):
        """Test the bounced event."""
        msg = self.do_send(event_type='bounced', status=EmailMessage.EmailStatus.FAILED)

        self.assertEqual(msg[0].status, EmailMessage.EmailStatus.FAILED)
        self.assertEqual(msg[0].error_code, 'bounced')
        self.assertEqual(msg[0].error_message, "{'sample': 'data'}")

    def test_inbound_event(self):
        """Test the inbound event."""
        # Create a test inbound event
        message = AnymailInboundMessage.construct(
            from_email='user@example.com',
            to='comments@example.net',
            subject='subject',
            text='text body',
            html='html <s>body</s>',
        )
        event = AnymailInboundEvent(message=message, event_type='inbound')
        inbound.send(sender=object(), event=event, esp_name='TestESP')

        # Check that the email was saved
        msg = EmailMessage.objects.filter(to=['comments@example.net']).first()
        self.assertEqual(EmailMessage.objects.count(), 1)
        self.assertEqual(msg.status, EmailMessage.EmailStatus.READ)
        self.assertEqual(msg.direction, EmailMessage.EmailDirection.INBOUND)
        self.assertEqual(msg.body, 'text body')
