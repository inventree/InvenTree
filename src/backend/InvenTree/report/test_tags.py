"""Test for custom report tags."""

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.safestring import SafeString

from backend.InvenTree.common.models import InvenTreeSetting
from backend.InvenTree.report.templatetags import barcode as barcode_tags
from backend.InvenTree.report.templatetags import report as report_tags
from PIL import Image
from zoneinfo import ZoneInfo


class ReportTagTest(TestCase):
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

        for k, v in data.items():
            self.assertEqual(report_tags.getkey(data, k), v)

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

    def test_part_image(self):
        """Unit tests for the 'part_image' tag."""
        with self.assertRaises(TypeError):
            report_tags.part_image(None)

    def test_company_image(self):
        """Unit tests for the 'company_image' tag."""
        with self.assertRaises(TypeError):
            report_tags.company_image(None)

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
        self.assertEqual(report_tags.subtract(10, 4.2), 5.8)
        self.assertEqual(report_tags.multiply(2.3, 4), 9.2)
        self.assertEqual(report_tags.divide(100, 5), 20)

    def test_number_tags(self):
        """Simple tests for number formatting tags."""
        fn = report_tags.format_number

        self.assertEqual(fn(1234), '1234')
        self.assertEqual(fn(1234.5678, decimal_places=2), '1234.57')
        self.assertEqual(fn(1234.5678, decimal_places=3), '1234.568')
        self.assertEqual(fn(-9999.5678, decimal_places=2, separator=','), '-9,999.57')
        self.assertEqual(
            fn(9988776655.4321, integer=True, separator=' '), '9 988 776 655'
        )

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
        style = report_tags.include_icon_fonts()

        self.assertIn('@font-face {', style)
        self.assertIn("font-family: 'inventree-icon-font-ti';", style)
        self.assertIn('tabler-icons/tabler-icons.ttf', style)
        self.assertIn('.icon {', style)


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


#
