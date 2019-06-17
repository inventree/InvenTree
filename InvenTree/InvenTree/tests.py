from django.test import TestCase
import django.core.exceptions as django_exceptions

from .validators import validate_overage, validate_part_name

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
