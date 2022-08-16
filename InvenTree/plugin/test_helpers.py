"""Unit tests for helpers.py."""

from django.test import TestCase

from .helpers import get_module_meta, render_template


class HelperTests(TestCase):
    """Tests for helpers."""

    def test_render_template(self):
        """Check if render_template helper works."""
        class ErrorSource:
            slug = 'sampleplg'

        # working sample
        response = render_template(ErrorSource(), 'sample/sample.html', {'abc': 123})
        self.assertEqual(response, '<h1>123</h1>\n')

        # Wrong sample
        response = render_template(ErrorSource(), 'sample/wrongsample.html', {'abc': 123})
        self.assertTrue('lert alert-block alert-danger' in response)
        self.assertTrue('Template file <em>sample/wrongsample.html</em>' in response)

    def test_get_module_meta(self):
        """Test for get_module_meta."""

        # We need a stable, known good that will be in enviroment for sure
        # and it can't be stdlib because does might differ depending on the abstraction layer
        # and version
        meta = get_module_meta('django')

        # Lets just hope they do not change the name or author
        self.assertEqual(meta['Name'], 'Django')
        self.assertEqual(meta['Author'], 'Django Software Foundation')
