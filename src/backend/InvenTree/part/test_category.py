"""Unit tests for the PartCategory model."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from common.models import InvenTreeSetting

from .models import Part, PartCategory, PartParameter, PartParameterTemplate


class CategoryTest(TestCase):
    """Tests to ensure that the relational category tree functions correctly.

    Loads the following test fixtures:
    - category.yaml
    """

    fixtures = ['category', 'part', 'location', 'params']

    @classmethod
    def setUpTestData(cls):
        """Extract some interesting categories for time-saving."""
        super().setUpTestData()

        cls.electronics = PartCategory.objects.get(name='Electronics')
        cls.mechanical = PartCategory.objects.get(name='Mechanical')
        cls.resistors = PartCategory.objects.get(name='Resistors')
        cls.capacitors = PartCategory.objects.get(name='Capacitors')
        cls.fasteners = PartCategory.objects.get(name='Fasteners')
        cls.ic = PartCategory.objects.get(name='IC')
        cls.transceivers = PartCategory.objects.get(name='Transceivers')

    def test_parents(self):
        """Test that the parent fields are properly set, based on the test fixtures."""
        self.assertEqual(self.resistors.parent, self.electronics)
        self.assertEqual(self.capacitors.parent, self.electronics)
        self.assertEqual(self.electronics.parent, None)

        self.assertEqual(self.fasteners.parent, self.mechanical)

    def test_children_count(self):
        """Test that categories have the correct number of children."""
        self.assertTrue(self.electronics.has_children)
        self.assertTrue(self.mechanical.has_children)

        self.assertEqual(len(self.electronics.children.all()), 3)
        self.assertEqual(len(self.mechanical.children.all()), 1)

    def test_unique_children(self):
        """Test the 'unique_children' functionality."""
        children = [item.pk for item in self.electronics.getUniqueChildren()]

        self.assertIn(self.transceivers.id, children)
        self.assertIn(self.ic.id, children)

        self.assertNotIn(self.fasteners.id, children)

    def test_unique_parents(self):
        """Test the 'unique_parents' functionality."""
        parents = [item.pk for item in self.transceivers.getUniqueParents()]

        self.assertIn(self.electronics.id, parents)
        self.assertIn(self.ic.id, parents)
        self.assertNotIn(self.fasteners.id, parents)

    def test_path_string(self):
        """Test that the category path string works correctly."""
        # Note that due to data migrations, these fields need to be saved first
        self.resistors.save()
        self.transceivers.save()

        self.assertEqual(str(self.resistors), 'Electronics/Resistors - Resistors')
        self.assertEqual(
            str(self.transceivers.pathstring), 'Electronics/IC/Transceivers'
        )

        # Create a new subcategory
        subcat = PartCategory.objects.create(
            name='Subcategory',
            description='My little sub category',
            parent=self.transceivers,
        )

        # Pathstring should have been updated correctly
        self.assertEqual(subcat.pathstring, 'Electronics/IC/Transceivers/Subcategory')
        self.assertEqual(len(subcat.path), 4)

        # Move to a new parent location
        subcat.parent = self.resistors
        subcat.save()
        self.assertEqual(subcat.pathstring, 'Electronics/Resistors/Subcategory')
        self.assertEqual(len(subcat.path), 3)

        # Move to top-level
        subcat.parent = None
        subcat.save()
        self.assertEqual(subcat.pathstring, 'Subcategory')
        self.assertEqual(len(subcat.path), 1)

        # Construct a very long pathstring and ensure it gets updated correctly
        cat = PartCategory.objects.create(
            name='Cat', description='A long running category', parent=None
        )

        parent = cat

        for idx in range(26):
            letter = chr(ord('A') + idx)

            child = PartCategory.objects.create(
                name=letter * 10, description=f'Subcategory {letter}', parent=parent
            )

            parent = child

        self.assertTrue(len(child.path), 26)
        self.assertEqual(
            child.pathstring,
            'Cat/AAAAAAAAAA/BBBBBBBBBB/CCCCCCCCCC/DDDDDDDDDD/EEEEEEEEEE/FFFFFFFFFF/GGGGGGGGGG/HHHHHHHHHH/IIIIIIIIII/JJJJJJJJJJ/KKKKKKKKK...OO/PPPPPPPPPP/QQQQQQQQQQ/RRRRRRRRRR/SSSSSSSSSS/TTTTTTTTTT/UUUUUUUUUU/VVVVVVVVVV/WWWWWWWWWW/XXXXXXXXXX/YYYYYYYYYY/ZZZZZZZZZZ',
        )
        self.assertLessEqual(len(child.pathstring), 250)

        # Attempt an invalid move
        with self.assertRaises(ValidationError):
            cat.parent = child
            cat.save()

    def test_url(self):
        """Test that the PartCategory URL works."""
        self.assertEqual(
            self.capacitors.get_absolute_url(), '/platform/part/category/3'
        )

    def test_part_count(self):
        """Test that the Category part count works."""
        self.assertEqual(self.fasteners.partcount(), 2)
        self.assertEqual(self.capacitors.partcount(), 1)

        self.assertEqual(self.electronics.partcount(), 3)

        self.assertEqual(self.mechanical.partcount(), 9)
        self.assertEqual(self.mechanical.partcount(active=True), 9)

        # Mark one part as inactive and retry
        part = Part.objects.get(pk=1)
        part.active = False
        part.save()

        self.assertEqual(self.mechanical.partcount(active=True), 8)

        self.assertEqual(self.mechanical.partcount(False), 7)

        self.assertEqual(self.electronics.item_count, self.electronics.partcount())

    def test_parameters(self):
        """Test that the Category parameters are correctly fetched."""
        # Check number of SQL queries to iterate other parameters
        with self.assertNumQueries(9):
            # Prefetch: 3 queries (parts, parameters and parameters_template)
            fasteners = self.fasteners.prefetch_parts_parameters()
            # Iterate through all parts and parameters
            for fastener in fasteners:
                self.assertIsInstance(fastener, Part)
                for parameter in fastener.parameters.all():
                    self.assertIsInstance(parameter, PartParameter)
                    self.assertIsInstance(parameter.template, PartParameterTemplate)

            # Test number of unique parameters
            self.assertEqual(
                len(self.fasteners.get_unique_parameters(prefetch=fasteners)), 1
            )
            # Test number of parameters found for each part
            parts_parameters = self.fasteners.get_parts_parameters(prefetch=fasteners)
            part_infos = ['pk', 'name', 'description']
            for part_parameter in parts_parameters:
                # Remove part information
                for item in part_infos:
                    part_parameter.pop(item)
                self.assertEqual(len(part_parameter), 1)

    def test_delete(self):
        """Test that category deletion moves the children properly."""
        # Delete the 'IC' category and 'Transceiver' should move to be under 'Electronics'
        self.assertEqual(self.transceivers.parent, self.ic)
        self.assertEqual(self.ic.parent, self.electronics)

        self.ic.delete()

        # Get the data again
        transceivers = PartCategory.objects.get(name='Transceivers')
        self.assertEqual(transceivers.parent, self.electronics)

        # Now delete the 'fasteners' category - the parts should move to 'mechanical'
        self.fasteners.delete()

        fasteners = Part.objects.filter(description__contains='screw')

        for f in fasteners:
            self.assertEqual(f.category, self.mechanical)

    def test_default_locations(self):
        """Test traversal for default locations."""
        self.assertIsNotNone(self.fasteners.default_location)
        self.fasteners.default_location.save()
        self.assertEqual(
            str(self.fasteners.default_location), 'Office/Drawer_1 - In my desk'
        )

        # Any part under electronics should default to 'Home'
        r1 = Part.objects.get(name='R_2K2_0805')
        self.assertIsNone(r1.default_location)
        self.assertEqual(r1.get_default_location().name, 'Home')

        # But one part has a default_location set
        r2 = Part.objects.get(name='R_4K7_0603')
        self.assertEqual(r2.get_default_location().name, 'Bathroom')

        # And one part should have no default location at all
        w = Part.objects.get(name='Widget')
        self.assertIsNone(w.get_default_location())

    def test_category_tree(self):
        """Unit tests for the part category tree structure (MPTT).

        Ensure that the MPTT structure is rebuilt correctly,
        and the correct ancestor tree is observed.
        """
        # Clear out any existing parts
        Part.objects.all().delete()

        PartCategory.objects.rebuild()

        # First, create a structured tree of part categories
        A = PartCategory.objects.create(name='A', description='Top level category')

        B1 = PartCategory.objects.create(name='B1', parent=A)
        B2 = PartCategory.objects.create(name='B2', parent=A)
        B3 = PartCategory.objects.create(name='B3', parent=A)

        C11 = PartCategory.objects.create(name='C11', parent=B1)
        C12 = PartCategory.objects.create(name='C12', parent=B1)
        C13 = PartCategory.objects.create(name='C13', parent=B1)

        C21 = PartCategory.objects.create(name='C21', parent=B2)
        C22 = PartCategory.objects.create(name='C22', parent=B2)
        C23 = PartCategory.objects.create(name='C23', parent=B2)

        C31 = PartCategory.objects.create(name='C31', parent=B3)
        C32 = PartCategory.objects.create(name='C32', parent=B3)
        C33 = PartCategory.objects.create(name='C33', parent=B3)

        D31 = PartCategory.objects.create(name='D31', parent=C31)
        D32 = PartCategory.objects.create(name='D32', parent=C32)
        D33 = PartCategory.objects.create(name='D33', parent=C33)

        E33 = PartCategory.objects.create(name='E33', parent=D33)

        # Check that pathstrings have been generated correctly
        self.assertEqual(B3.pathstring, 'A/B3')
        self.assertEqual(C11.pathstring, 'A/B1/C11')
        self.assertEqual(C22.pathstring, 'A/B2/C22')
        self.assertEqual(C33.pathstring, 'A/B3/C33')

        # Check that the tree_id value is correct
        for cat in [B1, B2, B3, C11, C22, C33]:
            self.assertEqual(cat.tree_id, A.tree_id)
            self.assertEqual(cat.level, cat.parent.level + 1)
            self.assertEqual(cat.get_ancestors().count(), cat.level)

        # Spot check for C31
        ancestors = C31.get_ancestors(include_self=True)

        self.assertEqual(ancestors.count(), 3)
        self.assertEqual(ancestors[0], A)
        self.assertEqual(ancestors[1], B3)
        self.assertEqual(ancestors[2], C31)

        # At this point, we are confident that the tree is correctly structured

        for i in range(10):
            Part.objects.create(
                name=f'Part {i}', description='A test part', category=B3
            )

        self.assertEqual(Part.objects.filter(category=B3).count(), 10)
        self.assertEqual(Part.objects.filter(category=A).count(), 0)

        # Delete category B3
        B3.delete()

        # Child parts have been moved to category A
        self.assertEqual(Part.objects.filter(category=A).count(), 10)

        for cat in [C31, C32, C33]:
            # These categories should now be directly under A
            cat.refresh_from_db()

            self.assertEqual(cat.parent, A)
            self.assertEqual(cat.level, 1)
            self.assertEqual(cat.get_ancestors().count(), 1)
            self.assertEqual(cat.get_ancestors()[0], A)

            self.assertEqual(cat.pathstring, f'A/{cat.name}')

        # Now, delete category A
        A.delete()

        # Parts have now been moved to the top-level category
        self.assertEqual(Part.objects.filter(category=None).count(), 10)

        for loc in [B1, B2, C31, C32, C33]:
            # These should now all be "top level" categories
            loc.refresh_from_db()

            self.assertEqual(loc.level, 0)
            self.assertEqual(loc.parent, None)

            # Pathstring should be the same as the name
            self.assertEqual(loc.pathstring, loc.name)

            # Test pathstring for direct children
            for child in loc.get_children():
                self.assertEqual(child.pathstring, f'{loc.name}/{child.name}')

        # Check descendants for B1
        descendants = B1.get_descendants()
        self.assertEqual(descendants.count(), 3)

        for loc in [C11, C12, C13]:
            self.assertIn(loc, descendants)

        # Check category C1x, should be B1 -> C1x
        for loc in [C11, C12, C13]:
            loc.refresh_from_db()

            self.assertEqual(loc.level, 1)
            self.assertEqual(loc.parent, B1)
            ancestors = loc.get_ancestors(include_self=True)

            self.assertEqual(ancestors.count(), 2)
            self.assertEqual(ancestors[0], B1)
            self.assertEqual(ancestors[1], loc)

            self.assertEqual(loc.pathstring, f'B1/{loc.name}')

        # Check category C2x, should be B2 -> C2x
        for loc in [C21, C22, C23]:
            loc.refresh_from_db()

            self.assertEqual(loc.level, 1)
            self.assertEqual(loc.parent, B2)
            ancestors = loc.get_ancestors(include_self=True)

            self.assertEqual(ancestors.count(), 2)
            self.assertEqual(ancestors[0], B2)
            self.assertEqual(ancestors[1], loc)

            self.assertEqual(loc.pathstring, f'B2/{loc.name}')

        # Check category D3x, should be C3x -> D3x
        D31.refresh_from_db()
        self.assertEqual(D31.pathstring, 'C31/D31')
        D32.refresh_from_db()
        self.assertEqual(D32.pathstring, 'C32/D32')
        D33.refresh_from_db()
        self.assertEqual(D33.pathstring, 'C33/D33')

        # Check category E33
        E33.refresh_from_db()
        self.assertEqual(E33.pathstring, 'C33/D33/E33')

        # Change the name of an upper level
        C33.name = '-C33-'
        C33.save()

        D33.refresh_from_db()
        self.assertEqual(D33.pathstring, '-C33-/D33')

        E33.refresh_from_db()
        self.assertEqual(E33.pathstring, '-C33-/D33/E33')

        # Test the "delete child categories" functionality
        C33.delete(delete_child_categories=True)

        # Any child underneath C33 should have been deleted
        for cat in [D33, E33]:
            with self.assertRaises(PartCategory.DoesNotExist):
                cat.refresh_from_db()

        Part.objects.all().delete()

        # Create some sample parts under D32
        for ii in range(10):
            Part.objects.create(
                name=f'Part D32 {ii}', description='A test part', category=D32
            )

        self.assertEqual(Part.objects.filter(category=D32).count(), 10)
        self.assertEqual(Part.objects.filter(category=C32).count(), 0)

        # Delete D32, should move the parts up to C32
        D32.delete(delete_child_categories=False, delete_parts=False)

        # All parts should have been deleted
        self.assertEqual(Part.objects.filter(category=C32).count(), 10)

        # Now, delete C32 and delete all parts underneath
        C32.delete(delete_parts=True)

        # 10 parts should have been deleted from the database
        self.assertEqual(Part.objects.count(), 0)

        # Finally, try deleting a category which has already been deleted
        # should log an exception
        with self.assertRaises(ValidationError):
            B3.delete()

    def test_icon(self):
        """Test the category icon."""
        # No default icon set
        cat = PartCategory.objects.create(name='Test Category')
        self.assertEqual(cat.icon, '')

        # Set a default icon
        InvenTreeSetting.set_setting('PART_CATEGORY_DEFAULT_ICON', 'ti:package:outline')
        self.assertEqual(cat.icon, 'ti:package:outline')

        # Set custom icon to default icon and assert that it does not get written to the database
        cat.icon = 'ti:package:outline'
        cat.save()
        self.assertEqual(cat._icon, '')

        # Set a different custom icon and assert that it takes precedence
        cat.icon = 'ti:tag:outline'
        cat.save()
        self.assertEqual(cat.icon, 'ti:tag:outline')
        InvenTreeSetting.set_setting('PART_CATEGORY_DEFAULT_ICON', '')

        # Test that the icon can be set to None again
        cat.icon = ''
        cat.save()
        self.assertEqual(cat.icon, '')
