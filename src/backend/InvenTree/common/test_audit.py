"""Audit log tests for the Attachment model."""

import uuid

from django.core.files.base import ContentFile
from django.urls import reverse

from audit.models import AuditLogEntry
from common.models import Attachment
from company.models import Company
from InvenTree.unit_test import InvenTreeAPITestCase

ACTION = AuditLogEntry.Action


class AttachmentAuditTest(InvenTreeAPITestCase):
    """Tests for audit history of Attachment objects."""

    roles = [
        'purchase_order.view',
        'purchase_order.add',
        'purchase_order.change',
        'purchase_order.delete',
    ]

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.company = Company.objects.create(name='Attachment Co', is_supplier=True)

    def upload(self, company=None, filename=None, **data):
        """Upload a file attachment against a company, via the API."""
        company = company or self.company
        filename = filename or f'audit_{uuid.uuid4().hex[:8]}.txt'

        response = self.post(
            reverse('api-attachment-list'),
            data={
                'model_type': 'company',
                'model_id': company.pk,
                'attachment': ContentFile(b'Hello world', name=filename),
                **data,
            },
            format='multipart',
            expected_code=201,
        )

        attachment = Attachment.objects.get(pk=response.data['pk'])

        # Remove the uploaded file from storage once the test is complete
        self.addCleanup(
            lambda: (
                attachment.attachment.storage.delete(attachment.attachment.name)
                if Attachment.objects.filter(pk=attachment.pk).exists()
                else None
            )
        )

        return attachment

    def entries(self, attachment, **filters):
        """Return audit entries for an attachment (by PK - which survives deletion)."""
        return AuditLogEntry.objects.filter(
            content_type=Attachment.get_content_type(),
            object_pk=str(attachment if isinstance(attachment, int) else attachment.pk),
            **filters,
        )

    def company_history(self, company=None, **params):
        """Return the audit history for a company (including attachments)."""
        company = company or self.company

        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': 'company.company', 'model_id': company.pk, **params},
        ).data

    def test_upload(self):
        """Uploading an attachment records the filename only, against the linked object."""
        attachment = self.upload(filename='datasheet.txt', comment='Datasheet')

        # Sanity check: the stored path includes the upload directory
        self.assertNotEqual(attachment.attachment.name, 'datasheet.txt')
        self.assertTrue(attachment.attachment.name.endswith('datasheet.txt'))

        entry = self.entries(attachment, action=ACTION.CREATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['attachment'], [None, 'datasheet.txt'])
        self.assertEqual(entry.changes_dict['comment'], [None, 'Datasheet'])
        self.assertEqual(entry.object_repr, 'datasheet.txt')

        # Linked to the attached object
        self.assertEqual(entry.parent_content_type, Company.get_content_type())
        self.assertEqual(entry.parent_object_pk, str(self.company.pk))

        # Derived fields are not recorded
        for field in ['thumbnail', 'is_image', 'file_size']:
            self.assertNotIn(field, entry.changes_dict)

        # The follow-up save (file size) and thumbnail task do not create extra entries
        self.assertFalse(self.entries(attachment, action=ACTION.UPDATE).exists())

        # Shown in the company history
        self.assertIn(
            ('common.attachment', ACTION.CREATE),
            [(e['model_type'], e['action']) for e in self.company_history()],
        )

    def test_edit_and_rename(self):
        """Comment edits and file renames are recorded (filename only)."""
        attachment = self.upload(filename='original.txt')
        url = reverse('api-attachment-detail', kwargs={'pk': attachment.pk})

        self.patch(url, {'comment': 'Updated comment'})

        entry = self.entries(attachment, action=ACTION.UPDATE).get()
        self.assertEqual(entry.changes_dict, {'comment': ['', 'Updated comment']})

        new_name = f'renamed_{uuid.uuid4().hex[:8]}.txt'
        self.patch(url, {'filename': new_name})

        attachment.refresh_from_db()
        self.addCleanup(
            lambda: attachment.attachment.storage.delete(attachment.attachment.name)
        )

        rename = (
            self
            .entries(attachment, action=ACTION.UPDATE)
            .filter(changes__has_key='attachment')
            .get()
        )

        self.assertEqual(rename.changes_dict['attachment'], ['original.txt', new_name])

        for value in rename.changes_dict['attachment']:
            self.assertNotIn('/', value)

    def test_delete(self):
        """Deleted attachments remain in the history of the linked object."""
        attachment = self.upload(filename='obsolete.txt')
        pk = attachment.pk

        self.delete(reverse('api-attachment-detail', kwargs={'pk': pk}))

        entry = self.entries(pk, action=ACTION.DELETE).get()

        self.assertEqual(entry.object_repr, 'obsolete.txt')
        self.assertEqual(entry.changes_dict['attachment'], ['obsolete.txt', None])
        self.assertEqual(entry.parent_object_pk, str(self.company.pk))

        self.assertIn(
            ('common.attachment', ACTION.DELETE),
            [(e['model_type'], e['action']) for e in self.company_history()],
        )

    def test_parent_deleted(self):
        """Attachments deleted along with their object retain the parent reference."""
        company = Company.objects.create(name='Temporary Co')
        company_pk = company.pk

        attachment = self.upload(company=company, filename='temp.txt')
        attachment_pk = attachment.pk

        company.delete()

        entry = self.entries(attachment_pk, action=ACTION.DELETE).get()
        self.assertEqual(entry.parent_object_pk, str(company_pk))

    def test_parent_permission(self):
        """Attachment entries require permission to view the linked object."""
        self.upload(filename='private.txt')

        def attachment_entries():
            return [
                e
                for e in self.get(reverse('api-audit-log-list')).data
                if e['model_type'] == 'common.attachment'
            ]

        self.assertEqual(len(attachment_entries()), 1)

        # The Attachment model itself requires no permissions,
        # but without access to companies the attachment history is hidden
        self.clearRoles()

        self.assertEqual(attachment_entries(), [])
        self.assertEqual(
            self.get(
                reverse('api-audit-log-list'), {'model_type': 'common.attachment'}
            ).data,
            [],
        )

        entry = self.entries(Attachment.objects.get().pk).first()
        self.get(
            reverse('api-audit-log-detail', kwargs={'pk': entry.pk}), expected_code=404
        )
