"""
Unit tests for RepairOrder model, serializers, and API endpoints.
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from inventree.order.models import (
    RepairOrder,
    RepairOrderLineItem,
    RepairOrderStatus,
    Order,
)
from inventree.order.serializers import (
    RepairOrderSerializer,
    RepairOrderLineItemSerializer,
    RepairOrderCreateSerializer,
    RepairOrderUpdateSerializer,
)
from inventree.stock.models import StockItem, StockLocation
from inventree.part.models import Part, PartCategory
from inventree.company.models import Company, CompanyType
from inventree.users.models import User


User = get_user_model()


class RepairOrderModelTests(TestCase):
    """Test cases for RepairOrder model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.customer = Company.objects.create(
            name='Test Customer',
            company_type=CompanyType.CUSTOMER,
            is_customer=True
        )
        self.location = StockLocation.objects.create(
            name='Test Location',
            path='test/location'
        )
        self.customer_unit = StockItem.objects.create(
            part=Part.objects.create(
                name='Test Part',
                description='A test part',
                category=PartCategory.objects.create(
                    name='Test Category',
                    description='Test category'
                )
            ),
            quantity=1,
            location=self.location
        )
        self.repair_order = RepairOrder.objects.create(
            order_id='REP-0001',
            customer=self.customer,
            customer_unit=self.customer_unit,
            description='Repair of test unit',
            created_by=self.user,
            status=RepairOrderStatus.PENDING
        )

    def test_repair_order_creation(self):
        """Test that a RepairOrder can be created with required fields."""
        self.assertEqual(self.repair_order.order_id, 'REP-0001')
        self.assertEqual(self.repair_order.customer, self.customer)
        self.assertEqual(self.repair_order.customer_unit, self.customer_unit)
        self.assertEqual(self.repair_order.description, 'Repair of test unit')
        self.assertEqual(self.repair_order.created_by, self.user)
        self.assertEqual(self.repair_order.status, RepairOrderStatus.PENDING)
        self.assertIsNotNone(self.repair_order.creation_date)

    def test_repair_order_str(self):
        """Test the string representation of RepairOrder."""
        expected_str = f"Repair Order REP-0001 - {self.customer.name}"
        self.assertEqual(str(self.repair_order), expected_str)

    def test_repair_order_status_transitions(self):
        """Test valid status transitions for RepairOrder."""
        # PENDING -> IN_PROGRESS
        self.repair_order.status = RepairOrderStatus.IN_PROGRESS
        self.repair_order.save()
        self.assertEqual(self.repair_order.status, RepairOrderStatus.IN_PROGRESS)

        # IN_PROGRESS -> COMPLETED
        self.repair_order.status = RepairOrderStatus.COMPLETED
        self.repair_order.save()
        self.assertEqual(self.repair_order.status, RepairOrderStatus.COMPLETED)

        # COMPLETED -> CANCELLED (should be allowed)
        self.repair_order.status = RepairOrderStatus.CANCELLED
        self.repair_order.save()
        self.assertEqual(self.repair_order.status, RepairOrderStatus.CANCELLED)

    def test_repair_order_invalid_status_transition(self):
        """Test that invalid status transitions raise appropriate errors."""
        # Cannot go from PENDING directly to COMPLETED without IN_PROGRESS
        with self.assertRaises(ValueError):
            self.repair_order.status = RepairOrderStatus.COMPLETED
            self.repair_order.save()

    def test_repair_order_line_item_creation(self):
        """Test that line items can be added to a RepairOrder."""
        part = Part.objects.create(
            name='Replacement Part',
            description='A replacement part for repair',
            category=PartCategory.objects.create(
                name='Replacement Category',
                description='Replacement parts'
            )
        )
        line_item = RepairOrderLineItem.objects.create(
            order=self.repair_order,
            part=part,
            quantity=2,
            unit_price=10.00,
            description='Replacement widget'
        )
        self.assertEqual(line_item.order, self.repair_order)
        self.assertEqual(line_item.part, part)
        self.assertEqual(line_item.quantity, 2)
        self.assertEqual(line_item.unit_price, 10.00)
        self.assertEqual(line_item.description, 'Replacement widget')

    def test_repair_order_total_cost(self):
        """Test calculation of total cost for a RepairOrder."""
        part1 = Part.objects.create(
            name='Part 1',
            description='First part',
            category=PartCategory.objects.create(
                name='Category 1',
                description='First category'
            )
        )
        part2 = Part.objects.create(
            name='Part 2',
            description='Second part',
            category=PartCategory.objects.create(
                name='Category 2',
                description='Second category'
            )
        )
        RepairOrderLineItem.objects.create(
            order=self.repair_order,
            part=part1,
            quantity=3,
            unit_price=15.00,
            description='Three widgets'
        )
        RepairOrderLineItem.objects.create(
            order=self.repair_order,
            part=part2,
            quantity=1,
            unit_price=25.00,
            description='One gadget'
        )
        expected_total = (3 * 15.00) + (1 * 25.00)
        self.assertEqual(self.repair_order.total_cost, expected_total)

    def test_repair_order_requires_customer_unit(self):
        """Test that a RepairOrder requires a customer_unit."""
        with self.assertRaises(Exception):
            RepairOrder.objects.create(
                order_id='REP-0002',
                customer=self.customer,
                description='Missing customer unit',
                created_by=self.user
            )


class RepairOrderSerializerTests(TestCase):
    """Test cases for RepairOrder serializers."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.customer = Company.objects.create(
            name='Test Customer',
            company_type=CompanyType.CUSTOMER,
            is_customer=True
        )
        self.location = StockLocation.objects.create(
            name='Test Location',
            path='test/location'
        )
        self.customer_unit = StockItem.objects.create(
            part=Part.objects.create(
                name='Test Part',
                description='A test part',
                category=PartCategory.objects.create(
                    name='Test Category',
                    description='Test category'
                )
            ),
            quantity=1,
            location=self.location
        )
        self.repair_order = RepairOrder.objects.create(
            order_id='REP-0001',
            customer=self.customer,
            customer_unit=self.customer_unit,
            description='Repair of test unit',
            created_by=self.user,
            status=RepairOrderStatus.PENDING
        )

    def test_repair_order_serializer_valid_data(self):
        """Test that RepairOrderSerializer accepts valid data."""
        data = {
            'order_id': 'REP-0002',
            'customer': self.customer.pk,
            'customer_unit': self.customer_unit.pk,
            'description': 'Another repair',
            'created_by': self.user.pk,
            'status': RepairOrderStatus.PENDING
        }
        serializer = RepairOrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()
        self.assertEqual(order.order_id, 'REP-0002')

    def test_repair_order_serializer_invalid_data(self):
        """Test that RepairOrderSerializer rejects invalid data."""
        data = {
            'order_id': '',  # Empty order_id
            'customer': None,  # Missing customer
            'customer_unit': None,  # Missing customer_unit
        }
        serializer = RepairOrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('order_id', serializer.errors)
        self.assertIn('customer', serializer.errors)
        self.assertIn('customer_unit', serializer.errors)

    def test_repair_order_create_serializer(self):
        """Test RepairOrderCreateSerializer."""
        data = {
            'order_id': 'REP-0003',
            'customer': self.customer.pk,
            'customer_unit': self.customer_unit.pk,
            'description': 'New repair order',
            'line_items': [
                {
                    'part': Part.objects.create(
                        name='New Part',
                        description='New part',
                        category=PartCategory.objects.create(
                            name='New Category',
                            description='New category'
                        )
                    ).pk,
                    'quantity': 1,
                    'unit_price': 50.00,
                    'description': 'New line item'
                }
            ]
        }
        serializer = RepairOrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save(created_by=self.user)
        self.assertEqual(order.order_id, 'REP-0003')
        self.assertEqual(order.line_items.count(), 1)

    def test_repair_order_update_serializer(self):
        """Test RepairOrderUpdateSerializer."""
        data = {
            'description': 'Updated repair description',
            'status': RepairOrderStatus.IN_PROGRESS
        }
        serializer = RepairOrderUpdateSerializer(
            instance=self.repair_order,
            data=data,
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_order = serializer.save()
        self.assertEqual(updated_order.description, 'Updated repair description')
        self.assertEqual(updated_order.status, RepairOrderStatus.IN_PROGRESS)

    def test_repair_order_line_item_serializer(self):
        """Test RepairOrderLineItemSerializer."""
        part = Part.objects.create(
            name='Line Item Part',
            description='Part for line item',
            category=PartCategory.objects.create(
                name='Line Item Category',
                description='Line item category'
            )
        )
        line_item = RepairOrderLineItem.objects.create(
            order=self.repair_order,
            part=part,
            quantity=5,
            unit_price=12.50,
            description='Five items'
        )
        serializer = RepairOrderLineItemSerializer(line_item)
        self.assertEqual(serializer.data['quantity'], 5)
        self.assertEqual(serializer.data['unit_price'], '12.50')
        self.assertEqual(serializer.data['description'], 'Five items')


class RepairOrderAPITests(APITestCase):
    """Test cases for RepairOrder API endpoints."""

    def setUp(self):
        """Set up test data and authenticate."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.customer = Company.objects.create(
            name='Test Customer',
            company_type=CompanyType.CUSTOMER,
            is_customer=True
        )
        self.location = StockLocation.objects.create(
            name='Test Location',
            path='test/location'
        )
        self.customer_unit = StockItem.objects.create(
            part=Part.objects.create(
                name='Test Part',
                description='A test part',
                category=PartCategory.objects.create(
                    name='Test Category',
                    description='Test category'
                )
            ),
            quantity=1,
            location=self.location
        )
        self.repair_order = RepairOrder.objects.create(
            order_id='REP-0001',
            customer=self.customer,
            customer_unit=self.customer_unit,
            description='Repair of test unit',
            created_by=self.user,
            status=RepairOrderStatus.PENDING
        )

    def test_list_repair_orders(self):
        """Test GET request to list repair orders."""
        url = reverse('api-repair-order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['order_id'], 'REP-0001')

    def test_create_repair_order(self):
        """Test POST request to create a repair order."""
        url = reverse('api-repair-order-list')
        data = {
            'order_id': 'REP-0002',
            'customer': self.customer.pk,
            'customer_unit': self.customer_unit.pk,
            'description': 'New repair order via API',
            'status': RepairOrderStatus.PENDING
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RepairOrder.objects.count(), 2)
        self.assertEqual(response.data['order_id'], 'REP-0002')

    def test_retrieve_repair_order(self):
        """Test GET request to retrieve a specific repair order."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.repair_order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_id'], 'REP-0001')
        self.assertEqual(response.data['customer'], self.customer.pk)

    def test_update_repair_order(self):
        """Test PUT request to update a repair order."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.repair_order.pk})
        data = {
            'order_id': 'REP-0001',
            'customer': self.customer.pk,
            'customer_unit': self.customer_unit.pk,
            'description': 'Updated repair description',
            'status': RepairOrderStatus.IN_PROGRESS
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.repair_order.refresh_from_db()
        self.assertEqual(self.repair_order.description, 'Updated repair description')
        self.assertEqual(self.repair_order.status, RepairOrderStatus.IN_PROGRESS)

    def test_partial_update_repair_order(self):
        """Test PATCH request to partially update a repair order."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.repair_order.pk})
        data = {'description': 'Partially updated description'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.repair_order.refresh_from_db()
        self.assertEqual(self.repair_order.description, 'Partially updated description')

    def test_delete_repair_order(self):
        """Test DELETE request to delete a repair order."""
        url = reverse('api-repair-order-detail', kwargs={'pk': self.repair_order.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RepairOrder.objects.count(), 0)

    def test_list_repair_order_line_items(self):
        """Test GET request to list line items for a repair order."""
        part = Part.objects.create(
            name='API Test Part',
            description='Part for API test',
            category=PartCategory.objects.create(
                name='API Test Category',
                description='API test category'
            )
        )
        RepairOrderLineItem.objects.create(
            order=self.repair_order,
            part=part,
            quantity=3,
            unit_price=20.00,
            description='API test line item'
        )
        url = reverse('api-repair-order-line-item-list', kwargs={'order_pk': self.repair_order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['quantity'], 3)

    def test_create_repair_order_line_item(self):
        """Test POST request to create a line item for a repair order."""
        part = Part.objects.create(
            name='New API Part',
            description='New part for API',
            category=PartCategory.objects.create(
                name='New API Category',
                description='New API category'
            )
        )
        url = reverse('api-repair-order-line-item-list', kwargs={'order_pk': self.repair_order.pk})
        data = {
            'part': part.pk,
            'quantity': 2,
            'unit_price': 15.00,
            'description': 'New line item via API'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.repair_order.line_items.count(), 1)

    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are rejected."""
        self.client.logout()
        url = reverse('api-repair-order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_repair_orders_by_status(self):
        """Test filtering repair orders by status."""
        # Create another repair order with different status
        RepairOrder.objects.create(
            order_id='REP-0003',
            customer=self.customer,
            customer_unit=self.customer_unit,
            description='Another repair',
            created_by=self.user,
            status=RepairOrderStatus.COMPLETED
        )
        url = reverse('api-repair-order-list')
        response = self.client.get(url, {'status': RepairOrderStatus.PENDING})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], RepairOrderStatus.PENDING)

    def test_search_repair_orders(self):
        """Test searching repair orders by order_id or description."""
        url = reverse('api-repair-order-list')
        response = self.client.get(url, {'search': 'REP-0001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['order_id'], 'REP-0001')

    def test_ordering_repair_orders(self):
        """Test ordering repair orders by creation_date."""
        # Create another repair order
        RepairOrder.objects.create(
            order_id='REP-0004',
            customer=self.customer,
            customer_unit=self.customer_unit,
            description='Older repair',
            created_by=self.user,
            status=RepairOrderStatus.PENDING,
            creation_date=