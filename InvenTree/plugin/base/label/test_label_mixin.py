"""Unit tests for the label printing mixin"""

from django.urls import reverse
from django.apps import apps

from InvenTree.api_tester import InvenTreeAPITestCase
from label.models import PartLabel
from part.models import Part
from plugin.registry import registry


class LabelMixinTests(InvenTreeAPITestCase):
    """Test that the Label mixin operates correctly"""

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
    ]

    roles = 'all'

    def activate_plugin(self):
        """Activate the 'samplelabel' plugin"""

        config = registry.get_plugin('samplelabel').plugin_config()
        config.active = True
        config.save()

    def test_installed(self):
        """Test that the sample printing plugin is installed"""

        # Get all label plugins
        plugins = registry.with_mixin('labels')
        self.assertEqual(len(plugins), 1)

        # But, it is not 'active'
        plugins = registry.with_mixin('labels', active=True)
        self.assertEqual(len(plugins), 0)

    def test_api(self):
        """Test that we can filter the API endpoint by mixin"""

        url = reverse('api-plugin-list')

        # Try POST (disallowed)
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 405)

        response = self.client.get(
            url,
            {
                'mixin': 'labels',
                'active': True,
            }
        )

        # No results matching this query!
        self.assertEqual(len(response.data), 0)

        # What about inactive?
        response = self.client.get(
            url,
            {
                'mixin': 'labels',
                'active': False,
            }
        )

        self.assertEqual(len(response.data), 0)


        self.activate_plugin()
        # Should be available via the API now
        response = self.client.get(
            url,
            {
                'mixin': 'labels',
                'active': True,
            }
        )

        self.assertEqual(len(response.data), 1)
        data = response.data[0]
        self.assertEqual(data['key'], 'samplelabel')

    def test_printing_process(self):
        """Test that a label can be printed"""
        # Lookup references
        label = PartLabel.objects.first()
        part = Part.objects.first()
        plugin_ref = 'samplelabel'

        # Non-exsisting plugin
        url = reverse('api-part-label-print', kwargs={'pk': label.pk})
        self.get(f'{url}?parts={part.pk}&plugin={plugin_ref}123', expected_code=404)

        # Inactive plugin
        url = reverse('api-part-label-print', kwargs={'pk': label.pk})
        self.get(f'{url}?parts={part.pk}&plugin={plugin_ref}', expected_code=404)

        # Activate the plugin
        plugin = registry.get_plugin(plugin_ref)

        config = plugin.plugin_config()
        config.active = True
        config.save()

        # Active plugin
        self.get(f'{url}?parts={part.pk}&plugin=samplelabel', expected_code=200)
