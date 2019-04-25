from django.test import TestCase

from .models import Part, PartCategory


class CategoryTest(TestCase):
    """
    Tests to ensure that the relational category tree functions correctly.
    """

    def setUp(self):
        self.p1 = PartCategory.objects.create(name='A',
                                              description='Most highest level',
                                              parent=None)

        self.p2 = PartCategory.objects.create(name='B',
                                              description='Sits under second',
                                              parent=self.p1)

        self.p3 = PartCategory.objects.create(name='C',
                                              description='Third tier category',
                                              parent=self.p2)

        # Add two parts in p2
        Part.objects.create(name='Flange', category=self.p2)
        Part.objects.create(name='Flob', category=self.p2)

        # Add one part in p3
        Part.objects.create(name='Blob', category=self.p3)

    def test_parents(self):
        self.assertEqual(self.p1.parent, None)
        self.assertEqual(self.p2.parent, self.p1)
        self.assertEqual(self.p3.parent, self.p2)

    def test_children_count(self):
        self.assertEqual(self.p1.has_children, True)
        self.assertEqual(self.p2.has_children, True)
        self.assertEqual(self.p3.has_children, False)

    def test_unique_childs(self):
        childs = self.p1.getUniqueChildren()

        self.assertIn(self.p2.id, childs)
        self.assertIn(self.p3.id, childs)

    def test_unique_parents(self):
        parents = self.p2.getUniqueParents()

        self.assertIn(self.p1.id, parents)

    def test_path_string(self):
        self.assertEqual(str(self.p3), 'A/B/C')

    def test_url(self):
        self.assertEqual(self.p1.get_absolute_url(), '/part/category/1/')

    def test_part_count(self):
        # No direct parts in the top-level category
        self.assertEqual(self.p1.has_parts, False)
        self.assertEqual(self.p2.has_parts, True)
        self.assertEqual(self.p3.has_parts, True)

        self.assertEqual(self.p1.partcount, 3)
        self.assertEqual(self.p2.partcount, 3)
        self.assertEqual(self.p3.partcount, 1)
