""" Unit tests for action plugins """

from django.test import TestCase

from InvenTree.helpers import InvenTreeTestCase
from plugin import InvenTreePlugin
from plugin.mixins import ActionMixin


class ActionMixinTests(TestCase):
    """ Tests for ActionMixin """
    ACTION_RETURN = 'a action was performed'

    def setUp(self):
        class SimplePlugin(ActionMixin, InvenTreePlugin):
            pass
        self.plugin = SimplePlugin()

        class TestActionPlugin(ActionMixin, InvenTreePlugin):
            """a action plugin"""
            ACTION_NAME = 'abc123'

            def perform_action(self, user=None, data=None):
                return ActionMixinTests.ACTION_RETURN + 'action'

            def get_result(self, user=None, data=None):
                return ActionMixinTests.ACTION_RETURN + 'result'

            def get_info(self, user=None, data=None):
                return ActionMixinTests.ACTION_RETURN + 'info'

        self.action_plugin = TestActionPlugin()

        class NameActionPlugin(ActionMixin, InvenTreePlugin):
            NAME = 'Aplugin'

        self.action_name = NameActionPlugin()

    def test_action_name(self):
        """check the name definition possibilities"""
        self.assertEqual(self.plugin.action_name(), '')
        self.assertEqual(self.action_plugin.action_name(), 'abc123')
        self.assertEqual(self.action_name.action_name(), 'Aplugin')

    def test_function(self):
        """check functions"""
        # the class itself
        self.assertIsNone(self.plugin.perform_action())
        self.assertEqual(self.plugin.get_result(), False)
        self.assertIsNone(self.plugin.get_info())
        self.assertEqual(self.plugin.get_response(), {
            "action": '',
            "result": False,
            "info": None,
        })

        # overriden functions
        self.assertEqual(self.action_plugin.perform_action(), self.ACTION_RETURN + 'action')
        self.assertEqual(self.action_plugin.get_result(), self.ACTION_RETURN + 'result')
        self.assertEqual(self.action_plugin.get_info(), self.ACTION_RETURN + 'info')
        self.assertEqual(self.action_plugin.get_response(), {
            "action": 'abc123',
            "result": self.ACTION_RETURN + 'result',
            "info": self.ACTION_RETURN + 'info',
        })


class APITests(InvenTreeTestCase):
    """ Tests for action api """

    def test_post_errors(self):
        """Check the possible errors with post"""

        # Test empty request
        response = self.client.post('/api/action/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {'error': 'No action specified'}
        )

        # Test non-exsisting action
        response = self.client.post('/api/action/', data={'action': "nonexsisting"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {'error': 'No matching action found', 'action': 'nonexsisting'}
        )
