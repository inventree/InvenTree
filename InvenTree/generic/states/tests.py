"""Tests for the generic states module."""
from django.utils.translation import gettext_lazy as _

from generic.states.states import StatusCode
from InvenTree.unit_test import InvenTreeTestCase


class GeneralStatus(StatusCode):
    """Defines a set of status codes for tests."""
    _TAG = 'general'

    PENDING = 10
    PLACED = 20
    COMPLETE = 30
    ABC = None  # This should be ignored
    DEF = 40  # This should be ignored

    def GHI(self):  # This should be ignored
        """A invalid function"""
        pass

    options = {
        PENDING: _("Pending"),
        PLACED: _("Placed"),
        COMPLETE: _("Complete"),
    }

    colors = {
        PENDING: 'secondary',
        PLACED: 'primary',
        COMPLETE: 'success',
    }

    # Open orders
    OPEN = [
        PENDING,
        PLACED,
    ]

    # Done orders
    DONE = [
        COMPLETE,
    ]


class GeneralStateTest(InvenTreeTestCase):
    """Test that the StatusCode class works."""
    def test_definition(self):
        """Test that the status code class has been defined correctly"""
        self.assertEqual(GeneralStatus.PENDING, 10)
        self.assertEqual(GeneralStatus.PLACED, 20)
        self.assertEqual(GeneralStatus.COMPLETE, 30)

        self.assertEqual(GeneralStatus.options, {
            10: _("Pending"),
            20: _("Placed"),
            30: _("Complete"),
        })

        self.assertEqual(GeneralStatus.colors, {
            10: 'secondary',
            20: 'primary',
            30: 'success',
        })

        self.assertEqual(GeneralStatus.OPEN, [
            10,
            20,
        ])

        self.assertEqual(GeneralStatus.DONE, [
            30,
        ])

    def test_functions(self):
        """Test that the status code class functions work correctly"""
        # render
        self.assertEqual(GeneralStatus.render(10), "<span class='badge rounded-pill bg-secondary'>Pending</span>")
        self.assertEqual(GeneralStatus.render(20), "<span class='badge rounded-pill bg-primary'>Placed</span>")
        # render with invalid key
        self.assertEqual(GeneralStatus.render(100), 100)

        # list
        self.assertEqual(GeneralStatus.list(), [{'color': 'success', 'key': 30, 'label': 'Complete', 'name': 'COMPLETE'}, {'color': 'secondary', 'key': 10, 'label': 'Pending', 'name': 'PENDING'}, {'color': 'primary', 'key': 20, 'label': 'Placed', 'name': 'PLACED'}])

        # text
        self.assertEqual(GeneralStatus.text(10), 'Pending')
        self.assertEqual(GeneralStatus.text(20), 'Placed')

        # items
        self.assertEqual(list(GeneralStatus.items()), [(10, 'Pending'), (20, 'Placed'), (30, 'Complete')])

        # keys
        self.assertEqual(list(GeneralStatus.keys()), ([10, 20, 30]))

        # labels
        self.assertEqual(list(GeneralStatus.labels()), ['Pending', 'Placed', 'Complete'])

        # names
        self.assertEqual(GeneralStatus.names(), {'PENDING': 10, 'PLACED': 20, 'COMPLETE': 30})

        # dict
        self.assertEqual(GeneralStatus.dict(), {
            'PENDING': {'key': 10, 'name': 'PENDING', 'label': 'Pending', 'color': 'secondary'},
            'PLACED': {'key': 20, 'name': 'PLACED', 'label': 'Placed', 'color': 'primary'},
            'COMPLETE': {'key': 30, 'name': 'COMPLETE', 'label': 'Complete', 'color': 'success'},
        })

        # label
        self.assertEqual(GeneralStatus.label(10), 'Pending')

        # value
        self.assertEqual(GeneralStatus.value('Pending'), 10)
        # value with invalid key
        with self.assertRaises(ValueError) as e:
            GeneralStatus.value('Invalid')
        self.assertEqual(str(e.exception), "Label not found")
