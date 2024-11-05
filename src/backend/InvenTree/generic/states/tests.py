"""Tests for the generic states module."""

from django.contrib.contenttypes.models import ContentType
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework.test import force_authenticate

from common.models import InvenTreeCustomUserStateModel
from generic.states import ColorEnum
from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase

from .api import StatusView
from .states import StatusCode


class GeneralStatus(StatusCode):
    """Defines a set of status codes for tests."""

    PENDING = 10, _('Pending'), ColorEnum.secondary
    PLACED = 20, _('Placed'), 'primary'
    COMPLETE = 30, _('Complete'), ColorEnum.success
    ABC = None  # This should be ignored
    _DEF = None  # This should be ignored
    jkl = None  # This should be ignored

    def GHI(self):  # This should be ignored
        """A invalid function."""


class GeneralStateTest(InvenTreeTestCase):
    """Test that the StatusCode class works."""

    def test_code_definition(self):
        """Test that the status code class has been defined correctly."""
        self.assertEqual(GeneralStatus.PENDING, 10)
        self.assertEqual(GeneralStatus.PLACED, 20)
        self.assertEqual(GeneralStatus.COMPLETE, 30)

    def test_code_functions(self):
        """Test that the status code class functions work correctly."""
        # render
        self.assertEqual(
            GeneralStatus.render(10),
            "<span class='badge rounded-pill bg-secondary'>Pending</span>",
        )
        self.assertEqual(
            GeneralStatus.render(20),
            "<span class='badge rounded-pill bg-primary'>Placed</span>",
        )
        # render with invalid key
        self.assertEqual(GeneralStatus.render(100), 100)

        # list
        self.assertEqual(
            GeneralStatus.list(),
            [
                {
                    'color': 'secondary',
                    'key': 10,
                    'label': 'Pending',
                    'name': 'PENDING',
                },
                {'color': 'primary', 'key': 20, 'label': 'Placed', 'name': 'PLACED'},
                {
                    'color': 'success',
                    'key': 30,
                    'label': 'Complete',
                    'name': 'COMPLETE',
                },
            ],
        )

        # text
        self.assertEqual(GeneralStatus.text(10), 'Pending')
        self.assertEqual(GeneralStatus.text(20), 'Placed')

        # items
        self.assertEqual(
            list(GeneralStatus.items()),
            [(10, 'Pending'), (20, 'Placed'), (30, 'Complete')],
        )

        # keys
        self.assertEqual(list(GeneralStatus.keys()), ([10, 20, 30]))

        # labels
        self.assertEqual(
            list(GeneralStatus.labels()), ['Pending', 'Placed', 'Complete']
        )

        # names
        self.assertEqual(
            GeneralStatus.names(), {'PENDING': 10, 'PLACED': 20, 'COMPLETE': 30}
        )

        # dict
        self.assertEqual(
            GeneralStatus.dict(),
            {
                'PENDING': {
                    'key': 10,
                    'name': 'PENDING',
                    'label': 'Pending',
                    'color': 'secondary',
                },
                'PLACED': {
                    'key': 20,
                    'name': 'PLACED',
                    'label': 'Placed',
                    'color': 'primary',
                },
                'COMPLETE': {
                    'key': 30,
                    'name': 'COMPLETE',
                    'label': 'Complete',
                    'color': 'success',
                },
            },
        )

        # label
        self.assertEqual(GeneralStatus.label(10), 'Pending')

    def test_color(self):
        """Test that the color enum validation works."""
        with self.assertRaises(ValueError) as e:

            class TTTT(StatusCode):
                PENDING = 10, _('Pending'), 'invalid'

        self.assertEqual(
            str(e.exception), "Invalid color value 'invalid' for status 'Pending'"
        )

    def test_tag_status_label(self):
        """Test that the status_label tag."""
        from .tags import status_label

        self.assertEqual(
            status_label('general', 10),
            "<span class='badge rounded-pill bg-secondary'>Pending</span>",
        )

        # invalid type
        with self.assertRaises(ValueError) as e:
            status_label('invalid', 10)
        self.assertEqual(str(e.exception), "Unknown status type 'invalid'")

        # Test non-existent key
        self.assertEqual(status_label('general', 100), '100')

    def test_tag_display_status_label(self):
        """Test that the display_status_label tag (mainly the same as status_label)."""
        from .tags import display_status_label

        self.assertEqual(
            display_status_label('general', 10, 11),
            "<span class='badge rounded-pill bg-secondary'>Pending</span>",
        )
        # Fallback
        self.assertEqual(display_status_label('general', None, 11), '11')
        self.assertEqual(
            display_status_label('general', None, 10),
            "<span class='badge rounded-pill bg-secondary'>Pending</span>",
        )

    def test_api(self):
        """Test StatusView API view."""
        view = StatusView.as_view()
        rqst = RequestFactory().get('status/')
        force_authenticate(rqst, user=self.user)

        # Correct call
        resp = view(rqst, **{StatusView.MODEL_REF: GeneralStatus})
        self.assertEqual(
            resp.data,
            {
                'class': 'GeneralStatus',
                'values': {
                    'COMPLETE': {
                        'key': 30,
                        'name': 'COMPLETE',
                        'label': 'Complete',
                        'color': 'success',
                    },
                    'PENDING': {
                        'key': 10,
                        'name': 'PENDING',
                        'label': 'Pending',
                        'color': 'secondary',
                    },
                    'PLACED': {
                        'key': 20,
                        'name': 'PLACED',
                        'label': 'Placed',
                        'color': 'primary',
                    },
                },
            },
        )

        # No status defined
        resp = view(rqst, **{StatusView.MODEL_REF: None})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            str(resp.rendered_content, 'utf-8'),
            '["StatusView view called without \'statusmodel\' parameter"]',
        )

        # Invalid call - not a class
        with self.assertRaises(NotImplementedError) as e:
            resp = view(rqst, **{StatusView.MODEL_REF: 'invalid'})
        self.assertEqual(str(e.exception), '`status_class` not a class')

        # Invalid call - not the right class
        with self.assertRaises(NotImplementedError) as e:
            resp = view(rqst, **{StatusView.MODEL_REF: object})
        self.assertEqual(
            str(e.exception), '`status_class` not a valid StatusCode class'
        )


class ApiTests(InvenTreeAPITestCase):
    """Test the API for the generic states module."""

    def test_all_states(self):
        """Test the API endpoint for listing all status models."""
        response = self.get(reverse('api-status-all'))
        self.assertEqual(len(response.data), 12)

        # Test the BuildStatus model
        build_status = response.data['BuildStatus']
        self.assertEqual(build_status['class'], 'BuildStatus')
        self.assertEqual(len(build_status['values']), 5)
        pending = build_status['values']['PENDING']
        self.assertEqual(pending['key'], 10)
        self.assertEqual(pending['name'], 'PENDING')
        self.assertEqual(pending['label'], 'Pending')

        # Test the StockStatus model (static)
        stock_status = response.data['StockStatus']
        self.assertEqual(stock_status['class'], 'StockStatus')
        self.assertEqual(len(stock_status['values']), 8)
        in_stock = stock_status['values']['OK']
        self.assertEqual(in_stock['key'], 10)
        self.assertEqual(in_stock['name'], 'OK')
        self.assertEqual(in_stock['label'], 'OK')

        # MachineStatus model
        machine_status = response.data['MachineStatus__LabelPrinterStatus']
        self.assertEqual(machine_status['class'], 'LabelPrinterStatus')
        self.assertEqual(len(machine_status['values']), 6)
        connected = machine_status['values']['CONNECTED']
        self.assertEqual(connected['key'], 100)
        self.assertEqual(connected['name'], 'CONNECTED')

        # Add custom status
        InvenTreeCustomUserStateModel.objects.create(
            key=11,
            name='OK - advanced',
            label='OK - adv.',
            color='secondary',
            logical_key=10,
            model=ContentType.objects.get(model='stockitem'),
            reference_status='StockStatus',
        )
        response = self.get(reverse('api-status-all'))
        self.assertEqual(len(response.data), 12)

        stock_status_cstm = response.data['StockStatus']
        self.assertEqual(stock_status_cstm['class'], 'StockStatus')
        self.assertEqual(len(stock_status_cstm['values']), 9)
        ok_advanced = stock_status_cstm['values']['OK']
        self.assertEqual(ok_advanced['key'], 10)
        self.assertEqual(ok_advanced['name'], 'OK')
        self.assertEqual(ok_advanced['label'], 'OK')
