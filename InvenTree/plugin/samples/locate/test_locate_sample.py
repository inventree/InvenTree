"""Unit tests for locate_sample sample plugins"""

from InvenTree.api_tester import InvenTreeAPITestCase
from plugin import InvenTreePlugin, registry
from plugin.helpers import MixinNotImplementedError
from plugin.mixins import LocateMixin


class SampleLocatePlugintests(InvenTreeAPITestCase):
    """Tests for SampleLocatePlugin"""

    def test_mixin(self):
        """Test that MixinNotImplementedError is raised"""

        with self.assertRaises(MixinNotImplementedError):
            class Wrong(LocateMixin, InvenTreePlugin):
                pass

            plugin = Wrong()
            plugin.locate_stock_item()
