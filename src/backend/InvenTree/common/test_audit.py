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


class ParameterAuditTest(InvenTreeAPITestCase):
    """Tests for audit history of Parameter objects."""

    roles = ['part.view', 'part.add', 'part.change', 'part.delete']

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        from common.models import ParameterTemplate
        from part.models import Part, PartCategory

        super().setUpTestData()

        cls.category = PartCategory.objects.create(name='Resistors')
        cls.part = Part.objects.create(
            name='R1', description='Resistor', category=cls.category
        )
        cls.length = ParameterTemplate.objects.create(name='Length', units='mm')
        cls.colour = ParameterTemplate.objects.create(name='Colour')

    def entries(self, **filters):
        """Return audit entries for Parameter objects."""
        from common.models import Parameter

        return AuditLogEntry.objects.filter(
            content_type=Parameter.get_content_type(), **filters
        )

    def part_history(self, part=None, **params):
        """Return the audit history for a part (including parameters)."""
        part = part or self.part

        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': 'part.part', 'model_id': part.pk, **params},
        ).data

    def test_parameter_crud(self):
        """Parameter create / update / delete via the API is recorded against the part."""
        from part.models import Part

        response = self.post(
            reverse('api-parameter-list'),
            {
                'model_type': 'part',
                'model_id': self.part.pk,
                'template': self.length.pk,
                'data': '10',
            },
        )

        pk = response.data['pk']
        url = reverse('api-parameter-detail', kwargs={'pk': pk})

        self.patch(url, {'data': '12'})
        self.delete(url)

        entries = self.entries(object_pk=str(pk))

        self.assertEqual(
            sorted(entries.values_list('action', flat=True)),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

        for entry in entries:
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(entry.parent_content_type, Part.get_content_type())
            self.assertEqual(entry.parent_object_pk, str(self.part.pk))

            # Derived / redundant fields are not recorded
            self.assertNotIn('data_numeric', entry.changes_dict)
            self.assertNotIn('updated_by', entry.changes_dict)

        update = entries.get(action=ACTION.UPDATE)
        self.assertEqual(update.changes_dict, {'data': ['10', '12']})
        self.assertEqual(update.object_repr, 'Length: 12 mm')

        # Shown in the part history (part is not itself audited)
        history = self.part_history()
        self.assertEqual(
            sorted(
                e['action'] for e in history if e['model_type'] == 'common.parameter'
            ),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

    def test_copy_parameters(self):
        """Parameters copied in bulk (copy_parameters_from) are recorded."""
        from common.models import Parameter
        from part.models import Part

        Parameter.objects.create(
            model_type=Part.get_content_type(),
            model_id=self.part.pk,
            template=self.colour,
            data='Blue',
        )

        other = Part.objects.create(name='R2', description='Resistor')
        other.copy_parameters_from(self.part)

        copied = Parameter.objects.get(model_id=other.pk, template=self.colour)

        entry = self.entries(object_pk=str(copied.pk), action=ACTION.CREATE).get()

        self.assertEqual(entry.parent_object_pk, str(other.pk))
        self.assertEqual(entry.changes_dict['data'], [None, 'Blue'])
        self.assertEqual(entry.object_repr, 'Colour: Blue')

    def test_category_parameters(self):
        """Default category parameters (created in bulk) are recorded."""
        from common.models import Parameter
        from part.models import Part, PartCategoryParameterTemplate

        PartCategoryParameterTemplate.objects.create(
            category=self.category, template=self.length, default_value='5'
        )

        part = Part.objects.create(
            name='R3', description='Resistor', category=self.category
        )
        part.copy_category_parameters(self.category)

        parameter = Parameter.objects.get(model_id=part.pk, template=self.length)

        entry = self.entries(object_pk=str(parameter.pk), action=ACTION.CREATE).get()
        self.assertEqual(entry.parent_object_pk, str(part.pk))
        self.assertEqual(entry.changes_dict['data'], [None, '5'])

    def test_parent_permission(self):
        """Parameter entries require permission to view the linked object."""
        from common.models import Parameter
        from part.models import Part

        Parameter.objects.create(
            model_type=Part.get_content_type(),
            model_id=self.part.pk,
            template=self.colour,
            data='Red',
        )

        def parameter_entries():
            return [
                e
                for e in self.get(reverse('api-audit-log-list')).data
                if e['model_type'] == 'common.parameter'
            ]

        self.assertEqual(len(parameter_entries()), 1)

        self.clearRoles()

        self.assertEqual(parameter_entries(), [])

    def test_bulk_create_without_pk(self):
        """Entries are recorded on backends which do not return PKs from bulk_create (e.g. MySQL)."""
        from unittest import mock

        from audit.helpers import audited_bulk_create
        from common.models import Parameter
        from part.models import Part

        original_bulk_create = Parameter.objects.bulk_create

        def bulk_create_without_pk(objs, *args, **kwargs):
            """Simulate a database which does not return primary keys."""
            created = original_bulk_create(objs, *args, **kwargs)

            for obj in created:
                obj.pk = None

            return created

        objs = [
            Parameter(
                model_type=Part.get_content_type(),
                model_id=self.part.pk,
                template=template,
                data=value,
            )
            for template, value in [(self.colour, 'Green'), (self.length, '7')]
        ]

        with mock.patch.object(
            Parameter.objects, 'bulk_create', side_effect=bulk_create_without_pk
        ):
            created = audited_bulk_create(Parameter, objs)

        self.assertEqual(len(created), 2)

        for obj, instance in zip(objs, created, strict=True):
            # Primary keys are populated on the provided objects
            self.assertIsNotNone(obj.pk)
            self.assertEqual(obj.pk, instance.pk)

            entry = self.entries(object_pk=str(obj.pk), action=ACTION.CREATE).get()
            self.assertEqual(entry.changes_dict['data'], [None, obj.data])
            self.assertEqual(entry.parent_object_pk, str(self.part.pk))

    def test_copy_preserves_metadata(self):
        """Copying parameters (via audited_bulk_create) retains their metadata."""
        from common.models import Parameter
        from part.models import Part

        Parameter.objects.create(
            model_type=Part.get_content_type(),
            model_id=self.part.pk,
            template=self.colour,
            data='Blue',
            metadata={'source': 'datasheet'},
        )

        other = Part.objects.create(name='R4', description='Resistor')
        other.copy_parameters_from(self.part)

        copied = Parameter.objects.get(model_id=other.pk, template=self.colour)
        self.assertEqual(copied.metadata, {'source': 'datasheet'})

    def test_requires_metadata_field(self):
        """audited_bulk_create() rejects models without a 'metadata' field."""
        from audit.helpers import audited_bulk_create
        from company.models import Address

        with self.assertRaises(TypeError):
            audited_bulk_create(Address, [])
