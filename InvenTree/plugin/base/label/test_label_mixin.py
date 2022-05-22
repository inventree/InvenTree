"""Unit tests for the label printing mixin"""

from django.apps import apps
from django.urls import reverse

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

    def get_url(self, parts, plugin_ref, label):
        """Generate an URL to print a label"""
        # Gather part details
        if len(parts) == 1:
            part_url = parts[0].pk
        else:
            part_url = f'[{",".join([str(item.pk) for item in parts])}]'
        # Construct url
        url = f'{reverse("api-part-label-print", kwargs={"pk": label.pk})}?parts={part_url}&plugin={plugin_ref}'
        return url

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

        # Ensure the labels were created
        apps.get_app_config('label').create_labels()

        # Lookup references
        part = Part.objects.first()
        plugin_ref = 'samplelabel'
        label = PartLabel.objects.first()

        url = self.get_url([part], plugin_ref, label)

        # Non-exsisting plugin
        response = self.get(f'{url}123', expected_code=404)
        self.assertIn(f'Plugin \'{plugin_ref}123\' not found', str(response.content, 'utf8'))

        # Inactive plugin
        response = self.get(url, expected_code=400)
        self.assertIn(f'Plugin \'{plugin_ref}\' is not enabled', str(response.content, 'utf8'))

        # Active plugin
        self.activate_plugin()
        self.get(url, expected_code=200)
