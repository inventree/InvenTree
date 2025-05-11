"""Tests for the custom email backend and models."""

from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse

from backend.InvenTree.InvenTree.unit_test import InvenTreeAPITestCase


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
        """Theat that normal django send_mail still works."""
        self._mail_test()

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
