""" Unit tests for action plugins """

from django.test import TestCase
from django.contrib.auth import get_user_model

from plugins.samples.action.simpleactionplugin import SimpleActionPlugin


class SimpleActionPluginTests(TestCase):
    """ Tests for SampleIntegrationPlugin """

    def setUp(self):
        # Create a user for auth
        user = get_user_model()
        user.objects.create_user('testuser', 'test@testing.com', 'password')

        self.client.login(username='testuser', password='password')

        self.plugin = SimpleActionPlugin()

    def test_name(self):
        """check plugn names """
        self.assertEqual(self.plugin.plugin_name(), "SimpleActionPlugin")
        self.assertEqual(self.plugin.action_name(), "simple")

    def test_function(self):
        """check if functions work """
        # test functions
        respone = self.client.get('/action/sample/')
        self.assertEqual(respone.status_code, 200)
        self.assertEqual(respone.content, {
            "action": 'simple',
            "result": True,
            "info": {
                "user": "testuser",
                "hello": "world",
            },
        })
