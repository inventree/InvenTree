"""Unit tests for the label printing mixin"""


from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from plugin.registry import registry

class LabelMixinTests(TestCase):
    """Test that the Label mixin operates correctly"""

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
    ]

    def setUp(self):
        super().setUp()

        # Create a user which has all the privelages
        user = get_user_model()

        self.user = user.objects.create_user(
            username='username',
            email='user@email.com',
            password='password'
        )

        # Put the user into a group with the correct permissions
        group = Group.objects.create(name='mygroup')
        self.user.groups.add(group)

        # Give the group *all* the permissions!
        for rule in group.rule_sets.all():
            rule.can_view = True
            rule.can_change = True
            rule.can_add = True
            rule.can_delete = True

            rule.save()

        self.client.login(username='username', password='password')

    def test_intalled(self):
        """Test that the sample printing plugin is installed"""

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

        self.assertEqual(len(response.data), 1)

        # Activate the plugin
        plugin = registry.get_plugin('samplelabel')

        config = plugin.plugin_config()
        config.active = True
        config.save()

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
        self.assertEqual(data[''])