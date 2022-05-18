"""
Unit tests for the 'locate' plugin mixin class
"""

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase

from plugin.registry import registry


class LocatePluginTests(InvenTreeAPITestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
    ]

    def test_installed(self):
        """Test that a locate plugin is actually installed"""

        plugins = registry.with_mixin('locate')

        self.assertTrue(len(plugins) > 0)

        self.assertTrue('samplelocate' in [p.slug for p in plugins])

    def test_locate_fail(self):
        """Test various API failure modes"""
        
        url = reverse('api-locate-plugin')

        # Post without a plugin
        response = self.post(
            url,
            {},
            expected_code=400
        )

        self.assertIn("'plugin' field must be supplied", str(response.data))

        # Post with a plugin that does not exist, or is invalid
        for slug in ['xyz', 'event', 'plugin']:
            response = self.post(
                url,
                {
                    'plugin': slug,
                },
                expected_code=400,
            )

            self.assertIn(f"Plugin '{slug}' is not installed, or does not support the location mixin", str(response.data))

        # Post with a valid plugin, but no other data
        response = self.post(
            url,
            {
                'plugin': 'samplelocate',
            },
            expected_code=400
        )

        self.assertIn("Must supply either 'item' or 'location' parameter", str(response.data))

        # Post with valid plugin, invalid item or location
        for pk in ['qq', 99999, -42]:
            response = self.post(
                url,
                {
                    'plugin': 'samplelocate',
                    'item': pk,
                },
                expected_code=404
            )

            self.assertIn(f"StockItem matching PK '{pk}' not found", str(response.data))

            response = self.post(
                url,
                {
                    'plugin': 'samplelocate',
                    'location': pk,
                },
                expected_code=404,
            )

            self.assertIn(f"StockLocation matching PK '{pk}' not found", str(response.data))