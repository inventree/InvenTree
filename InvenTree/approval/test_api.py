"""Unit tests for the Approval API."""

from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from approval.models import Approval, ApprovalState
from InvenTree.unit_test import InvenTreeAPITestCase
from order.models import PurchaseOrder

from .rules import ApprovalRule


class MixinApproval:
    """Mixin for approval tests."""
    time_threshold = timedelta(seconds=0.5)
    roles = [
        'approval.view',
        'approval.add',
        'approval.change',
    ]

    def setUp(self):
        """Add extra user."""
        super().setUp()

        self.user1 = get_user_model().objects.create_user(username='testuser1', password='password', email='testuser1', is_superuser=True)

    def create_approval(self):
        """Create a test approval."""

        self.purchase_order = PurchaseOrder.objects.create(
            description='A test order',
            creation_date=datetime.now().date(),
            target_date=datetime.now().date() + timedelta(days=7),
        )

        approval = Approval.objects.create(
            name='Test Approval',
            description='A test approval',
            content_object=self.purchase_order,
        )

        return approval

    def state_check(self, vals, state, usr=None, http: bool = False):
        """Check results"""
        ext_tm = datetime.now()
        assertations = {
            0: ['New', 0, False, 0],
            10: ['Pending', 1, False, 10],
            20: ['Approved', 2, True, 20],
            30: ['Rejected', 2, True, 30],
        }

        def get_val(ref):
            return vals[ref] if http else getattr(vals, ref)
        if usr:
            # Test common date and user settings
            self.assertEqual(get_val('modified_by'), usr.pk if http else usr)
            self.assertTrue((ext_tm - (datetime.fromisoformat(get_val('modified_date')) if http else get_val('modified_date'))) < self.time_threshold)
            if assertations[state][2]:
                self.assertEqual(get_val('finalised_by'), usr.pk if http else usr)
                self.assertTrue((ext_tm - (datetime.fromisoformat(get_val('finalised_date')) if http else get_val('finalised_date'))) < self.time_threshold)
        # Test common approval assertions
        self.assertEqual(len(get_val('decisions')) if http else vals.decisions.count(), assertations[state][1])
        self.assertEqual(get_val('status_text'), assertations[state][0])
        self.assertEqual(get_val('status'), assertations[state][3])
        self.assertEqual(get_val('status'), getattr(ApprovalState, assertations[state][0].upper()))
        self.assertEqual(get_val('finalised'), assertations[state][2])


class TestApprovalFunctions(MixinApproval, InvenTreeAPITestCase):
    """Test the function of approval functionality."""

    def test_rejected_approval(self):
        """Test a rejected approval flow."""
        # Base approval
        approval = self.create_approval()
        self.state_check(approval, 0)

        # Make one positive decision
        approval.add_decision(self.user, True)
        self.state_check(approval, 10, usr=self.user)

        # Add a negative decision
        approval.add_decision(self.user1, False)
        self.state_check(approval, 30, usr=self.user1)

        # Check API fnc
        self.assertEqual(approval.get_api_url(), f'/api/approval/{approval.pk}/')

    def test_accepted_approval(self):
        """Test a successful approval run."""
        # Base approval
        approval = self.create_approval()
        approval.add_decision(self.user1, True)
        approval.add_decision(self.user, True)
        self.state_check(approval, 20, usr=self.user)

    def test_rules(self):
        """Test rule implementation."""

        class WrongRule(ApprovalRule):
            """Test rule implementation."""
            pass

        with self.assertRaises(NotImplementedError):
            WrongRule()


class TestApprovalApi(MixinApproval, InvenTreeAPITestCase):
    """Test approval apis."""

    def test_list_urls(self):
        """Test that the approval list API can be accessed."""
        self.get(reverse('api-approval-list'))

    def test_detail_urls(self):
        """Test that the approval detail API can be accessed."""
        approval = self.create_approval()
        self.get(reverse('api-approval-detail', kwargs={'pk': approval.pk}))

    def test_full_runthrough(self):
        """Test that a full lifecycle of an approval can be run through.

        This replicates everything in TestApprovalFunctions.test_functions but via the api.
        """
        self.create_approval()

        # Create a new approval
        data = {
            'name': 'Test Approval',
            'description': 'A test approval',
            'content_type': ContentType.objects.get_for_model(self.purchase_order).pk,
            'object_id': self.purchase_order.pk,
            'content_object': self.purchase_order.get_api_url(),
        }
        pk = self.post(reverse('api-approval-list'), data, expected_code=201).data['id']
        url_detail = reverse('api-approval-detail', kwargs={'pk': pk})
        url_dec = reverse('api-approval-decision-list', kwargs={'pk': pk})

        # Check that the approval has been created
        response = self.get(url_detail)
        self.state_check(response.data, 0, http=True)

        # Add a decision to the approval
        self.post(url_dec, {'decision': True, 'approval': pk}, expected_code=201)

        # Check that the approval has one decision
        response = self.get(url_detail)
        self.state_check(response.data, 10, usr=self.user, http=True)

        # Add a second decision to the approval
        self.client.login(username=self.user1, password='password')
        self.post(url_dec, {'decision': True, 'approval': pk}, expected_code=201)

        # Check that the approval has two decisions
        response = self.get(url_detail)
        self.state_check(response.data, 20, usr=self.user1, http=True)
