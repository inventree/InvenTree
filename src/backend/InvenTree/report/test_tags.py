"""Test for custom report tags."""

from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.safestring import SafeString

from djmoney.money import Money
from PIL import Image

from common.models import InvenTreeSetting, Parameter, ParameterTemplate
from InvenTree.config import get_testfolder_dir
from InvenTree.unit_test import InvenTreeTestCase
from part.models import Part  # TODO fix import: PartParameter, PartParameterTemplate
from part.test_api import PartImageTestMixin
from report.templatetags import barcode as barcode_tags
from report.templatetags import report as report_tags


class ReportTagTest(PartImageTestMixin, InvenTreeTestCase):
    """Unit tests for the report template tags."""

    def debug_mode(self, value: bool):
        """Enable or disable debug mode for reports."""
        InvenTreeSetting.set_setting('REPORT_DEBUG_MODE', value, change_user=None)

    def test_getindex(self):
        """Tests for the 'getindex' template tag."""
        fn = report_tags.getindex
        data = [1, 2, 3, 4, 5, 6]

        # Out of bounds or invalid
        self.assertEqual(fn(data, -1), None)
        self.assertEqual(fn(data, 99), None)
        self.assertEqual(fn(data, 'xx'), None)

        for idx in range(len(data)):
            self.assertEqual(fn(data, idx), data[idx])

    def test_getkey(self):
        """Tests for the 'getkey' template tag."""
        data = {'hello': 'world', 'foo': 'bar', 'with spaces': 'withoutspaces', 1: 2}

        # Valid case
        for k, v in data.items():
            self.assertEqual(report_tags.getkey(data, k), v)

        # Error case
        self.assertEqual(
            None, report_tags.getkey('not a container', 'not-a-key', 'a value')
        )

    def test_asset(self):
        """Tests for asset files."""
        # Test that an error is raised if the file does not exist
        for b in [True, False]:
            self.debug_mode(b)

            with self.assertRaises(FileNotFoundError):
                report_tags.asset('bad_file.txt')

        # Create an asset file
        asset_dir = settings.MEDIA_ROOT.joinpath('report', 'assets')
        asset_dir.mkdir(parents=True, exist_ok=True)
        asset_path = asset_dir.joinpath('test.txt')

        asset_path.write_text('dummy data')

        self.debug_mode(True)
        asset = report_tags.asset('test.txt')
        self.assertEqual(asset, '/media/report/assets/test.txt')

        # Ensure that a 'safe string' also works
        asset = report_tags.asset(SafeString('test.txt'))
        self.assertEqual(asset, '/media/report/assets/test.txt')

        self.debug_mode(False)
        asset = report_tags.asset('test.txt')
        self.assertEqual(asset, f'file://{asset_dir}/test.txt')

    def test_uploaded_image(self):
        """Tests for retrieving uploaded images."""
        # Test for a missing image
        for b in [True, False]:
            self.debug_mode(b)

            with self.assertRaises(FileNotFoundError):
                report_tags.uploaded_image(
                    '/part/something/test.png', replace_missing=False
                )

            img = str(report_tags.uploaded_image('/part/something/other.png'))

            if b:
                self.assertIn('blank_image.png', img)
            else:
                self.assertIn('data:image/png;charset=utf-8;base64,', img)

        # Create a dummy image
        img_path = 'part/images/'
        img_path = settings.MEDIA_ROOT.joinpath(img_path)
        img_file = img_path.joinpath('test.jpg')

        img_path.mkdir(parents=True, exist_ok=True)
        img_file.write_text('dummy data')

        # Test in debug mode. Returns blank image as dummy file is not a valid image
        self.debug_mode(True)
        img = report_tags.uploaded_image('part/images/test.jpg')
        self.assertEqual(img, '/static/img/blank_image.png')

        # Now, let's create a proper image
        img = Image.new('RGB', (128, 128), color='RED')
        img.save(img_file)

        # Try again
        img = report_tags.uploaded_image('part/images/test.jpg')
        self.assertEqual(img, '/media/part/images/test.jpg')

        # Ensure that a 'safe string' also works
        img = report_tags.uploaded_image(SafeString('part/images/test.jpg'))
        self.assertEqual(img, '/media/part/images/test.jpg')

        self.debug_mode(False)
        img = report_tags.uploaded_image('part/images/test.jpg')
        self.assertTrue(img.startswith('data:image/png;charset=utf-8;base64,'))

        img = report_tags.uploaded_image(SafeString('part/images/test.jpg'))
        self.assertTrue(img.startswith('data:image/png;charset=utf-8;base64,'))

        # Check width, height, rotate
        img = report_tags.uploaded_image(
            'part/images/test.jpg', width=100, height=200, rotate=90
        )
        self.assertTrue(img.startswith('data:image/png;charset=utf-8;base64,'))

        img = report_tags.uploaded_image('part/images/test.jpg', width=100)
        self.assertTrue(img.startswith('data:image/png;charset=utf-8;base64,'))

        # Invalid args
        img = report_tags.uploaded_image(
            'part/images/test.jpg', width='a', height='b', rotate='c'
        )
        self.assertTrue(img.startswith('data:image/png;charset=utf-8;base64,'))

    def test_part_image(self):
        """Unit tests for the 'part_image' tag."""
        with self.assertRaises(TypeError):
            report_tags.part_image(None)

        obj = Part.objects.create(name='test', description='test')
        self.create_test_image()
        obj.refresh_from_db()

        report_tags.part_image(obj, preview=True)
        report_tags.part_image(obj, thumbnail=True)

    def test_company_image(self):
        """Unit tests for the 'company_image' tag."""
        with self.assertRaises(TypeError):
            report_tags.company_image(None)
        with self.assertRaises(TypeError):
            report_tags.company_image(None, preview=True)
        with self.assertRaises(TypeError):
            report_tags.company_image(None, thumbnail=True)

    def test_internal_link(self):
        """Unit tests for the 'internal_link' tag."""
        # Test with a valid object
        obj = Part.objects.create(name='test', description='test')
        self.assertEqual(report_tags.internal_link(obj, 'test123'), 'test123')
        link = report_tags.internal_link(obj.get_absolute_url(), 'test')

        # Test might return one of two results, depending on test env
        # If INVENTREE_SITE_URL is not set in the CI environment, the link will be relative
        options = [
            f'<a href="http://localhost:8000/web/part/{obj.pk}">test</a>',
            f'<a href="/web/part/{obj.pk}">test</a>',
        ]

        self.assertIn(link, options)

        # Test with an invalid object
        link = report_tags.internal_link(None, None)
        self.assertEqual(link, 'None')

    def test_logo_image(self):
        """Unit tests for the 'logo_image' tag."""
        # By default, should return the core InvenTree logo
        for b in [True, False]:
            self.debug_mode(b)
            logo = report_tags.logo_image()
            self.assertIn('inventree.png', logo)

    def test_maths_tags(self):
        """Simple tests for mathematical operator tags."""
        self.assertEqual(report_tags.add(1, 2), 3)
        self.assertEqual(report_tags.add('-33', '33'), 0)
        self.assertEqual(report_tags.add(4.5, Decimal(4.5), cast=float), 9.0)
        self.assertEqual(report_tags.subtract(10, 4.2, cast=float), 5.8)
        self.assertEqual(report_tags.multiply(2.3, 4, cast=str), '9.2')
        self.assertEqual(report_tags.multiply('-2', 4), -8)
        self.assertEqual(report_tags.divide(100, 5), 20)

        self.assertEqual(report_tags.modulo(10, 3), 1)
        self.assertEqual(report_tags.modulo('10', '4'), 2)

        with self.assertRaises(ValidationError):
            report_tags.divide(100, 0)

    def test_maths_tags_with_strings(self):
        """Tests for mathematical operator tags with string inputs."""
        self.assertEqual(report_tags.add(Decimal('10'), '20'), 30)
        self.assertEqual(report_tags.subtract('50.5', '20.2'), Decimal('30.3'))
        self.assertEqual(report_tags.multiply(3.0000000000000, '7'), 21)

        result = report_tags.divide(100, Decimal('4'), cast=int)
        self.assertEqual(result, 25)
        self.assertIsInstance(result, int)

    def test_maths_tags_with_decimal(self):
        """Tests for mathematical operator tags with Decimal inputs."""
        from decimal import Decimal

        self.assertEqual(
            report_tags.add(Decimal('1.1'), Decimal('2.2')), Decimal('3.3')
        )
        self.assertEqual(
            report_tags.subtract(Decimal('5.5'), Decimal('2.2')), Decimal('3.3')
        )
        self.assertEqual(report_tags.multiply(Decimal('3.0'), 4), Decimal('12.0'))
        self.assertEqual(
            report_tags.divide(Decimal('10.0'), Decimal('2.000')), Decimal('5.0')
        )

        self.assertEqual(report_tags.multiply(3.3, Decimal('2.0')), Decimal('6.6'))

    def test_maths_tags_with_money(self):
        """Tests for mathematical operator tags with Money inputs."""
        m1 = Money(100, 'USD')
        m2 = Money(50, 'USD')

        self.assertEqual(report_tags.add(m1, m2), Money(150, 'USD'))
        self.assertEqual(report_tags.subtract(m1, m2), Money(50, 'USD'))
        self.assertEqual(report_tags.multiply(m2, 3), Money(150, 'USD'))
        self.assertEqual(report_tags.multiply(-3, m2), Money(-150, 'USD'))
        self.assertEqual(report_tags.divide(m1, '4'), Money(25, 'USD'))

        result = report_tags.divide(Money(1000, 'GBP'), 4)
        self.assertIsInstance(result, Money)

    def test_maths_tags_invalid(self):
        """Tests for mathematical operator tags with invalid inputs."""
        with self.assertRaises(ValidationError):
            report_tags.add('abc', 10)

        with self.assertRaises(ValidationError):
            report_tags.subtract(50, 'xyz')

        with self.assertRaises(ValidationError):
            report_tags.multiply('foo', 'bar')

        with self.assertRaises(ValidationError):
            report_tags.divide('100', 'baz')

    def test_number_tags(self):
        """Simple tests for number formatting tags."""
        fn = report_tags.format_number

        # Passing None should raise an error
        with self.assertRaises(ValidationError):
            fn(None)

        for i in [1, '1', '1.0000', '  1  ']:
            self.assertEqual(fn(i), '1')

        for x in ['10.000000', '  10  ', 10.000000, 10]:
            self.assertEqual(fn(x), '10')

        self.assertEqual(fn(1234), '1234')
        self.assertEqual(fn(1234.5678, decimal_places=0), '1235')
        self.assertEqual(fn(1234.5678, decimal_places=1), '1234.6')
        self.assertEqual(fn(1234.5678, decimal_places=2), '1234.57')
        self.assertEqual(fn(1234.5678, decimal_places=3), '1234.568')
        self.assertEqual(fn(-9999.5678, decimal_places=2, separator=','), '-9,999.57')
        self.assertEqual(
            fn(9988776655.4321, integer=True, separator=' '), '9 988 776 655'
        )

        # Test with multiplier
        self.assertEqual(fn(1000, multiplier=1.5), '1500')

        # Failure cases
        self.assertEqual(fn('abc'), 'abc')
        self.assertEqual(fn(1234.456, decimal_places='a'), '1234.456')
        self.assertEqual(fn(1234.456, leading='a'), '1234.456')

    @override_settings(TIME_ZONE='America/New_York')
    def test_date_tags(self):
        """Test for date formatting tags.

        - Source timezone is Australia/Sydney
        - Server timezone is America/New York
        """
        time = timezone.datetime(
            year=2024,
            month=3,
            day=13,
            hour=12,
            minute=30,
            second=0,
            tzinfo=ZoneInfo('Australia/Sydney'),
        )

        # Format a set of tests: timezone, format, expected
        tests = [
            (None, None, '2024-03-12T21:30:00-04:00'),
            (None, '%d-%m-%y', '12-03-24'),
            ('UTC', None, '2024-03-13T01:30:00+00:00'),
            ('UTC', '%d-%B-%Y', '13-March-2024'),
            ('Europe/Amsterdam', None, '2024-03-13T02:30:00+01:00'),
            ('Europe/Amsterdam', '%y-%m-%d %H:%M', '24-03-13 02:30'),
        ]

        for tz, fmt, expected in tests:
            result = report_tags.format_datetime(time, tz, fmt)
            self.assertEqual(result, expected)

    def test_icon(self):
        """Test the icon template tag."""
        for icon in [None, '', 'not:the-correct-format', 'any-non-existent-icon']:
            self.assertEqual(report_tags.icon(icon), '')

        self.assertEqual(
            report_tags.icon('ti:package:outline'),
            f'<i class="icon " style="font-family: inventree-icon-font-ti">{chr(int("eaff", 16))}</i>',
        )
        self.assertEqual(
            report_tags.icon(
                'ti:package:outline', **{'class': 'my-custom-class my-seconds-class'}
            ),
            f'<i class="icon my-custom-class my-seconds-class" style="font-family: inventree-icon-font-ti">{chr(int("eaff", 16))}</i>',
        )

    def test_include_icon_fonts(self):
        """Test the include_icon_fonts template tag."""
        # ttf
        style = report_tags.include_icon_fonts()

        self.assertIn('@font-face {', style)
        self.assertIn("font-family: 'inventree-icon-font-ti';", style)
        self.assertIn('tabler-icons/tabler-icons.ttf', style)
        self.assertIn('.icon {', style)

        # woff
        style = report_tags.include_icon_fonts(woff=True)
        self.assertIn('tabler-icons/tabler-icons.woff', style)

    def test_filter_queryset(self):
        """Test the filter_queryset template tag."""
        # Test with a valid queryset
        qs = Part.objects.all()
        self.assertEqual(
            list(report_tags.filter_queryset(qs, name='test')),
            list(qs.filter(name='test')),
        )

        # Test with an invalid queryset
        self.assertEqual(report_tags.filter_queryset(None, name='test'), None)

    def test_filter_db_model(self):
        """Test the filter_db_model template tag."""
        self.assertEqual(list(report_tags.filter_db_model('part.part')), [])

        part = Part.objects.create(name='test', description='test')
        self.assertEqual(
            list(report_tags.filter_db_model('part.part', name='test')), [part]
        )
        self.assertEqual(
            list(report_tags.filter_db_model('part.part', name='test1')), []
        )

        # Invalid model
        self.assertEqual(report_tags.filter_db_model('part.abcd'), None)
        self.assertEqual(report_tags.filter_db_model(''), None)

    def test_encode_svg_image(self):
        """Test the encode_svg_image template tag."""
        # Generate smallest possible SVG for testing
        svg_path = get_testfolder_dir() / 'part_image_123abc.png'
        with open(svg_path, 'w', encoding='utf8') as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg>')

        # Test with a valid SVG file
        svg = report_tags.encode_svg_image(svg_path)
        self.assertTrue(svg.startswith('data:image/svg+xml;charset=utf-8;base64,'))
        self.assertIn('svg', svg)
        self.assertEqual(
            'data:image/svg+xml;charset=utf-8;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmc+',
            svg,
        )

    def test_part_parameter(self):
        """Test the part_parameter template tag."""
        # Test with a valid part
        part = Part.objects.create(name='test', description='test')
        t1 = ParameterTemplate.objects.create(name='Template 1', units='mm')

        content_type = ContentType.objects.get_for_model(Part)
        parameter = Parameter.objects.create(
            model_type=content_type, model_id=part.pk, template=t1, data='test'
        )

        # Note, use the 'parameter' and 'part_parameter' tags interchangeably here
        self.assertEqual(report_tags.part_parameter(part, 'name'), None)
        self.assertEqual(report_tags.parameter(part, 'Template 1'), parameter)

        # Test with a null part
        with self.assertRaises(ValueError):
            report_tags.parameter(None, 'name')

        # Test with an invalid model type
        with self.assertRaises(TypeError):
            report_tags.parameter(parameter, 'name')

    def test_render_currency(self):
        """Test the render_currency template tag."""
        m = Money(1234.56, 'USD')
        exp_m = '$1,234.56'

        self.assertEqual(report_tags.render_currency(m), exp_m)
        self.assertEqual(report_tags.render_currency(m, currency='EUR'), exp_m)
        self.assertEqual(report_tags.render_currency(m, decimal_places=3), '$1,234.560')
        self.assertEqual(
            report_tags.render_currency(
                Money(1234, 'USD'), currency='EUR', min_decimal_places=3
            ),
            '$1,234.000',
        )
        self.assertEqual(
            report_tags.render_currency(
                Money(1234, 'USD'), currency='EUR', max_decimal_places=1
            ),
            '$1,234.0',
        )

        # Test with non-currency values
        self.assertEqual(
            report_tags.render_currency(1234.45, currency='USD', decimal_places=2),
            '$1,234.45',
        )

        # Test with an invalid amount
        with self.assertRaises(ValidationError):
            report_tags.render_currency('abc', currency='-')

        with self.assertRaises(ValidationError):
            report_tags.render_currency(m, multiplier='quork')

        self.assertEqual(report_tags.render_currency(m, decimal_places='a'), exp_m)
        self.assertEqual(report_tags.render_currency(m, min_decimal_places='a'), exp_m)
        self.assertEqual(report_tags.render_currency(m, max_decimal_places='a'), exp_m)

    def test_create_currency(self):
        """Test the create_currency template tag."""
        m = report_tags.create_currency(1000, 'USD')
        self.assertIsInstance(m, Money)
        self.assertEqual(m.amount, Decimal('1000'))
        self.assertEqual(str(m.currency), 'USD')

        # Test with invalid currency code
        with self.assertRaises(ValidationError):
            report_tags.create_currency(1000, 'QWERTY')

        # Test with invalid amount
        with self.assertRaises(ValidationError):
            report_tags.create_currency('abc', 'USD')

    def test_convert_currency(self):
        """Test the convert_currency template tag."""
        from djmoney.contrib.exchange.models import ExchangeBackend, Rate

        # Generate some dummy exchange rates
        rates = {'AUD': 1.5, 'CAD': 1.7, 'GBP': 0.9, 'USD': 1.0}

        # Create a dummy backend
        ExchangeBackend.objects.create(name='InvenTreeExchange', base_currency='USD')

        backend = ExchangeBackend.objects.get(name='InvenTreeExchange')

        items = []

        for currency, rate in rates.items():
            items.append(Rate(currency=currency, value=rate, backend=backend))

        Rate.objects.bulk_create(items)

        m = report_tags.create_currency(1000, 'GBP')

        # Test with valid conversion
        converted = report_tags.convert_currency(m, 'CAD')
        self.assertIsInstance(converted, Money)
        self.assertEqual(str(converted.currency), 'CAD')

        # Test with invalid currency code
        with self.assertRaises(ValidationError):
            report_tags.convert_currency(m, 'QWERTY')

        # Test with missing exchange rate
        with self.assertRaises(ValidationError):
            report_tags.convert_currency(m, 'AFD')

    def test_render_html_text(self):
        """Test the render_html_text template tag."""
        # Test with a valid text
        self.assertEqual(report_tags.render_html_text('hello world'), 'hello world')
        self.assertEqual(
            report_tags.render_html_text('<b>hello world</b>'), '<b>hello world</b>'
        )
        self.assertEqual(
            report_tags.render_html_text('hello world', bold=True),
            '<strong>hello world</strong>',
        )
        self.assertEqual(
            report_tags.render_html_text('hello world', italic=True),
            '<em>hello world</em>',
        )
        self.assertEqual(
            report_tags.render_html_text('hello world', heading='h1'),
            '<h1>hello world</h1>',
        )

    def test_format_date(self):
        """Test the format_date template tag."""
        # Test with a valid date
        date = timezone.datetime(year=2024, month=3, day=13)
        self.assertEqual(report_tags.format_date(date), '2024-03-13')
        self.assertEqual(report_tags.format_date(date, fmt='%d-%m-%y'), '13-03-24')

        # Test with an invalid date
        self.assertEqual(report_tags.format_date('abc'), 'abc')
        self.assertEqual(report_tags.format_date(date, fmt='a'), 'a')


class BarcodeTagTest(TestCase):
    """Unit tests for the barcode template tags."""

    def test_barcode(self):
        """Test the barcode generation tag."""
        barcode = barcode_tags.barcode('12345')

        self.assertIsInstance(barcode, str)
        self.assertTrue(barcode.startswith('data:image/png;'))

        # Try with a different format
        barcode = barcode_tags.barcode('99999', format='BMP')
        self.assertIsInstance(barcode, str)
        self.assertTrue(barcode.startswith('data:image/bmp;'))

        # Test empty tag
        with self.assertRaises(ValueError):
            barcode_tags.barcode('')

    def test_qrcode(self):
        """Test the qrcode generation tag."""
        # Test with default settings
        qrcode = barcode_tags.qrcode('hello world')
        self.assertIsInstance(qrcode, str)
        self.assertTrue(qrcode.startswith('data:image/png;'))
        self.assertEqual(len(qrcode), 700)

        # Generate a much larger qrcode
        qrcode = barcode_tags.qrcode(
            'hello_world', version=2, box_size=50, format='BMP'
        )
        self.assertIsInstance(qrcode, str)
        self.assertTrue(qrcode.startswith('data:image/bmp;'))
        self.assertEqual(len(qrcode), 309720)

        # Test empty tag
        with self.assertRaises(ValueError):
            barcode_tags.qrcode('')

    def test_clean_barcode(self):
        """Test clean_barcode tag."""
        self.assertEqual(barcode_tags.clean_barcode('hello world'), 'hello world')
        self.assertEqual(barcode_tags.clean_barcode('`hello world`'), 'hello world')

        with self.assertRaises(ValidationError):
            self.assertEqual(
                barcode_tags.clean_barcode('<b>hello world</b>'), 'hello world'
            )

    def test_datamatrix(self):
        """Test the datamatrix generation tag."""
        # Test with default settings
        datamatrix = barcode_tags.datamatrix('hello world')
        self.assertEqual(
            datamatrix,
            'data:image/png;charset=utf-8;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAIAAADZrBkAAAAAlElEQVR4nJ1TQQ7AIAgri///cncw6wroEseBgEFbCgZJnNsFICKOPAAIjeSM5T11IznK5f5WRMgnkhP9JfCcTC/MxFZ5hxLOgqrn3o/z/OqtsNpdSL31Iu9W4Dq8Sulu+q5Nuqa3XYOdnuidlICPpXhZVBruyzAKSZehT+yNlzvZQcq6JiW7Ni592swf/43kdlDfdgMk1eOtR7kWpAAAAABJRU5ErkJggg==',
        )

        datamatrix = barcode_tags.datamatrix(
            'hello world', border=3, fill_color='red', back_color='blue'
        )
        self.assertEqual(
            datamatrix,
            'data:image/png;charset=utf-8;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAIAAABL1vtsAAAAqElEQVR4nN1UQQ6AMAgrxv9/GQ9mpJYSY/QkBxM3KLUUA0i8i+1l/dcQiXj09CwSEU2aQJ7nE8ou2faVUXoPZSEkq+dZKVxWg4UqxUHnVdkp6IdwMXMulGvzNBDMk4WwPSrUF3LNnQNZBJmOsZaVXa44QSEKnvWb5mIgKon1E1H6aPyOcIa15uhONP9aR4hSCiGmYAoYpj4uO+vK4+ybMhr8Nkjmn/z4Dvoldi8uJu4iAAAAAElFTkSuQmCC',
        )

        # Test empty tag
        with self.assertRaises(ValueError):
            barcode_tags.datamatrix('')

        # Failure cases with wrong args
        datamatrix = barcode_tags.datamatrix(
            'hello world', border='abc', fill_color='aaaaaaa', back_color='aaaaaaa'
        )
        self.assertEqual(
            datamatrix,
            'data:image/png;charset=utf-8;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAIAAADZrBkAAAAAlElEQVR4nJ1TQQ7AIAgri///cncw6wroEseBgEFbCgZJnNsFICKOPAAIjeSM5T11IznK5f5WRMgnkhP9JfCcTC/MxFZ5hxLOgqrn3o/z/OqtsNpdSL31Iu9W4Dq8Sulu+q5Nuqa3XYOdnuidlICPpXhZVBruyzAKSZehT+yNlzvZQcq6JiW7Ni592swf/43kdlDfdgMk1eOtR7kWpAAAAABJRU5ErkJggg==',
        )
