"""Unit tests for the 'locate' plugin mixin class."""

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from plugin import InvenTreePlugin, MixinNotImplementedError, registry
from plugin.base.locate.mixins import LocateMixin
from stock.models import StockItem, StockLocation


class LocatePluginTests(InvenTreeAPITestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
    ]

    def test_installed(self):
        """Test that a locate plugin is actually installed."""
        plugins = registry.with_mixin('locate')

        self.assertTrue(len(plugins) > 0)

        self.assertTrue('samplelocate' in [p.slug for p in plugins])

    def test_locate_fail(self):
        """Test various API failure modes."""
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

    def test_locate_item(self):
        """Test that the plugin correctly 'locates' a StockItem.

        As the background worker is not running during unit testing,
        the sample 'locate' function will be called 'inline'
        """
        url = reverse('api-locate-plugin')

        item = StockItem.objects.get(pk=1)

        # The sample plugin will set the 'located' metadata tag
        item.set_metadata('located', False)

        response = self.post(
            url,
            {
                'plugin': 'samplelocate',
                'item': 1,
            },
            expected_code=200
        )

        self.assertEqual(response.data['item'], 1)

        item.refresh_from_db()

        # Item metadata should have been altered!
        self.assertTrue(item.metadata['located'])

    def test_locate_location(self):
        """Test that the plugin correctly 'locates' a StockLocation."""
        url = reverse('api-locate-plugin')

        for location in StockLocation.objects.all():

            location.set_metadata('located', False)

            response = self.post(
                url,
                {
                    'plugin': 'samplelocate',
                    'location': location.pk,
                },
                expected_code=200
            )

            self.assertEqual(response.data['location'], location.pk)

            location.refresh_from_db()

            # Item metadata should have been altered!
            self.assertTrue(location.metadata['located'])

    def test_mixin_locate(self):
        """Test the sample mixin redirection."""
        class SamplePlugin(LocateMixin, InvenTreePlugin):
            pass

        plugin = SamplePlugin()

        # Test that the request is patched through to location
        with self.assertRaises(MixinNotImplementedError):
            plugin.locate_stock_item(1)

        # Test that it runs through
        plugin.locate_stock_item(999)
