"""Unit tests for helpers.py"""

from django.test import TestCase

from .helpers import render_template


class HelperTests(TestCase):
    """Tests for helpers"""

    def test_render_template(self):
        """Check if render_template helper works"""
        class ErrorSource:
            slug = 'sampleplg'

        # working sample
        response = render_template(ErrorSource(), 'sample/sample.html', {'abc': 123})
        self.assertEqual(response, '<h1>123</h1>\n')

        # Wrong sample
        response = render_template(ErrorSource(), 'sample/wrongsample.html', {'abc': 123})
        self.assertTrue('lert alert-block alert-danger' in response)
        self.assertTrue('Template file <em>sample/wrongsample.html</em>' in response)
