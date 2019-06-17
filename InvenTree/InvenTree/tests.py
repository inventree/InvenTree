from django.test import TestCase
import django.core.exceptions as django_exceptions

from .validators import validate_overage, validate_part_name
from . import helpers


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


class TestQuoteWrap(TestCase):
    """ Tests for string wrapping """

    def test_single(self):

        self.assertEqual(helpers.WrapWithQuotes('hello'), '"hello"')
        self.assertEqual(helpers.WrapWithQuotes('hello"'), '"hello"')


class TestMakeBarcoede(TestCase):
    """ Tests for barcode string creation """

    def test_barcode(self):

        data = {
            'animal': 'cat',
            'legs': 3,
            'noise': 'purr'
        }

        bc = helpers.MakeBarcode("part", 3, "www.google.com", data)

        self.assertIn('animal', bc)
        self.assertIn('tool', bc)
        self.assertIn('"tool": "InvenTree"', bc)


class TestDownloadFile(TestCase):


    def test_download(self):
        helpers.DownloadFile("hello world", "out.txt")
        helpers.DownloadFile(bytes("hello world".encode("utf8")), "out.bin")
