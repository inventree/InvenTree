"""Unit tests for the AutoCreateBuildsPlugin."""

from decimal import Decimal

from build.models import Build
from build.status_codes import BuildStatus
from common.settings import set_global_setting
from InvenTree.unit_test import InvenTreeTestCase
from part.models import BomItem, Part
from plugin import registry
from stock.models import StockItem


class AutoCreateBuildsTest(InvenTreeTestCase):
    """Tests for automatically creating child build orders."""

    @classmethod
    def setUpTestData(cls):
        """Create a multi-level assembly tree.

        top -> sub_1 (x0.5) -> sub_2 (x2) -> sub_3 (x1)
        """
        super().setUpTestData()

        cls.top = Part.objects.create(name='Top', description='Top', assembly=True)
        cls.sub_1 = Part.objects.create(
            name='Sub 1', description='Sub 1', assembly=True, component=True
        )
        cls.sub_2 = Part.objects.create(
            name='Sub 2', description='Sub 2', assembly=True, component=True
        )
        cls.sub_3 = Part.objects.create(
            name='Sub 3', description='Sub 3', assembly=True, component=True
        )

        BomItem.objects.create(part=cls.top, sub_part=cls.sub_1, quantity=0.5)
        BomItem.objects.create(part=cls.sub_1, sub_part=cls.sub_2, quantity=2)
        BomItem.objects.create(part=cls.sub_2, sub_part=cls.sub_3, quantity=1)

    def setUp(self):
        """Activate the plugin and create a top-level build order."""
        super().setUp()

        registry.set_plugin_state('autocreatebuilds', True)
        self.plugin = registry.get_plugin('autocreatebuilds')

        self.build = Build.objects.create(
            part=self.top, quantity=3, status=BuildStatus.PRODUCTION, title='Top build'
        )

    def set_depth(self, depth: int):
        """Set the cascade depth for the plugin."""
        self.plugin.set_setting('CASCADE_DEPTH', depth)

    def run_plugin(self):
        """Run the plugin against the top-level build, executing any cascaded tasks."""
        with self.captureOnCommitCallbacks(execute=True):
            self.plugin.create_child_builds(
                self.build.pk, self.plugin.get_cascade_depth()
            )

    def test_default_depth(self):
        """With the default depth, only direct children are created."""
        self.assertEqual(self.plugin.get_cascade_depth(), 1)

        self.run_plugin()

        children = self.build.children.all()
        self.assertEqual(children.count(), 1)

        child = children.first()
        self.assertEqual(child.part, self.sub_1)
        self.assertEqual(child.status, BuildStatus.PENDING)

        # 3 x 0.5 = 1.5, rounded up
        self.assertEqual(child.quantity, 2)

        self.assertEqual(child.children.count(), 0)
        self.assertEqual(Build.objects.count(), 2)

    def test_cascade(self):
        """Child builds are cascaded down to the configured depth."""
        self.set_depth(2)
        self.run_plugin()

        child = self.build.children.get()
        grandchild = child.children.get()

        self.assertEqual(grandchild.part, self.sub_2)
        self.assertEqual(grandchild.quantity, 4)
        self.assertEqual(grandchild.children.count(), 0)

        # Increasing the depth extends the existing tree
        self.set_depth(5)
        self.run_plugin()

        great_grandchild = grandchild.children.get()
        self.assertEqual(great_grandchild.part, self.sub_3)
        self.assertEqual(great_grandchild.quantity, 4)

        self.assertEqual(Build.objects.count(), 4)

    def test_idempotent(self):
        """Running the plugin multiple times does not create duplicate builds."""
        self.set_depth(3)

        for _ in range(3):
            self.run_plugin()

        self.assertEqual(Build.objects.count(), 4)

        for part in [self.sub_1, self.sub_2, self.sub_3]:
            self.assertEqual(Build.objects.filter(part=part).count(), 1)

    def test_sufficient_stock(self):
        """No child build is created if there is sufficient stock."""
        StockItem.objects.create(part=self.sub_1, quantity=Decimal(10))

        self.set_depth(3)
        self.run_plugin()

        self.assertEqual(self.build.children.count(), 0)
        self.assertEqual(Build.objects.count(), 1)

    def test_inactive_build(self):
        """No child builds are created for an inactive build order."""
        self.build.status = BuildStatus.CANCELLED
        self.build.save()

        self.run_plugin()

        self.assertEqual(self.build.children.count(), 0)

    def test_validation_error(self):
        """A sub-assembly which fails validation is skipped."""
        set_global_setting('BUILDORDER_REQUIRE_ACTIVE_PART', True)

        self.sub_1.active = False
        self.sub_1.save()

        self.run_plugin()

        self.assertEqual(self.build.children.count(), 0)
