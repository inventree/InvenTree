"""Tests for mechanisms in common."""

import io
import json
import time
from datetime import timedelta
from http import HTTPStatus
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.urls import reverse

import PIL

import common.validators
from common.settings import get_global_setting, set_global_setting
from InvenTree.helpers import str2bool
from InvenTree.unit_test import (
    AdminTestCase,
    InvenTreeAPITestCase,
    InvenTreeTestCase,
    PluginMixin,
)
from part.models import Part, PartParameterTemplate
from plugin import registry
from plugin.models import NotificationUserSetting

from .api import WebhookView
from .models import (
    Attachment,
    CustomUnit,
    InvenTreeCustomUserStateModel,
    InvenTreeSetting,
    InvenTreeUserSetting,
    NotesImage,
    NotificationEntry,
    NotificationMessage,
    ProjectCode,
    SelectionList,
    SelectionListEntry,
    WebhookEndpoint,
    WebhookMessage,
)

CONTENT_TYPE_JSON = 'application/json'


class AttachmentTest(InvenTreeAPITestCase):
    """Unit tests for the 'Attachment' model."""

    fixtures = ['part', 'category', 'location']

    def generate_file(self, fn: str):
        """Generate an attachment file object."""
        file_object = io.StringIO('Some dummy data')
        file_object.seek(0)

        return ContentFile(file_object.getvalue(), fn)

    def test_filename_validation(self):
        """Test that the filename validation works as expected.

        The django file-upload mechanism should sanitize filenames correctly.
        """
        part = Part.objects.first()

        filenames = {
            'test.txt': 'test.txt',
            'r####at.mp4': 'rat.mp4',
            '../../../win32.dll': 'win32.dll',
            'ABC!@#$%^&&&&&&&)-XYZ-(**&&&\\/QqQ.sqlite': 'QqQ.sqlite',
            '/var/log/inventree.log': 'inventree.log',
            'c:\\Users\\admin\\passwd.txt': 'cUsersadminpasswd.txt',
            '8&&&8.txt': '88.txt',
        }

        for fn, expected in filenames.items():
            attachment = Attachment.objects.create(
                attachment=self.generate_file(fn),
                comment=f'Testing filename: {fn}',
                model_type='part',
                model_id=part.pk,
            )

            expected_path = f'attachments/part/{part.pk}/{expected}'
            self.assertEqual(attachment.attachment.name, expected_path)
            self.assertEqual(attachment.file_size, 15)

        self.assertEqual(part.attachments.count(), len(filenames.keys()))

        # Delete any attachments after the test is completed
        for attachment in part.attachments.all():
            path = attachment.attachment.name
            attachment.delete()

            # Remove uploaded files to prevent them sticking around
            if default_storage.exists(path):
                default_storage.delete(path)

        self.assertEqual(
            Attachment.objects.filter(model_type='part', model_id=part.pk).count(), 0
        )

    def test_mixin(self):
        """Test that the mixin class works as expected."""
        part = Part.objects.first()

        self.assertEqual(part.attachments.count(), 0)

        part.create_attachment(
            attachment=self.generate_file('test.txt'), comment='Hello world'
        )

        self.assertEqual(part.attachments.count(), 1)

        attachment = part.attachments.first()

        self.assertEqual(attachment.comment, 'Hello world')
        self.assertIn(f'attachments/part/{part.pk}/test', attachment.attachment.name)

    def test_upload_via_api(self):
        """Test that we can upload attachments via the API."""
        part = Part.objects.first()
        url = reverse('api-attachment-list')

        data = {
            'model_type': 'part',
            'model_id': part.pk,
            'link': 'https://www.google.com',
            'comment': 'Some appropriate comment',
        }

        # Start without appropriate permissions
        # User must have 'part.change' to upload an attachment against a Part instance
        self.logout()
        self.user.is_staff = False
        self.user.is_superuser = False
        self.user.save()
        self.clearRoles()

        # Check without login (401)
        response = self.post(url, data, expected_code=401)

        self.login()

        response = self.post(url, data, expected_code=403)

        self.assertIn(
            'User does not have permission to create or edit attachments for this model',
            str(response.data['detail']),
        )

        # Add the required permission
        self.assignRole('part.change')

        # Upload should now work!
        response = self.post(url, data, expected_code=201)

        pk = response.data['pk']

        # Edit the attachment via API
        response = self.patch(
            reverse('api-attachment-detail', kwargs={'pk': pk}),
            {'comment': 'New comment'},
            expected_code=200,
        )

        self.assertEqual(response.data['comment'], 'New comment')

        attachment = Attachment.objects.get(pk=pk)
        self.assertEqual(attachment.comment, 'New comment')

        # And check that we cannot edit the attachment without the correct permissions
        self.clearRoles()

        self.patch(
            reverse('api-attachment-detail', kwargs={'pk': pk}),
            {'comment': 'New comment 2'},
            expected_code=403,
        )

        # Try to delete the attachment via API (should fail)
        attachment = part.attachments.first()
        url = reverse('api-attachment-detail', kwargs={'pk': attachment.pk})
        response = self.delete(url, expected_code=403)
        self.assertIn(
            'User does not have permission to delete this attachment',
            str(response.data['detail']),
        )

        # Assign 'delete' permission to 'part' model
        self.assignRole('part.delete')
        response = self.delete(url, expected_code=204)


class SettingsTest(InvenTreeTestCase):
    """Tests for the 'settings' model."""

    fixtures = ['settings']

    def test_settings_objects(self):
        """Test fixture loading and lookup for settings."""
        # There should be two settings objects in the database
        settings = InvenTreeSetting.objects.all()

        self.assertGreaterEqual(settings.count(), 2)

        instance_name = InvenTreeSetting.objects.get(pk=1)
        self.assertEqual(instance_name.key, 'INVENTREE_INSTANCE')
        self.assertEqual(instance_name.value, 'My very first InvenTree Instance')

        # Check object lookup (case insensitive)
        self.assertEqual(
            InvenTreeSetting.get_setting_object('iNvEnTrEE_inSTanCE').pk, 1
        )

    def test_settings_functions(self):
        """Test settings functions and properties."""
        # define settings to check
        instance_ref = 'INVENTREE_INSTANCE'
        instance_obj = InvenTreeSetting.get_setting_object(instance_ref, cache=False)

        stale_ref = 'STOCK_STALE_DAYS'
        stale_days = InvenTreeSetting.get_setting_object(stale_ref, cache=False)

        report_size_obj = InvenTreeSetting.get_setting_object(
            'REPORT_DEFAULT_PAGE_SIZE'
        )

        # check settings base fields
        self.assertEqual(instance_obj.name, 'Server Instance Name')
        self.assertEqual(
            instance_obj.get_setting_name(instance_ref), 'Server Instance Name'
        )
        self.assertEqual(
            instance_obj.description, 'String descriptor for the server instance'
        )
        self.assertEqual(
            instance_obj.get_setting_description(instance_ref),
            'String descriptor for the server instance',
        )

        # check units
        self.assertEqual(instance_obj.units, '')
        self.assertEqual(instance_obj.get_setting_units(instance_ref), '')
        self.assertEqual(instance_obj.get_setting_units(stale_ref), 'days')

        # check as_choice
        self.assertEqual(instance_obj.as_choice(), 'My very first InvenTree Instance')
        self.assertEqual(report_size_obj.as_choice(), 'A4')

        # check is_choice
        self.assertEqual(instance_obj.is_choice(), False)
        self.assertEqual(report_size_obj.is_choice(), True)

        # check setting_type
        self.assertEqual(instance_obj.setting_type(), 'string')
        self.assertEqual(stale_days.setting_type(), 'integer')

        # check as_int
        self.assertEqual(stale_days.as_int(), 0)
        self.assertEqual(
            instance_obj.as_int(), 'InvenTree'
        )  # not an int -> return default

        # check to_native_value
        self.assertEqual(stale_days.to_native_value(), 0)

    def test_allValues(self):
        """Make sure that the allValues functions returns correctly."""
        # define testing settings

        # check a few keys
        result = InvenTreeSetting.allValues()
        self.assertIn('INVENTREE_INSTANCE', result)
        self.assertIn('PART_COPY_TESTS', result)
        self.assertIn('STOCK_OWNERSHIP_CONTROL', result)
        self.assertIn('SIGNUP_GROUP', result)
        self.assertIn('SERVER_RESTART_REQUIRED', result)

        result = InvenTreeSetting.allValues(exclude_hidden=True)
        self.assertNotIn('SERVER_RESTART_REQUIRED', result)

    def test_all_settings(self):
        """Make sure that the all_settings function returns correctly."""
        result = InvenTreeSetting.all_settings()
        self.assertIn('INVENTREE_INSTANCE', result)
        self.assertIsInstance(result['INVENTREE_INSTANCE'], InvenTreeSetting)

    @mock.patch('common.models.InvenTreeSetting.get_setting_definition')
    def test_check_all_settings(self, get_setting_definition):
        """Make sure that the check_all_settings function returns correctly."""
        # define partial schema
        settings_definition = {
            'AB': {  # key that's has not already been accessed
                'required': True
            },
            'CD': {'required': True, 'protected': True},
            'EF': {},
        }

        def mocked(key, **kwargs):
            return settings_definition.get(key, {})

        get_setting_definition.side_effect = mocked

        self.assertEqual(
            InvenTreeSetting.check_all_settings(
                settings_definition=settings_definition
            ),
            (False, ['AB', 'CD']),
        )
        InvenTreeSetting.set_setting('AB', 'hello', self.user)
        InvenTreeSetting.set_setting('CD', 'world', self.user)
        self.assertEqual(InvenTreeSetting.check_all_settings(), (True, []))

    @mock.patch('common.models.InvenTreeSetting.get_setting_definition')
    def test_settings_validator(self, get_setting_definition):
        """Make sure that the validator function gets called on set setting."""

        def validator(x):
            if x == 'hello':
                return x

            raise ValidationError(f'{x} is not valid')

        mock_validator = mock.Mock(side_effect=validator)

        # define partial schema
        settings_definition = {
            'AB': {  # key that's has not already been accessed
                'validator': mock_validator
            }
        }

        def mocked(key, **kwargs):
            return settings_definition.get(key, {})

        get_setting_definition.side_effect = mocked

        InvenTreeSetting.set_setting('AB', 'hello', self.user)
        mock_validator.assert_called_with('hello')

        with self.assertRaises(ValidationError):
            InvenTreeSetting.set_setting('AB', 'world', self.user)
        mock_validator.assert_called_with('world')

    def run_settings_check(self, key, setting):
        """Test that all settings are valid.

        - Ensure that a name is set and that it is translated
        - Ensure that a description is set
        - Ensure that every setting key is valid
        - Ensure that a validator is supplied
        """
        self.assertIs(type(setting), dict)

        name = setting.get('name', None)

        self.assertIsNotNone(name)
        self.assertIn('django.utils.functional.lazy', str(type(name)))

        description = setting.get('description', None)

        self.assertIsNotNone(description)
        self.assertIn('django.utils.functional.lazy', str(type(description)))

        if key != key.upper():
            raise ValueError(
                f"Setting key '{key}' is not uppercase"
            )  # pragma: no cover

        # Check that only allowed keys are provided
        allowed_keys = [
            'name',
            'description',
            'default',
            'validator',
            'hidden',
            'choices',
            'units',
            'requires_restart',
            'after_save',
            'before_save',
        ]

        for k in setting:
            self.assertIn(k, allowed_keys)

        # Check default value for boolean settings
        validator = setting.get('validator', None)

        if validator is bool:
            default = setting.get('default', None)

            # Default value *must* be supplied for boolean setting!
            self.assertIsNotNone(default)

            # Default value for boolean must itself be a boolean
            self.assertIn(default, [True, False])

    def test_setting_data(self):
        """Test for settings data.

        - Ensure that every setting has a name, which is translated
        - Ensure that every setting has a description, which is translated
        """
        for key, setting in InvenTreeSetting.SETTINGS.items():
            try:
                self.run_settings_check(key, setting)
            except Exception as exc:  # pragma: no cover
                print(f"run_settings_check failed for global setting '{key}'")
                raise exc

        for key, setting in InvenTreeUserSetting.SETTINGS.items():
            try:
                self.run_settings_check(key, setting)
            except Exception as exc:  # pragma: no cover
                print(f"run_settings_check failed for user setting '{key}'")
                raise exc

    @override_settings(SITE_URL=None, PLUGIN_TESTING=True, PLUGIN_TESTING_SETUP=True)
    def test_defaults(self):
        """Populate the settings with default values."""
        for key in InvenTreeSetting.SETTINGS:
            value = InvenTreeSetting.get_setting_default(key)

            try:
                InvenTreeSetting.set_setting(key, value, change_user=self.user)
            except Exception as exc:  # pragma: no cover
                print(f"test_defaults: Failed to set default value for setting '{key}'")
                raise exc

            self.assertEqual(value, InvenTreeSetting.get_setting(key))

            # Any fields marked as 'boolean' must have a default value specified
            setting = InvenTreeSetting.get_setting_object(key)

            if setting.is_bool():
                if setting.default_value not in [True, False]:
                    raise ValueError(
                        f'Non-boolean default value specified for {key}'
                    )  # pragma: no cover

    def test_global_setting_caching(self):
        """Test caching operations for the global settings class."""
        key = 'PART_NAME_FORMAT'

        cache_key = InvenTreeSetting.create_cache_key(key)
        self.assertEqual(cache_key, 'InvenTreeSetting:PART_NAME_FORMAT')

        cache.clear()

        self.assertIsNone(cache.get(cache_key))

        # First request should set cache
        val = InvenTreeSetting.get_setting(key)
        self.assertEqual(cache.get(cache_key).value, val)

        for val in ['A', '{{ part.IPN }}', 'C']:
            # Check that the cached value is updated whenever the setting is saved
            InvenTreeSetting.set_setting(key, val, None)
            self.assertEqual(cache.get(cache_key).value, val)
            self.assertEqual(InvenTreeSetting.get_setting(key), val)

    def test_user_setting_caching(self):
        """Test caching operation for the user settings class."""
        cache.clear()

        # Generate a number of new users
        for idx in range(5):
            get_user_model().objects.create(
                username=f'User_{idx}', password='hunter42', email='email@dot.com'
            )

        key = 'SEARCH_PREVIEW_RESULTS'

        # Check that the settings are correctly cached for each separate user
        for user in get_user_model().objects.all():
            setting = InvenTreeUserSetting.get_setting_object(key, user=user)
            cache_key = setting.cache_key
            self.assertEqual(
                cache_key,
                f'InvenTreeUserSetting:SEARCH_PREVIEW_RESULTS_user:{user.username}',
            )
            InvenTreeUserSetting.set_setting(key, user.pk, None, user=user)
            self.assertIsNotNone(cache.get(cache_key))

        # Iterate through a second time, ensure the values have been cached correctly
        for user in get_user_model().objects.all():
            value = InvenTreeUserSetting.get_setting(key, user=user)
            self.assertEqual(value, user.pk)


class GlobalSettingsApiTest(InvenTreeAPITestCase):
    """Tests for the global settings API."""

    def setUp(self):
        """Ensure cache is cleared as part of test setup."""
        cache.clear()
        return super().setUp()

    def test_global_settings_api_list(self):
        """Test list URL for global settings."""
        url = reverse('api-global-setting-list')

        # Read out each of the global settings value, to ensure they are instantiated in the database
        for key in InvenTreeSetting.SETTINGS:
            InvenTreeSetting.get_setting_object(key, cache=False)

        response = self.get(url, expected_code=200)

        n_public_settings = len([
            k for k in InvenTreeSetting.SETTINGS if not k.startswith('_')
        ])

        # Number of results should match the number of settings
        self.assertEqual(len(response.data), n_public_settings)

    def test_currency_settings(self):
        """Run tests for currency specific settings."""
        url = reverse('api-global-setting-detail', kwargs={'key': 'CURRENCY_CODES'})

        response = self.patch(url, data={'value': 'USD,XYZ'}, expected_code=400)

        self.assertIn("Invalid currency code: 'XYZ'", str(response.data))

        response = self.patch(
            url, data={'value': 'AUD,USD, AUD,AUD,'}, expected_code=400
        )

        self.assertIn("Duplicate currency code: 'AUD'", str(response.data))

        response = self.patch(url, data={'value': ',,,,,'}, expected_code=400)

        self.assertIn('No valid currency codes provided', str(response.data))

        response = self.patch(url, data={'value': 'AUD,USD,GBP'}, expected_code=200)

        codes = InvenTreeSetting.get_setting('CURRENCY_CODES')

        self.assertEqual(codes, 'AUD,USD,GBP')

    def test_company_name(self):
        """Test a settings object lifecycle e2e."""
        setting = InvenTreeSetting.get_setting_object('INVENTREE_COMPANY_NAME')

        # Check default value
        self.assertEqual(setting.value, 'My company name')

        url = reverse('api-global-setting-detail', kwargs={'key': setting.key})

        # Test getting via the API
        for val in ['test', '123', 'My company nam3']:
            setting.value = val
            setting.save()

            response = self.get(url, expected_code=200)

            self.assertEqual(response.data['value'], val)

        # Test setting via the API
        for val in ['cat', 'hat', 'bat', 'mat']:
            response = self.patch(url, {'value': val}, expected_code=200)

            self.assertEqual(response.data['value'], val)

            setting.refresh_from_db()
            self.assertEqual(setting.value, val)

    def test_api_detail(self):
        """Test that we can access the detail view for a setting based on the <key>."""
        # These keys are invalid, and should return 404
        for key in ['apple', 'carrot', 'dog']:
            response = self.get(
                reverse('api-global-setting-detail', kwargs={'key': key}),
                expected_code=404,
            )

        key = 'INVENTREE_INSTANCE'
        url = reverse('api-global-setting-detail', kwargs={'key': key})

        InvenTreeSetting.objects.filter(key=key).delete()

        # Check that we can access a setting which has not previously been created
        self.assertFalse(InvenTreeSetting.objects.filter(key=key).exists())

        # Access via the API, and the default value should be received
        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['value'], 'InvenTree')

        # Now, the object should have been created in the DB
        self.patch(url, {'value': 'My new title'}, expected_code=200)

        setting = InvenTreeSetting.objects.get(key=key)

        self.assertEqual(setting.value, 'My new title')

        # And retrieving via the API now returns the updated value
        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['value'], 'My new title')


class UserSettingsApiTest(InvenTreeAPITestCase):
    """Tests for the user settings API."""

    def test_user_settings_api_list(self):
        """Test list URL for user settings."""
        url = reverse('api-user-setting-list')

        self.get(url, expected_code=200)

    def test_user_setting_invalid(self):
        """Test a user setting with an invalid key."""
        url = reverse('api-user-setting-detail', kwargs={'key': 'DONKEY'})

        self.get(url, expected_code=404)

    def test_user_setting_init(self):
        """Test we can retrieve a setting which has not yet been initialized."""
        key = 'LABEL_INLINE'

        # Ensure it does not actually exist in the database
        self.assertFalse(InvenTreeUserSetting.objects.filter(key=key).exists())

        url = reverse('api-user-setting-detail', kwargs={'key': key})

        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['value'], 'True')

        self.patch(url, {'value': 'False'}, expected_code=200)

        setting = InvenTreeUserSetting.objects.get(key=key, user=self.user)

        self.assertEqual(setting.value, 'False')
        self.assertEqual(setting.to_native_value(), False)

    def test_user_setting_boolean(self):
        """Test a boolean user setting value."""
        # Ensure we have a boolean setting available
        setting = InvenTreeUserSetting.get_setting_object(
            'SEARCH_PREVIEW_SHOW_PARTS', user=self.user
        )

        # Check default values
        self.assertEqual(setting.to_native_value(), True)

        # Fetch via API
        url = reverse('api-user-setting-detail', kwargs={'key': setting.key})

        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['pk'], setting.pk)
        self.assertEqual(response.data['key'], 'SEARCH_PREVIEW_SHOW_PARTS')
        self.assertEqual(
            response.data['description'], 'Display parts in search preview window'
        )
        self.assertEqual(response.data['type'], 'boolean')
        self.assertEqual(len(response.data['choices']), 0)
        self.assertTrue(str2bool(response.data['value']))

        # Assign some truthy values
        for v in ['true', True, 1, 'y', 'TRUE']:
            self.patch(url, {'value': str(v)}, expected_code=200)

            response = self.get(url, expected_code=200)

            self.assertTrue(str2bool(response.data['value']))

        # Assign some false(ish) values
        for v in ['false', False, '0', 'n', 'FalSe']:
            self.patch(url, {'value': str(v)}, expected_code=200)

            response = self.get(url, expected_code=200)

            self.assertFalse(str2bool(response.data['value']))

        # Assign some invalid values
        for v in ['x', '', 'invalid', None, '-1', 'abcde']:
            response = self.patch(url, {'value': str(v)}, expected_code=200)

            # Invalid values evaluate to False
            self.assertFalse(str2bool(response.data['value']))

    def test_user_setting_choice(self):
        """Test a user setting with choices."""
        setting = InvenTreeUserSetting.get_setting_object(
            'DATE_DISPLAY_FORMAT', user=self.user
        )

        url = reverse('api-user-setting-detail', kwargs={'key': setting.key})

        # Check default value
        self.assertEqual(setting.value, 'YYYY-MM-DD')

        # Check that a valid option can be assigned via the API
        for opt in ['YYYY-MM-DD', 'DD-MM-YYYY', 'MM/DD/YYYY']:
            self.patch(url, {'value': opt}, expected_code=200)

            setting.refresh_from_db()
            self.assertEqual(setting.value, opt)

        # Send an invalid option
        for opt in ['cat', 'dog', 12345]:
            response = self.patch(url, {'value': opt}, expected_code=400)

            self.assertIn('Chosen value is not a valid option', str(response.data))

    def test_user_setting_integer(self):
        """Test a integer user setting value."""
        setting = InvenTreeUserSetting.get_setting_object(
            'SEARCH_PREVIEW_RESULTS', user=self.user, cache=False
        )

        url = reverse('api-user-setting-detail', kwargs={'key': setting.key})

        # Check default value for this setting
        self.assertEqual(setting.value, 10)

        for v in [1, 9, 99]:
            setting.value = v
            setting.save()

            response = self.get(url)

            self.assertEqual(response.data['value'], str(v))

        # Set valid options via the api
        for v in [5, 15, 25]:
            self.patch(url, {'value': v}, expected_code=200)

            setting.refresh_from_db()
            self.assertEqual(setting.to_native_value(), v)

        # Set invalid options via the API
        # Note that this particular setting has a MinValueValidator(1) associated with it
        for v in [0, -1, -5]:
            response = self.patch(url, {'value': v}, expected_code=400)


class NotificationUserSettingsApiTest(InvenTreeAPITestCase):
    """Tests for the notification user settings API."""

    def test_api_list(self):
        """Test list URL."""
        url = reverse('api-notification-setting-list')

        self.get(url, expected_code=200)

    def test_setting(self):
        """Test the string name for NotificationUserSetting."""
        NotificationUserSetting.set_setting(
            'NOTIFICATION_METHOD_MAIL', True, change_user=self.user, user=self.user
        )
        test_setting = NotificationUserSetting.get_setting_object(
            'NOTIFICATION_METHOD_MAIL', user=self.user
        )
        self.assertEqual(
            str(test_setting), 'NOTIFICATION_METHOD_MAIL (for testuser): True'
        )


class PluginSettingsApiTest(PluginMixin, InvenTreeAPITestCase):
    """Tests for the plugin settings API."""

    def test_plugin_list(self):
        """List installed plugins via API."""
        url = reverse('api-plugin-list')

        # Simple request
        self.get(url, expected_code=200)

        # Request with filter
        self.get(url, expected_code=200, data={'mixin': 'settings'})

    def test_api_list(self):
        """Test list URL."""
        url = reverse('api-plugin-setting-list')

        self.get(url, expected_code=200)

    def test_valid_plugin_slug(self):
        """Test that an valid plugin slug runs through."""
        # Activate plugin
        registry.set_plugin_state('sample', True)

        # get data
        url = reverse(
            'api-plugin-setting-detail', kwargs={'plugin': 'sample', 'key': 'API_KEY'}
        )
        response = self.get(url, expected_code=200)

        # check the right setting came through
        self.assertTrue(response.data['key'], 'API_KEY')
        self.assertTrue(response.data['plugin'], 'sample')
        self.assertTrue(response.data['type'], 'string')
        self.assertTrue(
            response.data['description'], 'Key required for accessing external API'
        )

        # Failure mode tests

        # Non-existent plugin
        url = reverse(
            'api-plugin-setting-detail',
            kwargs={'plugin': 'doesnotexist', 'key': 'doesnotmatter'},
        )
        response = self.get(url, expected_code=404)
        self.assertIn("Plugin 'doesnotexist' not installed", str(response.data))

        # Wrong key
        url = reverse(
            'api-plugin-setting-detail',
            kwargs={'plugin': 'sample', 'key': 'doesnotexist'},
        )
        response = self.get(url, expected_code=404)
        self.assertIn(
            "Plugin 'sample' has no setting matching 'doesnotexist'", str(response.data)
        )

    def test_invalid_setting_key(self):
        """Test that an invalid setting key returns a 404."""

    def test_uninitialized_setting(self):
        """Test that requesting an uninitialized setting creates the setting."""


class ErrorReportTest(InvenTreeAPITestCase):
    """Unit tests for the error report API."""

    def test_error_list(self):
        """Test error list."""
        from InvenTree.exceptions import log_error

        url = reverse('api-error-list')
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 0)

        # Throw an error!
        log_error(
            'test error', error_name='My custom error', error_info={'test': 'data'}
        )

        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 1)

        err = response.data[0]
        for k in ['when', 'info', 'data', 'path']:
            self.assertIn(k, err)


class TaskListApiTests(InvenTreeAPITestCase):
    """Unit tests for the background task API endpoints."""

    def test_pending_tasks(self):
        """Test that the pending tasks endpoint is available."""
        # Schedule some tasks
        from django_q.models import OrmQ

        from InvenTree.tasks import offload_task

        n = OrmQ.objects.count()

        for i in range(3):
            offload_task(f'fake_module.test_{i}', force_async=True)

        self.assertEqual(OrmQ.objects.count(), 3)

        url = reverse('api-pending-task-list')
        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), n + 3)

        for task in response.data:
            self.assertTrue(task['func'].startswith('fake_module.test_'))

    def test_scheduled_tasks(self):
        """Test that the scheduled tasks endpoint is available."""
        from django_q.models import Schedule

        for i in range(5):
            Schedule.objects.create(
                name='time.sleep', func='time.sleep', args=f'{i + 1}'
            )

        n = Schedule.objects.count()
        self.assertGreater(n, 0)

        url = reverse('api-scheduled-task-list')
        response = self.get(url, expected_code=200)

        for task in response.data:
            self.assertEqual(task['name'], 'time.sleep')


class WebhookMessageTests(TestCase):
    """Tests for webhooks."""

    def setUp(self):
        """Setup for all tests."""
        self.endpoint_def = WebhookEndpoint.objects.create()
        self.url = f'/api/webhook/{self.endpoint_def.endpoint_id}/'
        self.client = Client(enforce_csrf_checks=True)

    def test_bad_method(self):
        """Test that a wrong HTTP method does not work."""
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_missing_token(self):
        """Tests that token checks work."""
        response = self.client.post(self.url, content_type=CONTENT_TYPE_JSON)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (
            json.loads(response.content)['detail']
            == WebhookView.model_class.MESSAGE_TOKEN_ERROR
        )

    def test_bad_token(self):
        """Test that a wrong token is not working."""
        response = self.client.post(
            self.url, content_type=CONTENT_TYPE_JSON, HTTP_TOKEN='1234567fghj'
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (
            json.loads(response.content)['detail']
            == WebhookView.model_class.MESSAGE_TOKEN_ERROR
        )

    def test_bad_url(self):
        """Test that a wrongly formed url is not working."""
        response = self.client.post(
            '/api/webhook/1234/', content_type=CONTENT_TYPE_JSON
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_bad_json(self):
        """Test that malformed JSON is not accepted."""
        response = self.client.post(
            self.url,
            data="{'this': 123}",
            content_type=CONTENT_TYPE_JSON,
            HTTP_TOKEN=str(self.endpoint_def.token),
        )

        assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
        assert (
            json.loads(response.content)['detail']
            == 'Expecting property name enclosed in double quotes'
        )

    def test_success_no_token_check(self):
        """Test that a endpoint without a token set does not require one."""
        # delete token
        self.endpoint_def.token = ''
        self.endpoint_def.save()

        # check
        response = self.client.post(self.url, content_type=CONTENT_TYPE_JSON)

        assert response.status_code == HTTPStatus.OK
        assert str(response.content, 'utf-8') == WebhookView.model_class.MESSAGE_OK

    def test_bad_hmac(self):
        """Test that a malformed HMAC does not pass."""
        # delete token
        self.endpoint_def.token = ''
        self.endpoint_def.secret = '123abc'
        self.endpoint_def.save()

        # check
        response = self.client.post(self.url, content_type=CONTENT_TYPE_JSON)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (
            json.loads(response.content)['detail']
            == WebhookView.model_class.MESSAGE_TOKEN_ERROR
        )

    def test_success_hmac(self):
        """Test with a valid HMAC provided."""
        # delete token
        self.endpoint_def.token = ''
        self.endpoint_def.secret = '123abc'
        self.endpoint_def.save()

        # check
        response = self.client.post(
            self.url,
            content_type=CONTENT_TYPE_JSON,
            HTTP_TOKEN='68MXtc/OiXdA5e2Nq9hATEVrZFpLb3Zb0oau7n8s31I=',
        )

        assert response.status_code == HTTPStatus.OK
        assert str(response.content, 'utf-8') == WebhookView.model_class.MESSAGE_OK

    def test_success(self):
        """Test full e2e webhook call.

        The message should go through and save the json payload.
        """
        response = self.client.post(
            self.url,
            data={'this': 'is a message'},
            content_type=CONTENT_TYPE_JSON,
            HTTP_TOKEN=str(self.endpoint_def.token),
        )

        assert response.status_code == HTTPStatus.OK
        assert str(response.content, 'utf-8') == WebhookView.model_class.MESSAGE_OK
        message = WebhookMessage.objects.get()
        assert message.body == {'this': 'is a message'}


class NotificationTest(InvenTreeAPITestCase):
    """Tests for NotificationEntry."""

    fixtures = ['users']

    def test_check_notification_entries(self):
        """Test that notification entries can be created."""
        # Create some notification entries

        self.assertEqual(NotificationEntry.objects.count(), 0)

        NotificationEntry.notify('test.notification', 1)

        self.assertEqual(NotificationEntry.objects.count(), 1)

        delta = timedelta(days=1)

        self.assertFalse(NotificationEntry.check_recent('test.notification', 2, delta))
        self.assertFalse(NotificationEntry.check_recent('test.notification2', 1, delta))

        self.assertTrue(NotificationEntry.check_recent('test.notification', 1, delta))

    def test_api_list(self):
        """Test list URL."""
        url = reverse('api-notifications-list')

        self.get(url, expected_code=200)

        # Test the OPTIONS endpoint for the 'api-notification-list'
        # Ref: https://github.com/inventree/InvenTree/pull/3154
        response = self.options(url)

        self.assertIn('DELETE', response.data['actions'])
        self.assertIn('GET', response.data['actions'])
        self.assertNotIn('POST', response.data['actions'])

        self.assertEqual(
            response.data['description'],
            'List view for all notifications of the current user.',
        )

        # POST action should fail (not allowed)
        response = self.post(url, {}, expected_code=405)

    def test_bulk_delete(self):
        """Tests for bulk deletion of user notifications."""
        from error_report.models import Error

        # Create some notification messages by throwing errors
        for _ii in range(10):
            Error.objects.create()

        # Check that messages have been created
        messages = NotificationMessage.objects.all()

        # As there are three staff users (including the 'test' user) we expect 30 notifications
        # However, one user is marked as inactive
        self.assertEqual(messages.count(), 20)

        # Only 10 messages related to *this* user
        my_notifications = messages.filter(user=self.user)
        self.assertEqual(my_notifications.count(), 10)

        # Get notification via the API
        url = reverse('api-notifications-list')
        response = self.get(url, {}, expected_code=200)
        self.assertEqual(len(response.data), 10)

        # Mark some as read
        for ntf in my_notifications[0:3]:
            ntf.read = True
            ntf.save()

        # Read out via API again
        response = self.get(url, {'read': True}, expected_code=200)

        # Check validity of returned data
        self.assertEqual(len(response.data), 3)
        for ntf in response.data:
            self.assertTrue(ntf['read'])

        # Now, let's bulk delete all 'unread' notifications via the API,
        # but only associated with the logged in user
        response = self.delete(url, {'filters': {'read': False}}, expected_code=204)

        # Only 7 notifications should have been deleted,
        # as the notifications associated with other users must remain untouched
        self.assertEqual(NotificationMessage.objects.count(), 13)
        self.assertEqual(NotificationMessage.objects.filter(user=self.user).count(), 3)


class CommonTest(InvenTreeAPITestCase):
    """Tests for the common config."""

    def test_restart_flag(self):
        """Test that the restart flag is reset on start."""
        from plugin import registry

        # set flag true
        set_global_setting('SERVER_RESTART_REQUIRED', True, None)

        # reload the app
        registry.reload_plugins()

        # now it should be false again
        self.assertFalse(get_global_setting('SERVER_RESTART_REQUIRED'))

    def test_config_api(self):
        """Test config URLs."""
        # Not superuser
        self.get(reverse('api-config-list'), expected_code=403)

        # Turn into superuser
        self.user.is_superuser = True
        self.user.save()

        # Successful checks
        data = [
            self.get(reverse('api-config-list'), expected_code=200).data[
                0
            ],  # list endpoint
            self.get(
                reverse('api-config-detail', kwargs={'key': 'INVENTREE_DEBUG'}),
                expected_code=200,
            ).data,  # detail endpoint
        ]

        for item in data:
            self.assertEqual(item['key'], 'INVENTREE_DEBUG')
            self.assertEqual(item['env_var'], 'INVENTREE_DEBUG')
            self.assertEqual(item['config_key'], 'debug')

        # Turn into normal user again
        self.user.is_superuser = False
        self.user.save()

    def test_flag_api(self):
        """Test flag URLs."""
        # Not superuser
        response = self.get(reverse('api-flag-list'), expected_code=200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['key'], 'EXPERIMENTAL')

        # Turn into superuser
        self.user.is_superuser = True
        self.user.save()

        # Successful checks
        response = self.get(reverse('api-flag-list'), expected_code=200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['key'], 'EXPERIMENTAL')
        self.assertTrue(response.data[0]['conditions'])

        response = self.get(
            reverse('api-flag-detail', kwargs={'key': 'EXPERIMENTAL'}),
            expected_code=200,
        )
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data['key'], 'EXPERIMENTAL')
        self.assertTrue(response.data['conditions'])

        # Try without param -> false
        response = self.get(
            reverse('api-flag-detail', kwargs={'key': 'NEXT_GEN'}), expected_code=200
        )
        self.assertFalse(response.data['state'])

        # Try with param -> true
        response = self.get(
            reverse('api-flag-detail', kwargs={'key': 'NEXT_GEN'}),
            {'ngen': ''},
            expected_code=200,
        )
        self.assertTrue(response.data['state'])

        # Try non existent flag
        response = self.get(
            reverse('api-flag-detail', kwargs={'key': 'NON_EXISTENT'}),
            expected_code=404,
        )

        # Turn into normal user again
        self.user.is_superuser = False
        self.user.save()


class CurrencyAPITests(InvenTreeAPITestCase):
    """Unit tests for the currency exchange API endpoints."""

    def test_exchange_endpoint(self):
        """Test that the currency exchange endpoint works as expected."""
        response = self.get(reverse('api-currency-exchange'), expected_code=200)

        self.assertIn('base_currency', response.data)
        self.assertIn('exchange_rates', response.data)

    def test_refresh_endpoint(self):
        """Call the 'refresh currencies' endpoint."""
        from djmoney.contrib.exchange.models import Rate

        # Delete any existing exchange rate data
        Rate.objects.all().delete()

        # Updating via the external exchange may not work every time
        for _idx in range(5):
            self.post(
                reverse('api-currency-refresh'), expected_code=200, max_query_time=30
            )

            # There should be some new exchange rate objects now
            if Rate.objects.all().exists():
                # Exit early
                return

            # Delay and try again - might have problems with exchange rate endpoint
            time.sleep(10)  # pragma: no cover

        raise TimeoutError(
            'Could not refresh currency exchange data after 5 attempts'
        )  # pragma: no cover


class NotesImageTest(InvenTreeAPITestCase):
    """Tests for uploading images to be used in markdown notes."""

    def test_invalid_files(self):
        """Test that invalid files are rejected."""
        n = NotesImage.objects.count()

        # Test upload of a simple text file
        response = self.post(
            reverse('api-notes-image-list'),
            data={
                'image': SimpleUploadedFile(
                    'test.txt', b'this is not an image file', content_type='text/plain'
                )
            },
            format='multipart',
            expected_code=400,
        )

        self.assertIn('Upload a valid image', str(response.data['image']))

        # Test upload of an invalid image file
        response = self.post(
            reverse('api-notes-image-list'),
            data={
                'image': SimpleUploadedFile(
                    'test.png', b'this is not an image file', content_type='image/png'
                )
            },
            format='multipart',
            expected_code=400,
        )

        self.assertIn('Upload a valid image', str(response.data['image']))

        # Check that no extra database entries have been created
        self.assertEqual(NotesImage.objects.count(), n)

    def test_valid_image(self):
        """Test upload of a valid image file."""
        n = NotesImage.objects.count()

        # Construct a simple image file
        image = PIL.Image.new('RGB', (100, 100), color='red')

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            contents = output.getvalue()

        self.post(
            reverse('api-notes-image-list'),
            data={
                'image': SimpleUploadedFile(
                    'test.png', contents, content_type='image/png'
                )
            },
            format='multipart',
            expected_code=201,
        )

        # Check that a new file has been created
        self.assertEqual(NotesImage.objects.count(), n + 1)


class ProjectCodesTest(InvenTreeAPITestCase):
    """Units tests for the ProjectCodes model and API endpoints."""

    @property
    def url(self):
        """Return the URL for the project code list endpoint."""
        return reverse('api-project-code-list')

    @classmethod
    def setUpTestData(cls):
        """Create some initial project codes."""
        super().setUpTestData()

        codes = [
            ProjectCode(code='PRJ-001', description='Test project code'),
            ProjectCode(code='PRJ-002', description='Test project code'),
            ProjectCode(code='PRJ-003', description='Test project code'),
            ProjectCode(code='PRJ-004', description='Test project code'),
        ]

        ProjectCode.objects.bulk_create(codes)

    def test_list(self):
        """Test that the list endpoint works as expected."""
        response = self.get(self.url, expected_code=200)
        self.assertEqual(len(response.data), ProjectCode.objects.count())

    def test_delete(self):
        """Test we can delete a project code via the API."""
        n = ProjectCode.objects.count()

        # Get the first project code
        code = ProjectCode.objects.first()

        # Delete it
        self.delete(
            reverse('api-project-code-detail', kwargs={'pk': code.pk}),
            expected_code=204,
        )

        # Check it is gone
        self.assertEqual(ProjectCode.objects.count(), n - 1)

    def test_duplicate_code(self):
        """Test that we cannot create two project codes with the same code."""
        # Create a new project code
        response = self.post(
            self.url,
            data={'code': 'PRJ-001', 'description': 'Test project code'},
            expected_code=400,
        )

        self.assertIn(
            'Project Code with this Project Code already exists',
            str(response.data['code']),
        )

    def test_write_access(self):
        """Test that non-staff users have read-only access."""
        # By default user has staff access, can create a new project code
        response = self.post(
            self.url,
            data={'code': 'PRJ-xxx', 'description': 'Test project code'},
            expected_code=201,
        )

        pk = response.data['pk']

        # Test we can edit, also
        response = self.patch(
            reverse('api-project-code-detail', kwargs={'pk': pk}),
            data={'code': 'PRJ-999'},
            expected_code=200,
        )

        self.assertEqual(response.data['code'], 'PRJ-999')

        # Restrict user access to non-staff
        self.user.is_staff = False
        self.user.save()

        # As user does not have staff access, should return 403 for list endpoint
        response = self.post(
            self.url,
            data={'code': 'PRJ-123', 'description': 'Test project code'},
            expected_code=403,
        )

        # Should also return 403 for detail endpoint
        response = self.patch(
            reverse('api-project-code-detail', kwargs={'pk': pk}),
            data={'code': 'PRJ-999'},
            expected_code=403,
        )


class CustomUnitAPITest(InvenTreeAPITestCase):
    """Unit tests for the CustomUnit API."""

    @property
    def url(self):
        """Return the API endpoint for the CustomUnit list."""
        return reverse('api-custom-unit-list')

    @classmethod
    def setUpTestData(cls):
        """Construct some initial test fixture data."""
        super().setUpTestData()

        units = [
            CustomUnit(
                name='metres_per_amp', definition='meter / ampere', symbol='m/A'
            ),
            CustomUnit(
                name='hectares_per_second',
                definition='hectares per second',
                symbol='ha/s',
            ),
        ]

        CustomUnit.objects.bulk_create(units)

    def test_list(self):
        """Test API list functionality."""
        response = self.get(self.url, expected_code=200)
        self.assertEqual(len(response.data), CustomUnit.objects.count())

    def test_edit(self):
        """Test edit permissions for CustomUnit model."""
        unit = CustomUnit.objects.first()

        # Try to edit without permission
        self.user.is_staff = False
        self.user.save()

        self.patch(
            reverse('api-custom-unit-detail', kwargs={'pk': unit.pk}),
            {'name': 'new_unit_name'},
            expected_code=403,
        )

        # Ok, what if we have permission?
        self.user.is_staff = True
        self.user.save()

        self.patch(
            reverse('api-custom-unit-detail', kwargs={'pk': unit.pk}),
            {'name': 'new_unit_name'},
            # expected_code=200
        )

        unit.refresh_from_db()
        self.assertEqual(unit.name, 'new_unit_name')

    def test_validation(self):
        """Test that validation works as expected."""
        unit = CustomUnit.objects.first()

        self.user.is_staff = True
        self.user.save()

        # Test invalid 'name' values (must be valid identifier)
        invalid_name_values = ['1', '1abc', 'abc def', 'abc-def', 'abc.def']

        url = reverse('api-custom-unit-detail', kwargs={'pk': unit.pk})

        for name in invalid_name_values:
            self.patch(url, {'name': name}, expected_code=400)

    def test_api(self):
        """Test the CustomUnit API."""
        response = self.get(reverse('api-all-unit-list'))
        self.assertIn('default_system', response.data)
        self.assertIn('available_systems', response.data)
        self.assertIn('available_units', response.data)
        self.assertEqual(len(response.data['available_units']) > 100, True)


class ContentTypeAPITest(InvenTreeAPITestCase):
    """Unit tests for the ContentType API."""

    def test_list(self):
        """Test API list functionality."""
        response = self.get(reverse('api-contenttype-list'), expected_code=200)
        self.assertEqual(len(response.data), ContentType.objects.count())

    def test_detail(self):
        """Test API detail functionality."""
        ct = ContentType.objects.first()
        assert ct

        response = self.get(
            reverse('api-contenttype-detail', kwargs={'pk': ct.pk}), expected_code=200
        )

        self.assertEqual(response.data['app_label'], ct.app_label)
        self.assertEqual(response.data['model'], ct.model)

        # Test with model name
        response = self.get(
            reverse('api-contenttype-detail-modelname', kwargs={'model': ct.model}),
            expected_code=200,
        )
        self.assertEqual(response.data['app_label'], ct.app_label)
        self.assertEqual(response.data['model'], ct.model)

        # Test non-existent model
        self.get(
            reverse(
                'api-contenttype-detail-modelname', kwargs={'model': 'nonexistent'}
            ),
            expected_code=404,
        )

        # PK should not work on model name endpoint
        self.get(
            reverse('api-contenttype-detail-modelname', kwargs={'model': None}),
            expected_code=404,
        )


class IconAPITest(InvenTreeAPITestCase):
    """Unit tests for the Icons API."""

    def test_list(self):
        """Test API list functionality."""
        response = self.get(reverse('api-icon-list'), expected_code=200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(response.data[0]['prefix'], 'ti')
        self.assertEqual(response.data[0]['name'], 'Tabler Icons')
        for font_format in ['woff2', 'woff', 'truetype']:
            self.assertIn(font_format, response.data[0]['fonts'])

        self.assertGreater(len(response.data[0]['icons']), 1000)


class ValidatorsTest(TestCase):
    """Unit tests for the custom validators."""

    def test_validate_icon(self):
        """Test the validate_icon function."""
        common.validators.validate_icon('')
        common.validators.validate_icon(None)

        with self.assertRaises(ValidationError):
            common.validators.validate_icon('invalid')

        with self.assertRaises(ValidationError):
            common.validators.validate_icon('my:package:non-existing')

        with self.assertRaises(ValidationError):
            common.validators.validate_icon(
                'ti:my-non-existing-icon:non-existing-variant'
            )

        with self.assertRaises(ValidationError):
            common.validators.validate_icon('ti:package:non-existing-variant')

        common.validators.validate_icon('ti:package:outline')


class CustomStatusTest(TestCase):
    """Unit tests for the custom status model."""

    def setUp(self):
        """Setup for all tests."""
        self.data = {
            'key': 11,
            'name': 'OK - advanced',
            'label': 'OK - adv.',
            'color': 'secondary',
            'logical_key': 10,
            'model': ContentType.objects.get(model='stockitem'),
            'reference_status': 'StockStatus',
        }

    def test_validation_model(self):
        """Test that model is present."""
        data = self.data
        data.pop('model')
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation_key(self):
        """Tests Model must have a key."""
        data = self.data
        data.pop('key')
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation_logicalkey(self):
        """Tests Logical key must be present."""
        data = self.data
        data.pop('logical_key')
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation_reference(self):
        """Tests Reference status must be present."""
        data = self.data
        data.pop('reference_status')
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation_logical_unique(self):
        """Tests Logical key must be unique."""
        data = self.data
        data['logical_key'] = data['key']
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation_reference_exsists(self):
        """Tests Reference status set not found."""
        data = self.data
        data['reference_status'] = 'abcd'
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation_key_unique(self):
        """Tests Key must be different from the logical keys of the reference."""
        data = self.data
        data['key'] = 50
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation_logical_key_exsists(self):
        """Tests Logical key must be in the logical keys of the reference status."""
        data = self.data
        data['logical_key'] = 12
        with self.assertRaises(ValidationError):
            InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 0)

    def test_validation(self):
        """Tests Valid run."""
        data = self.data
        instance = InvenTreeCustomUserStateModel.objects.create(**data)
        self.assertEqual(data['key'], instance.key)
        self.assertEqual(InvenTreeCustomUserStateModel.objects.count(), 1)
        self.assertEqual(
            instance.__str__(), 'Stock Item (StockStatus): OK - advanced | 11 (10)'
        )


class SelectionListTest(InvenTreeAPITestCase):
    """Tests for the SelectionList and SelectionListEntry model and API endpoints."""

    fixtures = ['category', 'part', 'location', 'params', 'test_templates']

    def setUp(self):
        """Setup for all tests."""
        super().setUp()

        self.list = SelectionList.objects.create(name='Test List')
        self.entry1 = SelectionListEntry.objects.create(
            list=self.list,
            value='test1',
            label='Test Entry',
            description='Test Description',
        )
        self.entry2 = SelectionListEntry.objects.create(
            list=self.list,
            value='test2',
            label='Test Entry 2',
            description='Test Description 2',
            active=False,
        )
        self.list2 = SelectionList.objects.create(name='Test List 2', active=False)

        # Urls
        self.list_url = reverse('api-selectionlist-detail', kwargs={'pk': self.list.pk})
        self.entry_url = reverse(
            'api-selectionlistentry-detail',
            kwargs={'entrypk': self.entry1.pk, 'pk': self.list.pk},
        )

    def test_api(self):
        """Test the SelectionList and SelctionListEntry API endpoints."""
        url = reverse('api-selectionlist-list')
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 2)

        response = self.get(self.list_url, expected_code=200)
        self.assertEqual(response.data['name'], 'Test List')
        self.assertEqual(len(response.data['choices']), 2)
        self.assertEqual(response.data['choices'][0]['value'], 'test1')
        self.assertEqual(response.data['choices'][0]['label'], 'Test Entry')

        response = self.get(self.entry_url, expected_code=200)
        self.assertEqual(response.data['value'], 'test1')
        self.assertEqual(response.data['label'], 'Test Entry')
        self.assertEqual(response.data['description'], 'Test Description')

    def test_api_update(self):
        """Test adding and editing via the SelectionList."""
        # Test adding a new list via the API
        response = self.post(
            reverse('api-selectionlist-list'),
            {
                'name': 'New List',
                'active': True,
                'choices': [{'value': '1', 'label': 'Test Entry'}],
            },
            expected_code=201,
        )
        list_pk = response.data['pk']
        self.assertEqual(response.data['name'], 'New List')
        self.assertTrue(response.data['active'])
        self.assertEqual(len(response.data['choices']), 1)
        self.assertEqual(response.data['choices'][0]['value'], '1')

        # Test editing the list choices via the API (remove and add in same call)
        response = self.patch(
            reverse('api-selectionlist-detail', kwargs={'pk': list_pk}),
            {'choices': [{'value': '2', 'label': 'New Label'}]},
            expected_code=200,
        )
        self.assertEqual(response.data['name'], 'New List')
        self.assertTrue(response.data['active'])
        self.assertEqual(len(response.data['choices']), 1)
        self.assertEqual(response.data['choices'][0]['value'], '2')
        self.assertEqual(response.data['choices'][0]['label'], 'New Label')
        entry_id = response.data['choices'][0]['id']

        # Test changing an entry via list API
        response = self.patch(
            reverse('api-selectionlist-detail', kwargs={'pk': list_pk}),
            {'choices': [{'id': entry_id, 'value': '2', 'label': 'New Label Text'}]},
            expected_code=200,
        )
        self.assertEqual(response.data['name'], 'New List')
        self.assertTrue(response.data['active'])
        self.assertEqual(len(response.data['choices']), 1)
        self.assertEqual(response.data['choices'][0]['value'], '2')
        self.assertEqual(response.data['choices'][0]['label'], 'New Label Text')

    def test_api_locked(self):
        """Test editing with locked/unlocked list."""
        # Lock list
        self.list.locked = True
        self.list.save()
        response = self.patch(self.entry_url, {'label': 'New Label'}, expected_code=400)
        self.assertIn('Selection list is locked', response.data['list'])
        response = self.patch(self.list_url, {'name': 'New Name'}, expected_code=400)
        self.assertIn('Selection list is locked', response.data['locked'])

        # Unlock the list
        self.list.locked = False
        self.list.save()
        response = self.patch(self.entry_url, {'label': 'New Label'}, expected_code=200)
        self.assertEqual(response.data['label'], 'New Label')
        response = self.patch(self.list_url, {'name': 'New Name'}, expected_code=200)
        self.assertEqual(response.data['name'], 'New Name')

    def test_model_meta(self):
        """Test model meta functions."""
        # Models str
        self.assertEqual(str(self.list), 'Test List')
        self.assertEqual(str(self.list2), 'Test List 2 (Inactive)')
        self.assertEqual(str(self.entry1), 'Test Entry')
        self.assertEqual(str(self.entry2), 'Test Entry 2 (Inactive)')

        # API urls
        self.assertEqual(self.list.get_api_url(), '/api/selection/')

    def test_parameter(self):
        """Test the SelectionList parameter."""
        self.assertEqual(self.list.get_choices(), ['test1'])
        self.user.is_superuser = True
        self.user.save()

        # Add to parameter
        part = Part.objects.get(pk=1)
        template = PartParameterTemplate.objects.create(
            name='test_parameter', units='', selectionlist=self.list
        )
        rsp = self.get(
            reverse('api-part-parameter-template-detail', kwargs={'pk': template.pk})
        )
        self.assertEqual(rsp.data['name'], 'test_parameter')
        self.assertEqual(rsp.data['choices'], '')

        # Add to part
        url = reverse('api-part-parameter-list')
        response = self.post(
            url,
            {'part': part.pk, 'template': template.pk, 'data': 70},
            expected_code=400,
        )
        self.assertIn('Invalid choice for parameter value', response.data['data'])

        response = self.post(
            url,
            {'part': part.pk, 'template': template.pk, 'data': self.entry1.value},
            expected_code=201,
        )
        self.assertEqual(response.data['data'], self.entry1.value)


class AdminTest(AdminTestCase):
    """Tests for the admin interface integration."""

    def test_admin(self):
        """Test the admin URL."""
        self.helper(
            model=Attachment,
            model_kwargs={'link': 'https://aa.example.org', 'model_id': 1},
        )
