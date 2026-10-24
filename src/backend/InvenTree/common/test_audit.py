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

    def test_lazy_string_value(self):
        """Lazy translation strings (e.g. a generated report comment) are recorded as plain strings."""
        from django.utils.translation import gettext_lazy

        self.company.create_attachment(
            link='https://example.com/report', comment=gettext_lazy('Generated')
        )

        attachment = Attachment.objects.get(link='https://example.com/report')

        entry = self.entries(attachment, action=ACTION.CREATE).get()
        self.assertEqual(entry.changes_dict['comment'], [None, 'Generated'])

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

        with (
            mock.patch(
                'InvenTree.helpers_db.bulk_insert_returns_pks', return_value=False
            ),
            mock.patch.object(
                Parameter.objects, 'bulk_create', side_effect=bulk_create_without_pk
            ),
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

    def test_bulk_create_api(self):
        """Entries for a bulk API create are written together, with the request context."""
        response = self.post(
            reverse('api-parameter-list'),
            [
                {
                    'model_type': 'part',
                    'model_id': self.part.pk,
                    'template': template.pk,
                    'data': value,
                }
                for template, value in [(self.length, '10'), (self.colour, 'Red')]
            ],
            format='json',
        )

        pks = [str(item['pk']) for item in response.data]
        entries = self.entries(object_pk__in=pks, action=ACTION.CREATE)

        self.assertEqual(entries.count(), 2)
        self.assertEqual(len({entry.cid for entry in entries}), 1)

        for entry in entries:
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(entry.remote_addr, '127.0.0.1')
            self.assertEqual(entry.parent_object_pk, str(self.part.pk))

    def test_bulk_create_api_error(self):
        """No entries are written if any item in a bulk API create is invalid."""
        self.post(
            reverse('api-parameter-list'),
            [
                {
                    'model_type': 'part',
                    'model_id': self.part.pk,
                    'template': self.colour.pk,
                    'data': 'Red',
                },
                {'model_type': 'part', 'model_id': self.part.pk, 'template': 9999},
            ],
            format='json',
            expected_code=400,
        )

        self.assertFalse(self.entries().exists())

    def test_bulk_create_single_insert(self):
        """audited_bulk_create() writes all audit entries with a single query."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from audit.helpers import audited_bulk_create
        from common.models import Parameter
        from part.models import Part

        parts = [
            Part.objects.create(name=f'R{idx}', description='Resistor')
            for idx in range(5)
        ]

        objs = [
            Parameter(
                model_type=Part.get_content_type(),
                model_id=part.pk,
                template=self.colour,
                data='Red',
            )
            for part in parts
        ]

        with CaptureQueriesContext(connection) as context:
            audited_bulk_create(Parameter, objs)

        # Table name quoting differs between backends (e.g. backticks for MySQL)
        table = AuditLogEntry._meta.db_table

        inserts = [
            q
            for q in context.captured_queries
            if q['sql'].startswith('INSERT INTO') and table in q['sql']
        ]

        self.assertEqual(len(inserts), 1)
        self.assertEqual(self.entries(action=ACTION.CREATE).count(), 5)

    def test_requires_metadata_field(self):
        """audited_bulk_create() rejects models without a 'metadata' field."""
        from audit.helpers import audited_bulk_create
        from company.models import Address

        with self.assertRaises(TypeError):
            audited_bulk_create(Address, [])


class ConfigurationAuditTest(InvenTreeAPITestCase):
    """Tests for audit history of ParameterTemplate / ProjectCode / CustomUnit objects."""

    roles = ['part.view', 'part.add', 'part.change', 'part.delete']

    def entries(self, model, pk, **filters):
        """Return audit entries for a given object (by PK - which survives deletion)."""
        from django.contrib.contenttypes.models import ContentType

        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(model),
            object_pk=str(pk),
            **filters,
        )

    def history(self, model_type, pk):
        """Return the audit history for an object, with change details."""
        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': model_type, 'model_id': pk, 'changes_detail': True},
        ).data

    def check_crud(self, model, list_url, detail_name, create, update):
        """Create, update and delete an object via the API, and check the audit trail.

        Returns the UPDATE entry.
        """
        response = self.post(reverse(list_url), create)
        pk = response.data['pk']

        url = reverse(detail_name, kwargs={'pk': pk})
        self.patch(url, update)
        self.delete(url)

        entries = self.entries(model, pk)

        self.assertEqual(
            sorted(entries.values_list('action', flat=True)),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

        for entry in entries:
            self.assertEqual(entry.actor, self.user)
            self.assertIsNone(entry.parent_content_type)
            self.assertNotIn('metadata', entry.changes_dict)

        return entries.get(action=ACTION.UPDATE)

    def test_parameter_template(self):
        """ParameterTemplate changes are recorded (including choice field labels)."""
        from common.models import ParameterTemplate

        update = self.check_crud(
            ParameterTemplate,
            'api-parameter-template-list',
            'api-parameter-template-detail',
            {'name': 'Resistance', 'units': 'ohm', 'description': 'Resistance'},
            {'units': 'kohm', 'unique': ParameterTemplate.UniqueOptions.GLOBAL},
        )

        self.assertEqual(update.changes_dict['units'], ['ohm', 'kohm'])
        self.assertEqual(
            update.changes_dict['unique'],
            [
                ParameterTemplate.UniqueOptions.NONE,
                ParameterTemplate.UniqueOptions.GLOBAL,
            ],
        )
        self.assertEqual(update.object_repr, 'Resistance (kohm)')

    def test_parameter_template_display(self):
        """Choice field values are shown with their labels in the API."""
        from common.models import ParameterTemplate

        template = ParameterTemplate.objects.create(name='Colour')
        template.unique = ParameterTemplate.UniqueOptions.MODEL_TYPE
        template.save()

        [entry] = [
            e
            for e in self.history('common.parametertemplate', template.pk)
            if e['action'] == ACTION.UPDATE
        ]
        [row] = entry['changes_detail']

        self.assertEqual(row['field'], 'unique')
        self.assertEqual(
            row['new_display'], str(ParameterTemplate.UniqueOptions.MODEL_TYPE.label)
        )

    def test_project_code(self):
        """ProjectCode changes are recorded (including the responsible owner)."""
        from common.models import ProjectCode
        from users.models import Owner

        owner = Owner.get_owner(self.user)

        update = self.check_crud(
            ProjectCode,
            'api-project-code-list',
            'api-project-code-detail',
            {'code': 'PRJ-001', 'description': 'Project one'},
            {'description': 'Project 1', 'responsible': owner.pk, 'active': False},
        )

        self.assertEqual(
            update.changes_dict['description'], ['Project one', 'Project 1']
        )
        self.assertEqual(update.changes_dict['responsible'], [None, owner.pk])
        self.assertEqual(update.changes_dict['active'], [True, False])
        self.assertEqual(update.object_repr, 'PRJ-001')

    def test_custom_unit(self):
        """CustomUnit changes are recorded, and the unit registry still reloads."""
        from common.models import CustomUnit
        from InvenTree.conversion import convert_physical_value

        update = self.check_crud(
            CustomUnit,
            'api-custom-unit-list',
            'api-custom-unit-detail',
            {'name': 'furlong', 'definition': '220 yard', 'symbol': 'fur'},
            {'definition': '201.168 meter'},
        )

        self.assertEqual(
            update.changes_dict['definition'], ['220 yard', '201.168 meter']
        )
        self.assertEqual(update.object_repr, 'furlong')

        # Registry reload (post_save receiver) is unaffected by auditing
        CustomUnit.objects.create(name='smoot', definition='1.7018 meter')
        self.assertAlmostEqual(
            float(convert_physical_value('1 smoot', 'meter')), 1.7018, places=4
        )


class GlobalSettingAuditTest(InvenTreeAPITestCase):
    """Audit tests for global settings."""

    roles = 'all'

    def entries(self, **filters):
        """Return audit entries for global settings."""
        from django.contrib.contenttypes.models import ContentType

        from common.models import InvenTreeSetting

        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(InvenTreeSetting), **filters
        )

    def set_value(self, key, value):
        """Change a global setting via the API."""
        self.patch(
            reverse('api-global-setting-detail', kwargs={'key': key}), {'value': value}
        )

    def test_setting_change(self):
        """Changes to a global setting are recorded (key and value only)."""
        self.set_value('INVENTREE_INSTANCE', 'Audit Instance')

        entry = self.entries(object_repr='INVENTREE_INSTANCE').order_by('pk').last()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['value'][1], 'Audit Instance')

        for field in entry.changes_dict:
            self.assertIn(field, ['key', 'value'])

    def test_unchanged_value(self):
        """Saving a setting with an unchanged value is not recorded."""
        self.set_value('AUDIT_LOG_DELETE_OLD_ENTRIES', True)

        n = self.entries().count()
        self.set_value('AUDIT_LOG_DELETE_OLD_ENTRIES', True)

        self.assertEqual(self.entries().count(), n)

    def test_system_settings_not_recorded(self):
        """Settings which are written automatically by the system are not recorded."""
        from unittest import mock

        from common.models import InvenTreeSetting
        from common.settings import set_global_setting

        n = self.entries().count()

        # Internal settings (e.g. written by every scheduled task run)
        set_global_setting('_TEST_TASK_ATTEMPT', 'now', change_user=None)

        # Changing a setting which requires a restart also sets 'SERVER_RESTART_REQUIRED'
        # Note: A setting which is not overridden by the environment is used here
        # (e.g. PLUGIN_ON_STARTUP is set via environment variable in the docker image)
        def requires_restart(setting):
            return setting.key == 'INVENTREE_INSTANCE'

        with mock.patch.object(
            InvenTreeSetting,
            'requires_restart',
            autospec=True,
            side_effect=requires_restart,
        ):
            self.assertFalse(InvenTreeSetting.get_setting('SERVER_RESTART_REQUIRED'))
            self.set_value('INVENTREE_INSTANCE', 'Restart Instance')
            self.assertTrue(InvenTreeSetting.get_setting('SERVER_RESTART_REQUIRED'))

        keys = list(
            self.entries().order_by('pk')[n:].values_list('object_repr', flat=True)
        )

        self.assertEqual(keys, ['INVENTREE_INSTANCE'])

    def test_protected_value(self):
        """The values of protected settings are never recorded."""
        from unittest import mock

        from audit.models import MASKED_VALUE
        from common.models import InvenTreeSetting

        with mock.patch.object(InvenTreeSetting, 'is_protected', return_value=True):
            self.set_value('INVENTREE_INSTANCE', 'secret-value')

        entry = self.entries(object_repr='INVENTREE_INSTANCE').order_by('pk').last()

        self.assertEqual(entry.changes_dict['value'][1], MASKED_VALUE)

        for field in ['changes', 'changes_text', 'additional_data', 'object_repr']:
            self.assertNotIn('secret-value', str(getattr(entry, field)))

    def test_disable_audit_log(self):
        """Disabling (and re-enabling) the audit log is always recorded."""
        self.set_value('AUDIT_LOG_ENABLED', False)

        entry = self.entries(object_repr='AUDIT_LOG_ENABLED').order_by('pk').last()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['value'], ['True', 'False'])

        # Other changes are no longer recorded
        n = AuditLogEntry.objects.count()
        self.set_value('INVENTREE_INSTANCE', 'Not recorded')
        self.set_value('AUDIT_LOG_DELETE_DAYS', 7)
        Company.objects.create(name='Not recorded')

        # ...except for changes to the audit log settings themselves
        self.assertEqual(AuditLogEntry.objects.count(), n + 1)
        self.assertEqual(
            AuditLogEntry.objects.order_by('pk').last().object_repr,
            'AUDIT_LOG_DELETE_DAYS',
        )

        self.set_value('AUDIT_LOG_ENABLED', True)

        entry = self.entries(object_repr='AUDIT_LOG_ENABLED').order_by('pk').last()
        self.assertEqual(entry.changes_dict['value'], ['False', 'True'])

    def test_staff_only(self):
        """Setting history is only visible to staff users."""
        self.set_value('INVENTREE_INSTANCE', 'Staff only')

        url = reverse('api-audit-log-list')
        params = {'model_type': 'common.inventreesetting'}

        self.assertGreater(len(self.get(url, params).data), 0)

        # Staff users without the 'admin' role can still view settings history
        self.user.is_superuser = False
        self.user.save()
        self.clearRoles()

        self.assertGreater(len(self.get(url, params).data), 0)

    def test_default_value_not_recorded(self):
        """Settings created automatically (with their default value) are not recorded."""
        from common.models import InvenTreeSetting
        from common.settings import get_global_setting

        InvenTreeSetting.objects.filter(key='AUDIT_LOG_DELETE_DAYS').delete()

        n = self.entries().count()

        # Reading the setting creates it (with the default value)
        get_global_setting('AUDIT_LOG_DELETE_DAYS')
        self.assertTrue(
            InvenTreeSetting.objects.filter(key='AUDIT_LOG_DELETE_DAYS').exists()
        )

        self.assertEqual(self.entries().count(), n)
