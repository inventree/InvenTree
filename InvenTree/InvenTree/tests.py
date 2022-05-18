import json
import os

from unittest import mock

from django.test import TestCase, override_settings
import django.core.exceptions as django_exceptions
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings

from djmoney.money import Money
from djmoney.contrib.exchange.models import Rate, convert_money
from djmoney.contrib.exchange.exceptions import MissingRate

from .validators import validate_overage, validate_part_name
from . import helpers
from . import version
from . import status
from . import ready
from . import config

from decimal import Decimal

import InvenTree.tasks

from stock.models import StockLocation
from common.settings import currency_codes
from common.models import InvenTreeSetting


class ValidatorTest(TestCase):

    """ Simple tests for custom field validators """

    def test_part_name(self):
        """ Test part name validator """

        validate_part_name('hello world')

        with self.assertRaises(django_exceptions.ValidationError):
            validate_part_name('This | name is not } valid')

    def test_overage(self):
        """ Test overage validator """

        validate_overage("100%")
        validate_overage("10")
        validate_overage("45.2 %")

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage("-1")

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage("-2.04 %")

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage("105%")

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage("xxx %")

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage("aaaa")


class TestHelpers(TestCase):
    """ Tests for InvenTree helper functions """

    def test_image_url(self):
        """ Test if a filename looks like an image """

        for name in ['ape.png', 'bat.GiF', 'apple.WeBP', 'BiTMap.Bmp']:
            self.assertTrue(helpers.TestIfImageURL(name))

        for name in ['no.doc', 'nah.pdf', 'whatpng']:
            self.assertFalse(helpers.TestIfImageURL(name))

    def test_str2bool(self):
        """ Test string to boolean conversion """

        for s in ['yes', 'Y', 'ok', '1', 'OK', 'Ok', 'tRuE', 'oN']:
            self.assertTrue(helpers.str2bool(s))
            self.assertFalse(helpers.str2bool(s, test=False))

        for s in ['nO', '0', 'none', 'noNE', None, False, 'falSe', 'off']:
            self.assertFalse(helpers.str2bool(s))
            self.assertTrue(helpers.str2bool(s, test=False))

        for s in ['wombat', '', 'xxxx']:
            self.assertFalse(helpers.str2bool(s))
            self.assertFalse(helpers.str2bool(s, test=False))

    def test_isnull(self):

        for s in ['null', 'none', '', '-1', 'false']:
            self.assertTrue(helpers.isNull(s))

        for s in ['yes', 'frog', 'llama', 'true']:
            self.assertFalse(helpers.isNull(s))

    def testStaticUrl(self):

        self.assertEqual(helpers.getStaticUrl('test.jpg'), '/static/test.jpg')
        self.assertEqual(helpers.getBlankImage(), '/static/img/blank_image.png')
        self.assertEqual(helpers.getBlankThumbnail(), '/static/img/blank_image.thumbnail.png')

    def testMediaUrl(self):

        self.assertEqual(helpers.getMediaUrl('xx/yy.png'), '/media/xx/yy.png')

    def testDecimal2String(self):

        self.assertEqual(helpers.decimal2string(Decimal('1.2345000')), '1.2345')
        self.assertEqual(helpers.decimal2string('test'), 'test')


class TestQuoteWrap(TestCase):
    """ Tests for string wrapping """

    def test_single(self):

        self.assertEqual(helpers.WrapWithQuotes('hello'), '"hello"')
        self.assertEqual(helpers.WrapWithQuotes('hello"'), '"hello"')


class TestIncrement(TestCase):

    def tests(self):
        """ Test 'intelligent' incrementing function """

        tests = [
            ("", ""),
            (1, "2"),
            ("001", "002"),
            ("1001", "1002"),
            ("ABC123", "ABC124"),
            ("XYZ0", "XYZ1"),
            ("123Q", "123Q"),
            ("QQQ", "QQQ"),
        ]

        for test in tests:
            a, b = test

            result = helpers.increment(a)
            self.assertEqual(result, b)


class TestMakeBarcode(TestCase):
    """ Tests for barcode string creation """

    def test_barcode_extended(self):

        bc = helpers.MakeBarcode(
            "part",
            3,
            {
                "id": 3,
                "url": "www.google.com",
            },
            brief=False
        )

        self.assertIn('part', bc)
        self.assertIn('tool', bc)
        self.assertIn('"tool": "InvenTree"', bc)

        data = json.loads(bc)

        self.assertEqual(data['part']['id'], 3)
        self.assertEqual(data['part']['url'], 'www.google.com')

    def test_barcode_brief(self):

        bc = helpers.MakeBarcode(
            "stockitem",
            7,
        )

        data = json.loads(bc)
        self.assertEqual(len(data), 1)
        self.assertEqual(data['stockitem'], 7)


class TestDownloadFile(TestCase):

    def test_download(self):
        helpers.DownloadFile("hello world", "out.txt")
        helpers.DownloadFile(bytes(b"hello world"), "out.bin")


class TestMPTT(TestCase):
    """ Tests for the MPTT tree models """

    fixtures = [
        'location',
    ]

    def setUp(self):
        super().setUp()

        StockLocation.objects.rebuild()

    def test_self_as_parent(self):
        """ Test that we cannot set self as parent """

        loc = StockLocation.objects.get(pk=4)
        loc.parent = loc

        with self.assertRaises(ValidationError):
            loc.save()

    def test_child_as_parent(self):
        """ Test that we cannot set a child as parent """

        parent = StockLocation.objects.get(pk=4)
        child = StockLocation.objects.get(pk=5)

        parent.parent = child

        with self.assertRaises(ValidationError):
            parent.save()

    def test_move(self):
        """ Move an item to a different tree """

        drawer = StockLocation.objects.get(name='Drawer_1')

        # Record the tree ID
        tree = drawer.tree_id

        home = StockLocation.objects.get(name='Home')

        drawer.parent = home
        drawer.save()

        self.assertNotEqual(tree, drawer.tree_id)


class TestSerialNumberExtraction(TestCase):
    """ Tests for serial number extraction code """

    def test_simple(self):

        e = helpers.extract_serial_numbers

        sn = e("1-5", 5, 1)
        self.assertEqual(len(sn), 5, 1)
        for i in range(1, 6):
            self.assertIn(i, sn)

        sn = e("1, 2, 3, 4, 5", 5, 1)
        self.assertEqual(len(sn), 5)

        # Test partially specifying serials
        sn = e("1, 2, 4+", 5, 1)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, [1, 2, 4, 5, 6])

        # Test groups are not interpolated if enough serials are supplied
        sn = e("1, 2, 3, AF5-69H, 5", 5, 1)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, [1, 2, 3, "AF5-69H", 5])

        # Test groups are not interpolated with more than one hyphen in a word
        sn = e("1, 2, TG-4SR-92, 4+", 5, 1)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, [1, 2, "TG-4SR-92", 4, 5])

        # Test groups are not interpolated with alpha characters
        sn = e("1, A-2, 3+", 5, 1)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, [1, "A-2", 3, 4, 5])

        # Test multiple placeholders
        sn = e("1 2 ~ ~ ~", 5, 3)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, [1, 2, 3, 4, 5])

        sn = e("1-5, 10-15", 11, 1)
        self.assertIn(3, sn)
        self.assertIn(13, sn)

        sn = e("1+", 10, 1)
        self.assertEqual(len(sn), 10)
        self.assertEqual(sn, [_ for _ in range(1, 11)])

        sn = e("4, 1+2", 4, 1)
        self.assertEqual(len(sn), 4)
        self.assertEqual(sn, [4, 1, 2, 3])

        sn = e("~", 1, 1)
        self.assertEqual(len(sn), 1)
        self.assertEqual(sn, [1])

        sn = e("~", 1, 3)
        self.assertEqual(len(sn), 1)
        self.assertEqual(sn, [3])

        sn = e("~+", 2, 5)
        self.assertEqual(len(sn), 2)
        self.assertEqual(sn, [5, 6])

        sn = e("~+3", 4, 5)
        self.assertEqual(len(sn), 4)
        self.assertEqual(sn, [5, 6, 7, 8])

    def test_failures(self):

        e = helpers.extract_serial_numbers

        # Test duplicates
        with self.assertRaises(ValidationError):
            e("1,2,3,3,3", 5, 1)

        # Test invalid length
        with self.assertRaises(ValidationError):
            e("1,2,3", 5, 1)

        # Test empty string
        with self.assertRaises(ValidationError):
            e(", , ,", 0, 1)

        # Test incorrect sign in group
        with self.assertRaises(ValidationError):
            e("10-2", 8, 1)

        # Test invalid group
        with self.assertRaises(ValidationError):
            e("1-5-10", 10, 1)

        with self.assertRaises(ValidationError):
            e("10, a, 7-70j", 4, 1)

        # Test groups are not interpolated with word characters
        with self.assertRaises(ValidationError):
            e("1, 2, 3, E-5", 5, 1)

    def test_combinations(self):
        e = helpers.extract_serial_numbers

        sn = e("1 3-5 9+2", 7, 1)
        self.assertEqual(len(sn), 7)
        self.assertEqual(sn, [1, 3, 4, 5, 9, 10, 11])

        sn = e("1,3-5,9+2", 7, 1)
        self.assertEqual(len(sn), 7)
        self.assertEqual(sn, [1, 3, 4, 5, 9, 10, 11])

        sn = e("~+2", 3, 14)
        self.assertEqual(len(sn), 3)
        self.assertEqual(sn, [14, 15, 16])

        sn = e("~+", 2, 14)
        self.assertEqual(len(sn), 2)
        self.assertEqual(sn, [14, 15])


class TestVersionNumber(TestCase):
    """
    Unit tests for version number functions
    """

    def test_tuple(self):

        v = version.inventreeVersionTuple()
        self.assertEqual(len(v), 3)

        s = '.'.join([str(i) for i in v])

        self.assertTrue(s in version.inventreeVersion())

    def test_comparison(self):
        """
        Test direct comparison of version numbers
        """

        v_a = version.inventreeVersionTuple('1.2.0')
        v_b = version.inventreeVersionTuple('1.2.3')
        v_c = version.inventreeVersionTuple('1.2.4')
        v_d = version.inventreeVersionTuple('2.0.0')

        self.assertTrue(v_b > v_a)
        self.assertTrue(v_c > v_b)
        self.assertTrue(v_d > v_c)
        self.assertTrue(v_d > v_a)


class CurrencyTests(TestCase):
    """
    Unit tests for currency / exchange rate functionality
    """

    def test_rates(self):

        # Initially, there will not be any exchange rate information
        rates = Rate.objects.all()

        self.assertEqual(rates.count(), 0)

        # Without rate information, we cannot convert anything...
        with self.assertRaises(MissingRate):
            convert_money(Money(100, 'USD'), 'AUD')

        with self.assertRaises(MissingRate):
            convert_money(Money(100, 'AUD'), 'USD')

        InvenTree.tasks.update_exchange_rates()

        rates = Rate.objects.all()

        self.assertEqual(rates.count(), len(currency_codes()))

        # Now that we have some exchange rate information, we can perform conversions

        # Forwards
        convert_money(Money(100, 'USD'), 'AUD')

        # Backwards
        convert_money(Money(100, 'AUD'), 'USD')

        # Convert between non base currencies
        convert_money(Money(100, 'CAD'), 'NZD')

        # Convert to a symbol which is not covered
        with self.assertRaises(MissingRate):
            convert_money(Money(100, 'GBP'), 'ZWL')


class TestStatus(TestCase):
    """
    Unit tests for status functions
    """

    def test_check_system_healt(self):
        """test that the system health check is false in testing -> background worker not running"""
        self.assertEqual(status.check_system_health(), False)

    def test_TestMode(self):
        self.assertTrue(ready.isInTestMode())

    def test_Importing(self):
        self.assertEqual(ready.isImportingData(), False)


class TestSettings(TestCase):
    """
    Unit tests for settings
    """

    def setUp(self) -> None:
        self.user_mdl = get_user_model()

        # Create a user for auth
        user = get_user_model()
        self.user = user.objects.create_superuser('testuser1', 'test1@testing.com', 'password1')
        self.client.login(username='testuser1', password='password1')

    def in_env_context(self, envs={}):
        """Patch the env to include the given dict"""
        return mock.patch.dict(os.environ, envs)

    def run_reload(self, envs={}):
        from plugin import registry

        with self.in_env_context(envs):
            settings.USER_ADDED = False
            registry.reload_plugins()

    @override_settings(TESTING_ENV=True)
    def test_set_user_to_few(self):
        # add shortcut
        user_count = self.user_mdl.objects.count
        # enable testing mode
        settings.TESTING_ENV = True

        # nothing set
        self.run_reload()
        self.assertEqual(user_count(), 1)

        # not enough set
        self.run_reload({
            'INVENTREE_ADMIN_USER': 'admin'
        })
        self.assertEqual(user_count(), 1)

        # enough set
        self.run_reload({
            'INVENTREE_ADMIN_USER': 'admin',  # set username
            'INVENTREE_ADMIN_EMAIL': 'info@example.com',  # set email
            'INVENTREE_ADMIN_PASSWORD': 'password123'  # set password
        })
        self.assertEqual(user_count(), 2)

        # create user manually
        self.user_mdl.objects.create_user('testuser', 'test@testing.com', 'password')
        self.assertEqual(user_count(), 3)
        # check it will not be created again
        self.run_reload({
            'INVENTREE_ADMIN_USER': 'testuser',
            'INVENTREE_ADMIN_EMAIL': 'test@testing.com',
            'INVENTREE_ADMIN_PASSWORD': 'password',
        })
        self.assertEqual(user_count(), 3)

        # make sure to clean up
        settings.TESTING_ENV = False

    def test_initial_install(self):
        """Test if install of plugins on startup works"""
        from plugin import registry

        # Check an install run
        response = registry.install_plugin_file()
        self.assertEqual(response, 'first_run')

        # Set dynamic setting to True and rerun to launch install
        InvenTreeSetting.set_setting('PLUGIN_ON_STARTUP', True, self.user)
        registry.reload_plugins()

        # Check that there was anotehr run
        response = registry.install_plugin_file()
        self.assertEqual(response, True)

    def test_helpers_cfg_file(self):
        # normal run - not configured

        valid = [
            'inventree/config.yaml',
            'inventree/dev/config.yaml',
        ]

        self.assertTrue(any([opt in config.get_config_file().lower() for opt in valid]))

        # with env set
        with self.in_env_context({'INVENTREE_CONFIG_FILE': 'my_special_conf.yaml'}):
            self.assertIn('inventree/inventree/my_special_conf.yaml', config.get_config_file().lower())

    def test_helpers_plugin_file(self):
        # normal run - not configured

        valid = [
            'inventree/plugins.txt',
            'inventree/dev/plugins.txt',
        ]

        self.assertTrue(any([opt in config.get_plugin_file().lower() for opt in valid]))

        # with env set
        with self.in_env_context({'INVENTREE_PLUGIN_FILE': 'my_special_plugins.txt'}):
            self.assertIn('my_special_plugins.txt', config.get_plugin_file())

    def test_helpers_setting(self):
        TEST_ENV_NAME = '123TEST'
        # check that default gets returned if not present
        self.assertEqual(config.get_setting(TEST_ENV_NAME, None, '123!'), '123!')

        # with env set
        with self.in_env_context({TEST_ENV_NAME: '321'}):
            self.assertEqual(config.get_setting(TEST_ENV_NAME, None), '321')


class TestInstanceName(TestCase):
    """
    Unit tests for instance name
    """

    def setUp(self):
        # Create a user for auth
        user = get_user_model()
        self.user = user.objects.create_superuser('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

    def test_instance_name(self):

        # default setting
        self.assertEqual(version.inventreeInstanceTitle(), 'InvenTree')

        # set up required setting
        InvenTreeSetting.set_setting("INVENTREE_INSTANCE_TITLE", True, self.user)
        InvenTreeSetting.set_setting("INVENTREE_INSTANCE", "Testing title", self.user)

        self.assertEqual(version.inventreeInstanceTitle(), 'Testing title')
