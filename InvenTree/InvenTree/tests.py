"""Test general functions and helpers."""

import json
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from unittest import mock

import django.core.exceptions as django_exceptions
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils import timezone

import pint.errors
import pytz
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import Rate, convert_money
from djmoney.money import Money
from maintenance_mode.core import get_maintenance_mode, set_maintenance_mode
from sesame.utils import get_user

import InvenTree.conversion
import InvenTree.format
import InvenTree.helpers
import InvenTree.helpers_model
import InvenTree.tasks
from common.models import CustomUnit, InvenTreeSetting
from common.settings import currency_codes
from InvenTree.helpers_mixin import ClassProviderMixin, ClassValidationMixin
from InvenTree.sanitizer import sanitize_svg
from InvenTree.unit_test import InvenTreeTestCase
from part.models import Part, PartCategory
from stock.models import StockItem, StockLocation

from . import config, helpers, ready, status, version
from .tasks import offload_task
from .validators import validate_overage


class HostTest(InvenTreeTestCase):
    """Test for host configuration."""

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_allowed_hosts(self):
        """Test that the ALLOWED_HOSTS functions as expected."""
        self.assertIn('testserver', settings.ALLOWED_HOSTS)

        response = self.client.get('/api/', headers={'host': 'testserver'})

        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/', headers={'host': 'invalidserver'})

        self.assertEqual(response.status_code, 400)

    @override_settings(ALLOWED_HOSTS=['invalidserver.co.uk'])
    def test_allowed_hosts_2(self):
        """Another test for ALLOWED_HOSTS functionality."""
        response = self.client.get('/api/', headers={'host': 'invalidserver.co.uk'})

        self.assertEqual(response.status_code, 200)


class CorsTest(TestCase):
    """Unit tests for CORS functionality."""

    def cors_headers(self):
        """Return a list of CORS headers."""
        return [
            'access-control-allow-origin',
            'access-control-allow-credentials',
            'access-control-allow-methods',
            'access-control-allow-headers',
        ]

    def preflight(self, url, origin, method='GET'):
        """Make a CORS preflight request to the specified URL."""
        headers = {'origin': origin, 'access-control-request-method': method}

        return self.client.options(url, headers=headers)

    def test_no_origin(self):
        """Test that CORS headers are not included for regular requests.

        - We use the /api/ endpoint for this test (it does not require auth)
        - By default, in debug mode *all* CORS origins are allowed
        """
        # Perform an initial response without the "origin" header
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)

        for header in self.cors_headers():
            self.assertNotIn(header, response.headers)

        # Now, perform a "preflight" request with the "origin" header
        response = self.preflight('/api/', origin='http://random-external-server.com')
        self.assertEqual(response.status_code, 200)

        for header in self.cors_headers():
            self.assertIn(header, response.headers)

        self.assertEqual(response.headers['content-length'], '0')
        self.assertEqual(
            response.headers['access-control-allow-origin'],
            'http://random-external-server.com',
        )

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False,
        CORS_ALLOWED_ORIGINS=['http://my-external-server.com'],
        CORS_ALLOWED_ORIGIN_REGEXES=[],
    )
    def test_auth_view(self):
        """Test that CORS requests work for the /auth/ view.

        Here, we are not authorized by default,
        but the CORS headers should still be included.
        """
        url = '/auth/'

        # First, a preflight request with a "valid" origin

        response = self.preflight(url, origin='http://my-external-server.com')

        self.assertEqual(response.status_code, 200)

        for header in self.cors_headers():
            self.assertIn(header, response.headers)

        # Next, a preflight request with an "invalid" origin
        response = self.preflight(url, origin='http://random-external-server.com')

        self.assertEqual(response.status_code, 200)

        for header in self.cors_headers():
            self.assertNotIn(header, response.headers)

        # Next, make a GET request (without a token)
        response = self.client.get(
            url, headers={'origin': 'http://my-external-server.com'}
        )

        # Unauthorized
        self.assertEqual(response.status_code, 401)

        self.assertIn('access-control-allow-origin', response.headers)
        self.assertNotIn('access-control-allow-methods', response.headers)

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False,
        CORS_ALLOWED_ORIGINS=[],
        CORS_ALLOWED_ORIGIN_REGEXES=['http://.*myserver.com'],
    )
    def test_cors_regex(self):
        """Test that CORS regexes work as expected."""
        valid_urls = [
            'http://www.myserver.com',
            'http://test.myserver.com',
            'http://myserver.com',
            'http://www.myserver.com:8080',
        ]

        invalid_urls = [
            'http://myserver.org',
            'http://www.other-server.org',
            'http://google.com',
            'http://myserver.co.uk:8080',
        ]

        for url in valid_urls:
            response = self.preflight('/api/', origin=url)
            self.assertEqual(response.status_code, 200)
            self.assertIn('access-control-allow-origin', response.headers)

        for url in invalid_urls:
            response = self.preflight('/api/', origin=url)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('access-control-allow-origin', response.headers)


class ConversionTest(TestCase):
    """Tests for conversion of physical units."""

    def test_prefixes(self):
        """Test inputs where prefixes are used."""
        tests = {
            '3': 3,
            '3m': 3,
            '3mm': 0.003,
            '3k': 3000,
            '3u': 0.000003,
            '3 inch': 0.0762,
        }

        for val, expected in tests.items():
            q = InvenTree.conversion.convert_physical_value(val, 'm')
            self.assertAlmostEqual(q, expected, 3)

    def test_engineering_units(self):
        """Test that conversion works with engineering notation."""
        # Run some basic checks over the helper function
        tests = [
            ('3', '3'),
            ('3k3', '3.3k'),
            ('123R45', '123.45R'),
            ('10n5F', '10.5nF'),
        ]

        for val, expected in tests:
            self.assertEqual(
                InvenTree.conversion.from_engineering_notation(val), expected
            )

        # Now test the conversion function
        tests = [('33k3ohm', 33300), ('123kohm45', 123450), ('10n005', 0.000000010005)]

        for val, expected in tests:
            output = InvenTree.conversion.convert_physical_value(
                val, 'ohm', strip_units=True
            )
            self.assertAlmostEqual(output, expected, 12)

    def test_scientific_notation(self):
        """Test that scientific notation is handled correctly."""
        tests = [
            ('3E2', 300),
            ('-12.3E-3', -0.0123),
            ('1.23E-3', 0.00123),
            ('99E9', 99000000000),
        ]

        for val, expected in tests:
            output = InvenTree.conversion.convert_physical_value(val, strip_units=True)
            self.assertAlmostEqual(output, expected, 6)

    def test_temperature_units(self):
        """Test conversion of temperature units.

        Ref: https://github.com/inventree/InvenTree/issues/6495
        """
        tests = [
            ('3.3°F', '°C', -15.944),
            ('273°K', '°F', 31.73),
            ('900', '°C', 900),
            ('900°F', 'degF', 900),
            ('900°K', '°C', 626.85),
            ('800', 'kelvin', 800),
            ('-100°C', 'fahrenheit', -148),
            ('-100 °C', 'Fahrenheit', -148),
            ('-100 Celsius', 'fahrenheit', -148),
            ('-123.45 fahrenheit', 'kelvin', 186.7888),
            ('-99Fahrenheit', 'Celsius', -72.7777),
        ]

        for val, unit, expected in tests:
            output = InvenTree.conversion.convert_physical_value(
                val, unit, strip_units=True
            )
            self.assertAlmostEqual(output, expected, 3)

    def test_base_units(self):
        """Test conversion to specified base units."""
        tests = {
            '3': 3,
            '3 dozen': 36,
            '50 dozen kW': 600000,
            '1 / 10': 0.1,
            '1/2 kW': 500,
            '1/2 dozen kW': 6000,
            '0.005 MW': 5000,
        }

        for val, expected in tests.items():
            q = InvenTree.conversion.convert_physical_value(val, 'W')
            self.assertAlmostEqual(q, expected, places=2)
            q = InvenTree.conversion.convert_physical_value(val, 'W', strip_units=False)
            self.assertAlmostEqual(float(q.magnitude), expected, places=2)

    def test_imperial_lengths(self):
        """Test support of imperial length measurements."""
        tests = [
            ('1 inch', 'mm', 25.4),
            ('1 "', 'mm', 25.4),
            ('2 "', 'inches', 2),
            ('3 feet', 'inches', 36),
            ("3'", 'inches', 36),
            ("7 '", 'feet', 7),
        ]

        for val, unit, expected in tests:
            output = InvenTree.conversion.convert_physical_value(
                val, unit, strip_units=True
            )

            self.assertAlmostEqual(output, expected, 3)

    def test_dimensionless_units(self):
        """Tests for 'dimensionless' unit quantities."""
        # Test some dimensionless units
        tests = {
            'ea': 1,
            'each': 1,
            '3 piece': 3,
            '5 dozen': 60,
            '3 hundred': 300,
            '2 thousand': 2000,
            '12 pieces': 12,
            '1 / 10': 0.1,
            '1/2': 0.5,
            '-1 / 16': -0.0625,
            '3/2': 1.5,
            '1/2 dozen': 6,
        }

        for val, expected in tests.items():
            # Convert, and leave units
            q = InvenTree.conversion.convert_physical_value(val, strip_units=False)
            self.assertAlmostEqual(float(q.magnitude), expected, 3)

            # Convert, and strip units
            q = InvenTree.conversion.convert_physical_value(val)
            self.assertAlmostEqual(q, expected, 3)

    def test_invalid_units(self):
        """Test conversion with bad units."""
        tests = {'3': '10', '13': '-?-', '-3': 'xyz', '-12': '-12', '1/0': '1/0'}

        for val, unit in tests.items():
            with self.assertRaises(ValidationError):
                InvenTree.conversion.convert_physical_value(val, unit)

    def test_invalid_values(self):
        """Test conversion of invalid inputs."""
        inputs = ['-x', '1/0', 'xyz', '12B45C']

        for val in inputs:
            # Test with a provided unit
            with self.assertRaises(ValidationError):
                InvenTree.conversion.convert_physical_value(val, 'meter')

            # Test dimensionless
            with self.assertRaises(ValidationError):
                InvenTree.conversion.convert_physical_value(val)

    def test_custom_units(self):
        """Tests for custom unit conversion."""
        # Start with an empty set of units
        CustomUnit.objects.all().delete()
        InvenTree.conversion.reload_unit_registry()

        # Ensure that the custom unit does *not* exist to start with
        reg = InvenTree.conversion.get_unit_registry()

        with self.assertRaises(pint.errors.UndefinedUnitError):
            reg['hpmm']

        # Create a new custom unit
        CustomUnit.objects.create(
            name='fanciful_unit', definition='henry / mm', symbol='hpmm'
        )

        # Reload registry
        reg = InvenTree.conversion.get_unit_registry()

        # Ensure that the custom unit is now available
        reg['hpmm']

        # Convert some values
        tests = {
            '1': 1,
            '1 hpmm': 1000000,
            '1 / 10 hpmm': 100000,
            '1 / 100 hpmm': 10000,
            '0.3 hpmm': 300000,
            '-7hpmm': -7000000,
        }

        for val, expected in tests.items():
            # Convert, and leave units
            q = InvenTree.conversion.convert_physical_value(
                val, 'henry / km', strip_units=False
            )
            self.assertAlmostEqual(float(q.magnitude), expected, 2)

            # Convert and strip units
            q = InvenTree.conversion.convert_physical_value(val, 'henry / km')
            self.assertAlmostEqual(q, expected, 2)


class ValidatorTest(TestCase):
    """Simple tests for custom field validators."""

    def test_overage(self):
        """Test overage validator."""
        validate_overage('100%')
        validate_overage('10')
        validate_overage('45.2 %')

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage('-1')

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage('-2.04 %')

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage('105%')

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage('xxx %')

        with self.assertRaises(django_exceptions.ValidationError):
            validate_overage('aaaa')

    def test_url_validation(self):
        """Test for AllowedURLValidator."""
        from common.models import InvenTreeSetting
        from part.models import Part, PartCategory

        # Without strict URL validation
        InvenTreeSetting.set_setting('INVENTREE_STRICT_URLS', False, None)

        n = Part.objects.count()
        cat = PartCategory.objects.first()

        # Should pass, even without a schema
        Part.objects.create(
            name=f'Part {n}',
            description='Link without schema',
            category=cat,
            link='www.google.com',
        )

        # With strict URL validation
        InvenTreeSetting.set_setting('INVENTREE_STRICT_URLS', True, None)

        with self.assertRaises(ValidationError):
            Part.objects.create(
                name=f'Part {n + 1}',
                description='Link without schema',
                category=cat,
                link='www.google.com',
            )


class FormatTest(TestCase):
    """Unit tests for custom string formatting functionality."""

    def test_parse(self):
        """Tests for the 'parse_format_string' function."""
        # Extract data from a valid format string
        fmt = 'PO-{abc:02f}-{ref:04d}-{date}-???'

        info = InvenTree.format.parse_format_string(fmt)

        self.assertIn('abc', info)
        self.assertIn('ref', info)
        self.assertIn('date', info)

        # Try with invalid strings
        for fmt in ['PO-{{xyz}', 'PO-{xyz}}', 'PO-{xyz}-{']:
            with self.assertRaises(ValueError):
                InvenTree.format.parse_format_string(fmt)

    def test_create_regex(self):
        """Test function for creating a regex from a format string."""
        tests = {
            'PO-123-{ref:04f}': r'^PO\-123\-(?P<ref>.+)$',
            '{PO}-???-{ref}-{date}-22': r'^(?P<PO>.+)\-...\-(?P<ref>.+)\-(?P<date>.+)\-22$',
            'ABC-123-###-{ref}': r'^ABC\-123\-\d\d\d\-(?P<ref>.+)$',
            'ABC-123': r'^ABC\-123$',
        }

        for fmt, reg in tests.items():
            self.assertEqual(InvenTree.format.construct_format_regex(fmt), reg)

    def test_validate_format(self):
        """Test that string validation works as expected."""
        # These tests should pass
        for value, pattern in {
            'ABC-hello-123': '???-{q}-###',
            'BO-1234': 'BO-{ref}',
            '111.222.fred.china': '???.###.{name}.{place}',
            'PO-1234': 'PO-{ref:04d}',
        }.items():
            self.assertTrue(InvenTree.format.validate_string(value, pattern))

        # These tests should fail
        for value, pattern in {
            'ABC-hello-123': '###-{q}-???',
            'BO-1234': 'BO.{ref}',
            'BO-####': 'BO-{pattern}-{next}',
            'BO-123d': 'BO-{ref:04d}',
        }.items():
            self.assertFalse(InvenTree.format.validate_string(value, pattern))

    def test_extract_value(self):
        """Test that we can extract named values based on a format string."""
        # Simple tests based on a straight-forward format string
        fmt = 'PO-###-{ref:04d}'

        tests = {'123': 'PO-123-123', '456': 'PO-123-456', '789': 'PO-123-789'}

        for k, v in tests.items():
            self.assertEqual(InvenTree.format.extract_named_group('ref', v, fmt), k)

        # However these ones should fail
        tests = {'abc': 'PO-123-abc', 'xyz': 'PO-123-xyz'}

        for v in tests.values():
            with self.assertRaises(ValueError):
                InvenTree.format.extract_named_group('ref', v, fmt)

        # More complex tests
        fmt = 'PO-{date}-{test}-???-{ref}-###'
        val = 'PO-2022-02-01-hello-ABC-12345-222'

        data = {'date': '2022-02-01', 'test': 'hello', 'ref': '12345'}

        for k, v in data.items():
            self.assertEqual(InvenTree.format.extract_named_group(k, val, fmt), v)

        # Test for error conditions

        # Raises a ValueError as the format string is bad
        with self.assertRaises(ValueError):
            InvenTree.format.extract_named_group('test', 'PO-1234-5', 'PO-{test}-{')

        # Raises a NameError as the named group does not exist in the format string
        with self.assertRaises(NameError):
            InvenTree.format.extract_named_group('missing', 'PO-12345', 'PO-{test}')

        # Raises a ValueError as the value does not match the format string
        with self.assertRaises(ValueError):
            InvenTree.format.extract_named_group('test', 'PO-1234', 'PO-{test}-1234')

        with self.assertRaises(ValueError):
            InvenTree.format.extract_named_group('test', 'PO-ABC-xyz', 'PO-###-{test}')

    def test_currency_formatting(self):
        """Test that currency formatting works correctly for multiple currencies."""
        test_data = (
            (Money(3651.285718, 'USD'), 4, True, '$3,651.2857'),  # noqa: E201,E202
            (Money(487587.849178, 'CAD'), 5, True, 'CA$487,587.84918'),  # noqa: E201,E202
            (Money(0.348102, 'EUR'), 1, False, '0.3'),  # noqa: E201,E202
            (Money(0.916530, 'GBP'), 1, True, '£0.9'),  # noqa: E201,E202
            (Money(61.031024, 'JPY'), 3, False, '61.031'),  # noqa: E201,E202
            (Money(49609.694602, 'JPY'), 1, True, '¥49,609.7'),  # noqa: E201,E202
            (Money(155565.264777, 'AUD'), 2, False, '155,565.26'),  # noqa: E201,E202
            (Money(0.820437, 'CNY'), 4, True, 'CN¥0.8204'),  # noqa: E201,E202
            (Money(7587.849178, 'EUR'), 0, True, '€7,588'),  # noqa: E201,E202
            (Money(0.348102, 'GBP'), 3, False, '0.348'),  # noqa: E201,E202
            (Money(0.652923, 'CHF'), 0, True, 'CHF1'),  # noqa: E201,E202
            (Money(0.820437, 'CNY'), 1, True, 'CN¥0.8'),  # noqa: E201,E202
            (Money(98789.5295680, 'CHF'), 0, False, '98,790'),  # noqa: E201,E202
            (Money(0.585787, 'USD'), 1, True, '$0.6'),  # noqa: E201,E202
            (Money(0.690541, 'CAD'), 3, True, 'CA$0.691'),  # noqa: E201,E202
            (Money(427.814104, 'AUD'), 5, True, 'A$427.81410'),  # noqa: E201,E202
        )

        with self.settings(LANGUAGE_CODE='en-us'):
            for value, decimal_places, include_symbol, expected_result in test_data:
                result = InvenTree.format.format_money(
                    value, decimal_places=decimal_places, include_symbol=include_symbol
                )

                self.assertEqual(result, expected_result)


class TestHelpers(TestCase):
    """Tests for InvenTree helper functions."""

    def test_absolute_url(self):
        """Test helper function for generating an absolute URL."""
        base = 'https://demo.inventree.org:12345'

        InvenTreeSetting.set_setting('INVENTREE_BASE_URL', base, change_user=None)

        tests = {
            '': base,
            'api/': base + '/api/',
            '/api/': base + '/api/',
            'api': base + '/api',
            'media/label/output/': base + '/media/label/output/',
            'static/logo.png': base + '/static/logo.png',
            'https://www.google.com': 'https://www.google.com',
            'https://demo.inventree.org:12345/out.html': 'https://demo.inventree.org:12345/out.html',
            'https://demo.inventree.org/test.html': 'https://demo.inventree.org/test.html',
            'http://www.cwi.nl:80/%7Eguido/Python.html': 'http://www.cwi.nl:80/%7Eguido/Python.html',
            'test.org': base + '/test.org',
        }

        for url, expected in tests.items():
            # Test with supplied base URL
            self.assertEqual(
                InvenTree.helpers_model.construct_absolute_url(url, base_url=base),
                expected,
            )

            # Test without supplied base URL
            self.assertEqual(
                InvenTree.helpers_model.construct_absolute_url(url), expected
            )

    def test_image_url(self):
        """Test if a filename looks like an image."""
        for name in ['ape.png', 'bat.GiF', 'apple.WeBP', 'BiTMap.Bmp']:
            self.assertTrue(helpers.TestIfImageURL(name))

        for name in ['no.doc', 'nah.pdf', 'whatpng']:
            self.assertFalse(helpers.TestIfImageURL(name))

    def test_str2bool(self):
        """Test string to boolean conversion."""
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
        """Test isNull."""
        for s in ['null', 'none', '', '-1', 'false']:
            self.assertTrue(helpers.isNull(s))

        for s in ['yes', 'frog', 'llama', 'true']:
            self.assertFalse(helpers.isNull(s))

    def testStaticUrl(self):
        """Test static url helpers."""
        self.assertEqual(helpers.getStaticUrl('test.jpg'), '/static/test.jpg')
        self.assertEqual(helpers.getBlankImage(), '/static/img/blank_image.png')
        self.assertEqual(
            helpers.getBlankThumbnail(), '/static/img/blank_image.thumbnail.png'
        )

    def testMediaUrl(self):
        """Test getMediaUrl."""
        self.assertEqual(helpers.getMediaUrl('xx/yy.png'), '/media/xx/yy.png')

    def testDecimal2String(self):
        """Test decimal2string."""
        self.assertEqual(helpers.decimal2string(Decimal('1.2345000')), '1.2345')
        self.assertEqual(helpers.decimal2string('test'), 'test')

    def test_logo_image(self):
        """Test for retrieving logo image."""
        # By default, there is no custom logo provided
        logo = helpers.getLogoImage()
        self.assertEqual(logo, '/static/img/inventree.png')

        logo = helpers.getLogoImage(as_file=True)
        self.assertEqual(logo, f'file://{settings.STATIC_ROOT}/img/inventree.png')

    def test_download_image(self):
        """Test function for downloading image from remote URL."""
        # Run check with a sequence of bad URLs
        for url in ['blog', 'htp://test.com/?', 'google', '\\invalid-url']:
            with self.assertRaises(django_exceptions.ValidationError):
                InvenTree.helpers_model.download_image_from_url(url)

        def dl_helper(url, expected_error, timeout=2.5, retries=3):
            """Helper function for unit testing downloads.

            As the httpstat.us service occasionally refuses a connection,
            we will simply try multiple times
            """
            tries = 0

            with self.assertRaises(expected_error):
                while tries < retries:
                    try:
                        InvenTree.helpers_model.download_image_from_url(
                            url, timeout=timeout
                        )
                        break
                    except Exception as exc:
                        if type(exc) is expected_error:
                            # Re-throw this error
                            raise exc
                        else:
                            print('Unexpected error:', type(exc), exc)

                    tries += 1
                    time.sleep(10 * tries)

        # Attempt to download an image which throws a 404
        # TODO: Re-implement this test when we are happier with the external service
        # dl_helper("https://httpstat.us/404", requests.exceptions.HTTPError, timeout=10)

        # Attempt to download, but timeout
        # TODO: Re-implement this test when we are happier with the external service
        # dl_helper("https://httpstat.us/200?sleep=5000", requests.exceptions.ReadTimeout, timeout=1)

        large_img = 'https://github.com/inventree/InvenTree/raw/master/InvenTree/InvenTree/static/img/paper_splash_large.jpg'

        InvenTreeSetting.set_setting(
            'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE', 1, change_user=None
        )

        # Attempt to download an image which is too large
        with self.assertRaises(ValueError):
            InvenTree.helpers_model.download_image_from_url(large_img, timeout=10)

        # Increase allowable download size
        InvenTreeSetting.set_setting(
            'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE', 5, change_user=None
        )

        # Download a valid image (should not throw an error)
        InvenTree.helpers_model.download_image_from_url(large_img, timeout=10)

    def test_model_mixin(self):
        """Test the getModelsWithMixin function."""
        from InvenTree.models import InvenTreeBarcodeMixin

        models = InvenTree.helpers_model.getModelsWithMixin(InvenTreeBarcodeMixin)

        self.assertIn(Part, models)
        self.assertIn(StockLocation, models)
        self.assertIn(StockItem, models)

        self.assertNotIn(PartCategory, models)
        self.assertNotIn(InvenTreeSetting, models)

    def test_test_key(self):
        """Test for the generateTestKey function."""
        tests = {
            ' Hello World ': 'helloworld',
            ' MY NEW TEST KEY ': 'mynewtestkey',
            ' 1234 5678': '_12345678',
            ' 100 percenT': '_100percent',
            ' MY_NEW_TEST': 'my_new_test',
            ' 100_new_tests': '_100_new_tests',
        }

        for name, key in tests.items():
            self.assertEqual(helpers.generateTestKey(name), key)


class TestTimeFormat(TestCase):
    """Unit test for time formatting functionality."""

    @override_settings(TIME_ZONE='UTC')
    def test_tz_utc(self):
        """Check UTC timezone."""
        self.assertEqual(InvenTree.helpers.server_timezone(), 'UTC')

    @override_settings(TIME_ZONE='Europe/London')
    def test_tz_london(self):
        """Check London timezone."""
        self.assertEqual(InvenTree.helpers.server_timezone(), 'Europe/London')

    @override_settings(TIME_ZONE='Australia/Sydney')
    def test_to_local_time(self):
        """Test that the local time conversion works as expected."""
        source_time = timezone.datetime(
            year=2000,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            tzinfo=pytz.timezone('Europe/London'),
        )

        tests = [
            ('UTC', '2000-01-01 00:01:00+00:00'),
            ('Europe/London', '2000-01-01 00:00:00-00:01'),
            ('America/New_York', '1999-12-31 19:01:00-05:00'),
            # All following tests should result in the same value
            ('Australia/Sydney', '2000-01-01 11:01:00+11:00'),
            (None, '2000-01-01 11:01:00+11:00'),
            ('', '2000-01-01 11:01:00+11:00'),
        ]

        for tz, expected in tests:
            local_time = InvenTree.helpers.to_local_time(source_time, tz)
            self.assertEqual(local_time, expected)


class TestQuoteWrap(TestCase):
    """Tests for string wrapping."""

    def test_single(self):
        """Test WrapWithQuotes."""
        self.assertEqual(helpers.WrapWithQuotes('hello'), '"hello"')
        self.assertEqual(helpers.WrapWithQuotes('hello"'), '"hello"')


class TestIncrement(TestCase):
    """Tests for increment function."""

    def tests(self):
        """Test 'intelligent' incrementing function."""
        tests = [
            ('', '1'),
            (1, '2'),
            ('001', '002'),
            ('1001', '1002'),
            ('ABC123', 'ABC124'),
            ('XYZ0', 'XYZ1'),
            ('123Q', '123Q'),
            ('QQQ', 'QQQ'),
        ]

        for test in tests:
            a, b = test

            result = helpers.increment(a)
            self.assertEqual(result, b)


class TestMakeBarcode(TestCase):
    """Tests for barcode string creation."""

    def test_barcode_extended(self):
        """Test creation of barcode with extended data."""
        bc = helpers.MakeBarcode(
            'part', 3, {'id': 3, 'url': 'www.google.com'}, brief=False
        )

        self.assertIn('part', bc)
        self.assertIn('tool', bc)
        self.assertIn('"tool": "InvenTree"', bc)

        data = json.loads(bc)

        self.assertEqual(data['part']['id'], 3)
        self.assertEqual(data['part']['url'], 'www.google.com')

    def test_barcode_brief(self):
        """Test creation of simple barcode."""
        bc = helpers.MakeBarcode('stockitem', 7)

        data = json.loads(bc)
        self.assertEqual(len(data), 1)
        self.assertEqual(data['stockitem'], 7)


class TestDownloadFile(TestCase):
    """Tests for DownloadFile."""

    def test_download(self):
        """Tests for DownloadFile."""
        helpers.DownloadFile('hello world', 'out.txt')
        helpers.DownloadFile(bytes(b'hello world'), 'out.bin')


class TestMPTT(TestCase):
    """Tests for the MPTT tree models."""

    fixtures = ['location']

    @classmethod
    def setUpTestData(cls):
        """Setup for all tests."""
        super().setUpTestData()
        StockLocation.objects.rebuild()

    def test_self_as_parent(self):
        """Test that we cannot set self as parent."""
        loc = StockLocation.objects.get(pk=4)
        loc.parent = loc

        with self.assertRaises(ValidationError):
            loc.save()

    def test_child_as_parent(self):
        """Test that we cannot set a child as parent."""
        parent = StockLocation.objects.get(pk=4)
        child = StockLocation.objects.get(pk=5)

        parent.parent = child

        with self.assertRaises(ValidationError):
            parent.save()

    def test_move(self):
        """Move an item to a different tree."""
        drawer = StockLocation.objects.get(name='Drawer_1')

        # Record the tree ID
        tree = drawer.tree_id

        home = StockLocation.objects.get(name='Home')

        drawer.parent = home
        drawer.save()

        self.assertNotEqual(tree, drawer.tree_id)


class TestSerialNumberExtraction(TestCase):
    """Tests for serial number extraction code.

    Note that while serial number extraction is made available to custom plugins,
    only simple integer-based extraction is tested here.
    """

    def test_simple(self):
        """Test simple serial numbers."""
        e = helpers.extract_serial_numbers

        # Test a range of numbers
        sn = e('1-5', 5, 1)
        self.assertEqual(len(sn), 5)
        for i in range(1, 6):
            self.assertIn(str(i), sn)

        sn = e('11-30', 20, 1)
        self.assertEqual(len(sn), 20)

        sn = e('1, 2, 3, 4, 5', 5, 1)
        self.assertEqual(len(sn), 5)

        # Test partially specifying serials
        sn = e('1, 2, 4+', 5, 1)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, ['1', '2', '4', '5', '6'])

        # Test groups are not interpolated if enough serials are supplied
        sn = e('1, 2, 3, AF5-69H, 5', 5, 1)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, ['1', '2', '3', 'AF5-69H', '5'])

        # Test groups are not interpolated with more than one hyphen in a word
        sn = e('1, 2, TG-4SR-92, 4+', 5, 1)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, ['1', '2', 'TG-4SR-92', '4', '5'])

        # Test multiple placeholders
        sn = e('1 2 ~ ~ ~', 5, 2)
        self.assertEqual(len(sn), 5)
        self.assertEqual(sn, ['1', '2', '3', '4', '5'])

        sn = e('1-5, 10-15', 11, 1)
        self.assertIn('3', sn)
        self.assertIn('13', sn)

        sn = e('1+', 10, 1)
        self.assertEqual(len(sn), 10)
        self.assertEqual(sn, [str(_) for _ in range(1, 11)])

        sn = e('4, 1+2', 4, 1)
        self.assertEqual(len(sn), 4)
        self.assertEqual(sn, ['4', '1', '2', '3'])

        sn = e('~', 1, 1)
        self.assertEqual(len(sn), 1)
        self.assertEqual(sn, ['2'])

        sn = e('~', 1, 3)
        self.assertEqual(len(sn), 1)
        self.assertEqual(sn, ['4'])

        sn = e('~+', 2, 4)
        self.assertEqual(len(sn), 2)
        self.assertEqual(sn, ['5', '6'])

        sn = e('~+3', 4, 4)
        self.assertEqual(len(sn), 4)
        self.assertEqual(sn, ['5', '6', '7', '8'])

    def test_failures(self):
        """Test wrong serial numbers."""
        e = helpers.extract_serial_numbers

        # Test duplicates
        with self.assertRaises(ValidationError):
            e('1,2,3,3,3', 5, 1)

        # Test invalid length
        with self.assertRaises(ValidationError):
            e('1,2,3', 5, 1)

        # Test empty string
        with self.assertRaises(ValidationError):
            e(', , ,', 0, 1)

        # Test incorrect sign in group
        with self.assertRaises(ValidationError):
            e('10-2', 8, 1)

        # Test invalid group
        with self.assertRaises(ValidationError):
            e('1-5-10', 10, 1)

        with self.assertRaises(ValidationError):
            e('10, a, 7-70j', 4, 1)

        # Test groups are not interpolated with word characters
        with self.assertRaises(ValidationError):
            e('1, 2, 3, E-5', 5, 1)

        # Extract a range of values with a smaller range
        with self.assertRaises(ValidationError) as exc:
            e('11-50', 10, 1)
            self.assertIn('Range quantity exceeds 10', str(exc))

        # Test groups are not interpolated with alpha characters
        with self.assertRaises(ValidationError) as exc:
            e('1, A-2, 3+', 5, 1)
            self.assertIn('Invalid group range: A-2', str(exc))

    def test_combinations(self):
        """Test complex serial number combinations."""
        e = helpers.extract_serial_numbers

        sn = e('1 3-5 9+2', 7, 1)
        self.assertEqual(len(sn), 7)
        self.assertEqual(sn, ['1', '3', '4', '5', '9', '10', '11'])

        sn = e('1,3-5,9+2', 7, 1)
        self.assertEqual(len(sn), 7)
        self.assertEqual(sn, ['1', '3', '4', '5', '9', '10', '11'])

        sn = e('~+2', 3, 13)
        self.assertEqual(len(sn), 3)
        self.assertEqual(sn, ['14', '15', '16'])

        sn = e('~+', 2, 13)
        self.assertEqual(len(sn), 2)
        self.assertEqual(sn, ['14', '15'])

        # Test multiple increment groups
        sn = e('~+4, 20+4, 30+4', 15, 10)
        self.assertEqual(len(sn), 15)

        for v in [14, 24, 34]:
            self.assertIn(str(v), sn)

        # Test multiple range groups
        sn = e('11-20, 41-50, 91-100', 30, 1)
        self.assertEqual(len(sn), 30)

        for v in range(11, 21):
            self.assertIn(str(v), sn)
        for v in range(41, 51):
            self.assertIn(str(v), sn)
        for v in range(91, 101):
            self.assertIn(str(v), sn)


class TestVersionNumber(TestCase):
    """Unit tests for version number functions."""

    def test_tuple(self):
        """Test inventreeVersionTuple."""
        v = version.inventreeVersionTuple()
        self.assertEqual(len(v), 3)

        s = '.'.join([str(i) for i in v])

        self.assertTrue(s in version.inventreeVersion())

    def test_comparison(self):
        """Test direct comparison of version numbers."""
        v_a = version.inventreeVersionTuple('1.2.0')
        v_b = version.inventreeVersionTuple('1.2.3')
        v_c = version.inventreeVersionTuple('1.2.4')
        v_d = version.inventreeVersionTuple('2.0.0')

        self.assertTrue(v_b > v_a)
        self.assertTrue(v_c > v_b)
        self.assertTrue(v_d > v_c)
        self.assertTrue(v_d > v_a)

    def test_commit_info(self):
        """Test that the git commit information is extracted successfully."""
        envs = {
            'INVENTREE_COMMIT_HASH': 'abcdef',
            'INVENTREE_COMMIT_DATE': '2022-12-31',
        }

        # Check that the environment variables take priority

        with mock.patch.dict(os.environ, envs):
            self.assertEqual(version.inventreeCommitHash(), 'abcdef')
            self.assertEqual(version.inventreeCommitDate(), '2022-12-31')

        import subprocess

        # Check that the current .git values work too

        hash = str(
            subprocess.check_output('git rev-parse --short HEAD'.split()), 'utf-8'
        ).strip()

        self.assertEqual(hash, version.inventreeCommitHash())

        d = (
            str(subprocess.check_output('git show -s --format=%ci'.split()), 'utf-8')
            .strip()
            .split(' ')[0]
        )
        self.assertEqual(d, version.inventreeCommitDate())


class CurrencyTests(TestCase):
    """Unit tests for currency / exchange rate functionality."""

    def test_rates(self):
        """Test exchange rate update."""
        # Initially, there will not be any exchange rate information
        rates = Rate.objects.all()

        self.assertEqual(rates.count(), 0)

        # Without rate information, we cannot convert anything...
        with self.assertRaises(MissingRate):
            convert_money(Money(100, 'USD'), 'AUD')

        with self.assertRaises(MissingRate):
            convert_money(Money(100, 'AUD'), 'USD')

        update_successful = False

        # Note: the update sometimes fails in CI, let's give it a few chances
        for _ in range(10):
            InvenTree.tasks.update_exchange_rates()

            rates = Rate.objects.all()

            if rates.count() == len(currency_codes()):
                update_successful = True
                break

            else:  # pragma: no cover
                print('Exchange rate update failed - retrying')
                print(f'Expected {currency_codes()}, got {[a.currency for a in rates]}')
                time.sleep(1)

        self.assertTrue(update_successful)

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
    """Unit tests for status functions."""

    def test_check_system_health(self):
        """Test that the system health check is false in testing -> background worker not running."""
        self.assertEqual(status.check_system_health(), False)

    def test_TestMode(self):
        """Test isInTestMode check."""
        self.assertTrue(ready.isInTestMode())

    def test_Importing(self):
        """Test isImportingData check."""
        self.assertEqual(ready.isImportingData(), False)


class TestSettings(InvenTreeTestCase):
    """Unit tests for settings."""

    superuser = True

    def in_env_context(self, envs=None):
        """Patch the env to include the given dict."""
        # Set default - see B006
        if envs is None:
            envs = {}

        return mock.patch.dict(os.environ, envs)

    def run_reload(self, envs=None):
        """Helper function to reload InvenTree."""
        # Set default - see B006
        if envs is None:
            envs = {}

        from plugin import registry

        with self.in_env_context(envs):
            settings.USER_ADDED = False
            registry.reload_plugins()

    @override_settings(TESTING_ENV=True)
    def test_set_user_to_few(self):
        """Test adding an admin user via env variables."""
        user_model = get_user_model()
        # add shortcut
        user_count = user_model.objects.count
        # enable testing mode
        settings.TESTING_ENV = True

        # nothing set
        self.run_reload()
        self.assertEqual(user_count(), 1)

        # not enough set
        self.run_reload({'INVENTREE_ADMIN_USER': 'admin'})
        self.assertEqual(user_count(), 1)

        # enough set
        self.run_reload({
            'INVENTREE_ADMIN_USER': 'admin',  # set username
            'INVENTREE_ADMIN_EMAIL': 'info@example.com',  # set email
            'INVENTREE_ADMIN_PASSWORD': 'password123',  # set password
        })
        self.assertEqual(user_count(), 2)

        username2 = 'testuser1'
        email2 = 'test1@testing.com'
        password2 = 'password1'

        # create user manually
        user_model.objects.create_user(username2, email2, password2)
        self.assertEqual(user_count(), 3)
        # check it will not be created again
        self.run_reload({
            'INVENTREE_ADMIN_USER': username2,
            'INVENTREE_ADMIN_EMAIL': email2,
            'INVENTREE_ADMIN_PASSWORD': password2,
        })
        self.assertEqual(user_count(), 3)

        # make sure to clean up
        settings.TESTING_ENV = False

    def test_initial_install(self):
        """Test if install of plugins on startup works."""
        from plugin import registry

        if not settings.DOCKER:
            # Check an install run
            response = registry.install_plugin_file()
            self.assertEqual(response, 'first_run')

            # Set dynamic setting to True and rerun to launch install
            InvenTreeSetting.set_setting('PLUGIN_ON_STARTUP', True, self.user)
            registry.reload_plugins(full_reload=True)

        # Check that there was another run
        response = registry.install_plugin_file()
        self.assertEqual(response, True)

    def test_helpers_cfg_file(self):
        """Test get_config_file."""
        # normal run - not configured

        valid = ['inventree/config.yaml', 'inventree/data/config.yaml']

        self.assertTrue(
            any(opt in str(config.get_config_file()).lower() for opt in valid)
        )

        # with env set
        with self.in_env_context({
            'INVENTREE_CONFIG_FILE': '_testfolder/my_special_conf.yaml'
        }):
            self.assertIn(
                'inventree/_testfolder/my_special_conf.yaml',
                str(config.get_config_file()).lower(),
            )

    def test_helpers_plugin_file(self):
        """Test get_plugin_file."""
        # normal run - not configured

        valid = ['inventree/plugins.txt', 'inventree/data/plugins.txt']

        self.assertTrue(
            any(opt in str(config.get_plugin_file()).lower() for opt in valid)
        )

        # with env set
        with self.in_env_context({
            'INVENTREE_PLUGIN_FILE': '_testfolder/my_special_plugins.txt'
        }):
            self.assertIn(
                '_testfolder/my_special_plugins.txt', str(config.get_plugin_file())
            )

    def test_helpers_setting(self):
        """Test get_setting."""
        TEST_ENV_NAME = '123TEST'
        # check that default gets returned if not present
        self.assertEqual(config.get_setting(TEST_ENV_NAME, None, '123!'), '123!')

        # with env set
        with self.in_env_context({TEST_ENV_NAME: '321'}):
            self.assertEqual(config.get_setting(TEST_ENV_NAME, None), '321')

        # test typecasting to dict - None should be mapped to empty dict
        self.assertEqual(
            config.get_setting(TEST_ENV_NAME, None, None, typecast=dict), {}
        )

        # test typecasting to dict - valid JSON string should be mapped to corresponding dict
        with self.in_env_context({TEST_ENV_NAME: '{"a": 1}'}):
            self.assertEqual(
                config.get_setting(TEST_ENV_NAME, None, typecast=dict), {'a': 1}
            )

        # test typecasting to dict - invalid JSON string should be mapped to empty dict
        with self.in_env_context({TEST_ENV_NAME: "{'a': 1}"}):
            self.assertEqual(config.get_setting(TEST_ENV_NAME, None, typecast=dict), {})


class TestInstanceName(InvenTreeTestCase):
    """Unit tests for instance name."""

    def test_instance_name(self):
        """Test instance name settings."""
        # default setting
        self.assertEqual(version.inventreeInstanceTitle(), 'InvenTree')

        # set up required setting
        InvenTreeSetting.set_setting('INVENTREE_INSTANCE_TITLE', True, self.user)
        InvenTreeSetting.set_setting('INVENTREE_INSTANCE', 'Testing title', self.user)

        self.assertEqual(version.inventreeInstanceTitle(), 'Testing title')

        try:
            from django.contrib.sites.models import Site
        except (ImportError, RuntimeError):
            # Multi-site support not enabled
            return

        # The site should also be changed
        site_obj = Site.objects.all().order_by('id').first()
        self.assertEqual(site_obj.name, 'Testing title')

    def test_instance_url(self):
        """Test instance url settings."""
        # Set up required setting
        InvenTreeSetting.set_setting(
            'INVENTREE_BASE_URL', 'http://127.1.2.3', self.user
        )

        # No further tests if multi-site support is not enabled
        if not settings.SITE_MULTI:
            return

        # The site should also be changed
        try:
            from django.contrib.sites.models import Site

            site_obj = Site.objects.all().order_by('id').first()
            self.assertEqual(site_obj.domain, 'http://127.1.2.3')
        except Exception:
            pass


class TestOffloadTask(InvenTreeTestCase):
    """Tests for offloading tasks to the background worker."""

    fixtures = ['category', 'part', 'location', 'stock']

    def test_offload_tasks(self):
        """Test that we can offload various tasks to the background worker thread.

        This set of tests also ensures that various types of objects
        can be encoded by the django-q serialization layer!

        Note that as the background worker is not actually running for the tests,
        the call to 'offload_task' won't really *do* anything!

        However, it serves as a validation that object serialization works!

        Ref: https://github.com/inventree/InvenTree/pull/3273
        """
        self.assertTrue(
            offload_task(
                'dummy_tasks.stock',
                item=StockItem.objects.get(pk=1),
                loc=StockLocation.objects.get(pk=1),
                force_async=True,
            )
        )

        self.assertTrue(
            offload_task('dummy_task.numbers', 1, 2, 3, 4, 5, force_async=True)
        )

        # Offload a dummy task, but force sync
        # This should fail, because the function does not exist
        with self.assertLogs(logger='inventree', level='WARNING') as log:
            self.assertFalse(
                offload_task('dummy_task.numbers', 1, 1, 1, force_sync=True)
            )

            self.assertIn('Malformed function path', str(log.output))

        # Offload dummy task with a Part instance
        # This should succeed, ensuring that the Part instance is correctly pickled
        self.assertTrue(
            offload_task(
                'dummy_tasks.parts',
                part=Part.objects.get(pk=1),
                cat=PartCategory.objects.get(pk=1),
                force_async=True,
            )
        )

    def test_daily_holdoff(self):
        """Tests for daily task holdoff helper functions."""
        import InvenTree.tasks

        with self.assertLogs(logger='inventree', level='INFO') as cm:
            # With a non-positive interval, task will not run
            result = InvenTree.tasks.check_daily_holdoff('some_task', 0)
            self.assertFalse(result)
            self.assertIn('Specified interval', str(cm.output))

        with self.assertLogs(logger='inventree', level='INFO') as cm:
            # First call should run without issue
            result = InvenTree.tasks.check_daily_holdoff('dummy_task')
            self.assertTrue(result)
            self.assertIn("Logging task attempt for 'dummy_task'", str(cm.output))

        with self.assertLogs(logger='inventree', level='INFO') as cm:
            # An attempt has been logged, but it is too recent
            result = InvenTree.tasks.check_daily_holdoff('dummy_task')
            self.assertFalse(result)
            self.assertIn(
                "Last attempt for 'dummy_task' was too recent", str(cm.output)
            )

        # Mark last attempt a few days ago - should now return True
        t_old = datetime.now() - timedelta(days=3)
        t_old = t_old.isoformat()
        InvenTreeSetting.set_setting('_dummy_task_ATTEMPT', t_old, None)

        result = InvenTree.tasks.check_daily_holdoff('dummy_task', 5)
        self.assertTrue(result)

        # Last attempt should have been updated
        self.assertNotEqual(
            t_old, InvenTreeSetting.get_setting('_dummy_task_ATTEMPT', '', cache=False)
        )

        # Last attempt should prevent us now
        with self.assertLogs(logger='inventree', level='INFO') as cm:
            result = InvenTree.tasks.check_daily_holdoff('dummy_task')
            self.assertFalse(result)
            self.assertIn(
                "Last attempt for 'dummy_task' was too recent", str(cm.output)
            )

        # Configure so a task was successful too recently
        InvenTreeSetting.set_setting('_dummy_task_ATTEMPT', t_old, None)
        InvenTreeSetting.set_setting('_dummy_task_SUCCESS', t_old, None)

        with self.assertLogs(logger='inventree', level='INFO') as cm:
            result = InvenTree.tasks.check_daily_holdoff('dummy_task', 7)
            self.assertFalse(result)
            self.assertIn('Last successful run for', str(cm.output))

            result = InvenTree.tasks.check_daily_holdoff('dummy_task', 2)
            self.assertTrue(result)


class BarcodeMixinTest(InvenTreeTestCase):
    """Tests for the InvenTreeBarcodeMixin mixin class."""

    def test_barcode_model_type(self):
        """Test that the barcode_model_type property works for each class."""
        from part.models import Part
        from stock.models import StockItem, StockLocation

        self.assertEqual(Part.barcode_model_type(), 'part')
        self.assertEqual(StockItem.barcode_model_type(), 'stockitem')
        self.assertEqual(StockLocation.barcode_model_type(), 'stocklocation')

    def test_barcode_hash(self):
        """Test that the barcode hashing function provides correct results."""
        # Test multiple values for the hashing function
        # This is to ensure that the hash function is always "backwards compatible"
        hashing_tests = {
            'abcdefg': '7ac66c0f148de9519b8bd264312c4d64',
            'ABCDEFG': 'bb747b3df3130fe1ca4afa93fb7d97c9',
            '1234567': 'fcea920f7412b5da7be0cf42b8c93759',
            '{"part": 17, "stockitem": 12}': 'c88c11ed0628eb7fef0d59b098b96975',
        }

        for barcode, hash in hashing_tests.items():
            self.assertEqual(InvenTree.helpers.hash_barcode(barcode), hash)


class SanitizerTest(TestCase):
    """Simple tests for sanitizer functions."""

    def test_svg_sanitizer(self):
        """Test that SVGs are sanitized accordingly."""
        valid_string = """<svg xmlns="http://www.w3.org/2000/svg" version="1.1" id="svg2" height="400" width="400">{0}
        <path id="path1" d="m -151.78571,359.62883 v 112.76373 l 97.068507,-56.04253 V 303.14815 Z" style="fill:#ddbc91;"></path>
        </svg>"""
        dangerous_string = valid_string.format('<script>alert();</script>')

        # Test that valid string
        self.assertEqual(valid_string, sanitize_svg(valid_string))

        # Test that invalid string is cleaned
        self.assertNotEqual(dangerous_string, sanitize_svg(dangerous_string))


class MagicLoginTest(InvenTreeTestCase):
    """Test magic login token generation."""

    def test_generation(self):
        """Test that magic login tokens are generated correctly."""
        # User does not exists
        resp = self.client.post(reverse('sesame-generate'), {'email': 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {'status': 'ok'})
        self.assertEqual(len(mail.outbox), 0)

        # User exists
        resp = self.client.post(reverse('sesame-generate'), {'email': self.user.email})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {'status': 'ok'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[InvenTree] Log in to the app')

        # Check that the token is in the email
        self.assertTrue('http://testserver/api/email/login/' in mail.outbox[0].body)
        token = mail.outbox[0].body.split('/')[-1].split('\n')[0][8:]
        self.assertEqual(get_user(token), self.user)

        # Log user off
        self.client.logout()

        # Check that the login works
        resp = self.client.get(reverse('sesame-login') + '?sesame=' + token)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/api/auth/login-redirect/')
        # And we should be logged in again
        self.assertEqual(resp.wsgi_request.user, self.user)


# TODO - refactor to not use CUI
@tag('cui')
class MaintenanceModeTest(InvenTreeTestCase):
    """Unit tests for maintenance mode."""

    def test_basic(self):
        """Test basic maintenance mode operation."""
        for value in [False, True, False]:
            set_maintenance_mode(value)
            self.assertEqual(get_maintenance_mode(), value)

        # API request is blocked in maintenance mode
        set_maintenance_mode(True)

        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 503)

        set_maintenance_mode(False)

        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)

    def test_timestamp(self):
        """Test that the timestamp value is interpreted correctly."""
        KEY = '_MAINTENANCE_MODE'

        # Deleting the setting means maintenance mode is off
        InvenTreeSetting.objects.filter(key=KEY).delete()

        self.assertFalse(get_maintenance_mode())

        def set_timestamp(value):
            InvenTreeSetting.set_setting(KEY, value, None)

        # Test blank value
        set_timestamp('')
        self.assertFalse(get_maintenance_mode())

        # Test timestamp in the past
        ts = datetime.now() - timedelta(minutes=10)
        set_timestamp(ts.isoformat())
        self.assertFalse(get_maintenance_mode())

        # Test timestamp in the future
        ts = datetime.now() + timedelta(minutes=10)
        set_timestamp(ts.isoformat())
        self.assertTrue(get_maintenance_mode())

        # Set to false, check for empty string
        set_maintenance_mode(False)
        self.assertFalse(get_maintenance_mode())
        self.assertEqual(InvenTreeSetting.get_setting(KEY, None), '')


class ClassValidationMixinTest(TestCase):
    """Tests for the ClassValidationMixin class."""

    class BaseTestClass(ClassValidationMixin):
        """A valid class that inherits from ClassValidationMixin."""

        NAME: str

        def test(self):
            """Test function."""
            pass

        def test1(self):
            """Test function."""
            pass

        def test2(self):
            """Test function."""
            pass

        required_attributes = ['NAME']
        required_overrides = [test, [test1, test2]]

    class InvalidClass:
        """An invalid class that does not inherit from ClassValidationMixin."""

        pass

    def test_valid_class(self):
        """Test that a valid class passes the validation."""

        class TestClass(self.BaseTestClass):
            """A valid class that inherits from BaseTestClass."""

            NAME = 'Test'

            def test(self):
                """Test function."""
                pass

            def test2(self):
                """Test function."""
                pass

        TestClass.validate()

    def test_invalid_class(self):
        """Test that an invalid class fails the validation."""

        class TestClass1(self.BaseTestClass):
            """A bad class that inherits from BaseTestClass."""

        with self.assertRaisesRegex(
            NotImplementedError,
            r'\'<.*TestClass1\'>\' did not provide the following attributes: NAME and did not override the required attributes: test, one of test1 or test2',
        ):
            TestClass1.validate()

        class TestClass2(self.BaseTestClass):
            """A bad class that inherits from BaseTestClass."""

            NAME = 'Test'

            def test2(self):
                """Test function."""
                pass

        with self.assertRaisesRegex(
            NotImplementedError,
            r'\'<.*TestClass2\'>\' did not override the required attributes: test',
        ):
            TestClass2.validate()


class ClassProviderMixinTest(TestCase):
    """Tests for the ClassProviderMixin class."""

    class TestClass(ClassProviderMixin):
        """This class is a dummy class to test the ClassProviderMixin."""

        pass

    def test_get_provider_file(self):
        """Test the get_provider_file function."""
        self.assertEqual(self.TestClass.get_provider_file(), __file__)

    def test_provider_plugin(self):
        """Test the provider_plugin function."""
        self.assertEqual(self.TestClass.get_provider_plugin(), None)

    def test_get_is_builtin(self):
        """Test the get_is_builtin function."""
        self.assertTrue(self.TestClass.get_is_builtin())
