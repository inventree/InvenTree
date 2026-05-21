"""POS sales webhook — orchestrates sales-order workflow from receipt data."""

from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

import requests
import structlog
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

import common.settings
import company.models as company_models
import stock.models as stock_models
from InvenTree.mixins import CreateAPI
from order import models, serializers
from order.status_codes import SalesOrderStatus, SalesOrderStatusGroups
from part.models import Part

logger = structlog.get_logger('inventree')


class PosSalesOrchestrator:
    """Runs the sales-order workflow using InvenTree models and serializers.

    Orchestrates the complete POS sale workflow from receipt data to completed shipment.
    """

    def __init__(self, user: User):
        """Initialize the orchestrator with a service user."""
        self.user = user
        self.request_context = {'request': _FakeRequest(user)}

    def process_sale(self, receipt_id: str, location_id: str) -> models.SalesOrder:
        """End-to-end POS sale processing.

        Workflow (InvenTree-recommended order):
        fetch receipt → create order → lines → issue → shipment → allocate → check →
        complete shipment (async) → ship order → complete order.
        """
        from django.db import transaction

        line_specs = self._parse_receipt_lines(receipt_id)
        customer = self._get_or_create_location_customer(location_id)
        stock_location = self._resolve_stock_location(location_id)

        sales_order = self._get_or_create_sales_order(receipt_id, customer)

        if sales_order.lines.exists():
            logger.info(
                'POS sale already processed',
                receipt_id=receipt_id,
                sales_order_pk=sales_order.pk,
            )
            return sales_order

        shipment: models.SalesOrderShipment

        # DB steps that must commit before the background shipment task runs.
        with transaction.atomic():
            self._create_line_items(sales_order, line_specs)
            self._issue_order(sales_order)
            shipment = self._create_shipment(sales_order, receipt_id)
            self._allocate_stock(sales_order, shipment, line_specs, stock_location)
            self._check_shipment(shipment)

        task_id = self._complete_shipment(shipment)
        self._wait_for_background_task(task_id)

        self._ship_sales_order(sales_order)
        self._complete_sales_order(sales_order)

        sales_order.refresh_from_db()
        return sales_order

    def _get_or_create_location_customer(
        self, location_id: str
    ) -> company_models.Company:
        """Each POS location maps to a dedicated InvenTree customer company."""
        prefix = 'POS Location'  # Can be made configurable
        name = f'{prefix} {location_id}'

        customer = company_models.Company.objects.filter(
            name=name, is_customer=True
        ).first()

        if customer:
            return customer

        customer = company_models.Company.objects.create(
            name=name,
            description=f'Auto-created for POS location_id={location_id}',
            is_customer=True,
            is_supplier=False,
            active=True,
        )

        logger.info(
            'Created POS customer', location_id=location_id, customer_pk=customer.pk
        )
        return customer

    def _resolve_stock_location(self, location_id: str) -> stock_models.StockLocation:
        """Resolve external location_id to an InvenTree stock location."""
        # Try exact location_id match
        try:
            return stock_models.StockLocation.objects.get(pk=location_id)
        except (stock_models.StockLocation.DoesNotExist, ValueError):
            pass

        # Fallback: match by name
        location = stock_models.StockLocation.objects.filter(name=location_id).first()

        if location:
            return location

        raise ValueError(
            _(
                'No stock location found for location_id=%(loc)s. '
                'Provide a valid StockLocation pk or name.'
            )
            % {'loc': location_id}
        )

    def _get_or_create_sales_order(
        self, receipt_id: str, customer: company_models.Company
    ) -> models.SalesOrder:
        """Idempotent sales order keyed by POS receipt id."""
        reference = f'POS-{receipt_id}'

        existing = models.SalesOrder.objects.filter(reference=reference).first()

        if existing:
            return existing

        return models.SalesOrder.objects.create(
            reference=reference,
            customer=customer,
            description=f'POS receipt {receipt_id}',
            created_by=self.user,
        )

    def _parse_receipt_lines(self, receipt_id: str) -> list[dict[str, Any]]:
        """Fetch and normalize itemized receipt data from the external POS API."""
        endpoint = common.settings.get_global_setting(
            'PA_RECEIPT_API_ENDPOINT', environment_key='PA_RECEIPT_API_ENDPOINT'
        )
        api_key = common.settings.get_global_setting(
            'PA_RECEIPT_API_KEY', environment_key='PA_RECEIPT_API_KEY'
        )

        if not endpoint:
            raise ValueError(
                _(
                    'POS receipt API endpoint is not configured. '
                    'Set PA_RECEIPT_API_ENDPOINT in the environment or database.'
                )
            )

        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'}

        try:
            response = requests.get(
                endpoint, headers=headers, params={'receipt_id': receipt_id}, timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise ValueError(
                _('POS receipt API timed out for receipt %(id)s') % {'id': receipt_id}
            ) from exc
        except requests.exceptions.HTTPError:
            raise ValueError(
                _('POS receipt API returned %(status)s for receipt %(id)s')
                % {'status': response.status_code, 'id': receipt_id}
            )
        except requests.exceptions.ConnectionError as exc:
            raise ValueError(
                _('POS receipt API is unreachable for receipt %(id)s')
                % {'id': receipt_id}
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(
                _('POS receipt API returned invalid JSON for receipt %(id)s')
                % {'id': receipt_id}
            ) from exc

        lines = data.get('lines') or data.get('items') or data.get('line_items')

        if not lines:
            raise ValueError(
                _('Receipt %(id)s contains no line items in the POS response')
                % {'id': receipt_id}
            )

        normalized: list[dict[str, Any]] = []
        for entry in lines:
            if not isinstance(entry, dict):
                continue

            quantity = entry.get('quantity') or entry.get('qty') or 0

            normalized.append({
                'part_id': entry.get('part_id') or entry.get('partId'),
                'sku': entry.get('sku') or entry.get('ipn') or entry.get('part_number'),
                'barcode': entry.get('barcode') or entry.get('barcode_hash'),
                'quantity': Decimal(str(quantity)),
            })

        if not normalized:
            raise ValueError(
                _('No usable line items in receipt %(id)s') % {'id': receipt_id}
            )

        logger.info(
            'Fetched POS receipt lines',
            receipt_id=receipt_id,
            line_count=len(normalized),
        )

        return normalized

    def _create_line_items(
        self, sales_order: models.SalesOrder, line_specs: list[dict[str, Any]]
    ) -> list[models.SalesOrderLineItem]:
        """Create sales order line items from receipt lines."""
        created: list[models.SalesOrderLineItem] = []

        for spec in line_specs:
            part = self._resolve_part(spec)

            if not part.salable:
                raise ValueError(
                    _('Part %(part)s is not salable') % {'part': part.name}
                )

            line = models.SalesOrderLineItem.objects.create(
                order=sales_order,
                part=part,
                quantity=spec['quantity'],
                reference=spec.get('sku') or part.IPN,
            )
            created.append(line)

        return created

    def _resolve_part(self, spec: dict[str, Any]) -> Part:
        """Resolve a receipt line to an InvenTree Part."""
        if spec.get('part_id'):
            return Part.objects.get(pk=spec['part_id'])

        if spec.get('sku'):
            match = Part.objects.filter(IPN=spec['sku']).first()

            if match:
                return match

        if spec.get('barcode'):
            item = stock_models.StockItem.lookup_barcode(spec['barcode'])

            if item:
                return item.part

        raise ValueError(
            _('Could not resolve part for line: %(line)s') % {'line': spec}
        )

    def _issue_order(self, sales_order: models.SalesOrder) -> None:
        """Issue the sales order (PENDING → IN_PROGRESS)."""
        if not sales_order.can_issue:
            return

        serializer = serializers.SalesOrderIssueSerializer(
            data={}, context={**self.request_context, 'order': sales_order}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _create_shipment(
        self, sales_order: models.SalesOrder, receipt_id: str
    ) -> models.SalesOrderShipment:
        """Create a single shipment for this POS sale."""
        return models.SalesOrderShipment.objects.create(
            order=sales_order, reference=f'POS-SHP-{receipt_id}'
        )

    def _allocate_stock(
        self,
        sales_order: models.SalesOrder,
        shipment: models.SalesOrderShipment,
        line_specs: list[dict[str, Any]],
        stock_location: stock_models.StockLocation,
    ) -> None:
        """Allocate stock from the configured location for each line."""
        allocation_items = []

        locations = stock_location.get_descendants(include_self=True)

        for spec in line_specs:
            part = self._resolve_part(spec)
            line = sales_order.lines.filter(part=part).first()

            if not line:
                raise ValueError(
                    _('No sales order line for part %(part)s') % {'part': part.pk}
                )

            remaining = spec['quantity']

            stock_qs = stock_models.StockItem.objects.filter(
                part=part, location__in=locations
            ).order_by('pk')

            for stock_item in stock_qs:
                if remaining <= 0:
                    break

                available = stock_item.unallocated_quantity()

                if available <= 0:
                    continue

                take = min(remaining, available)

                allocation_items.append({
                    'line_item': line,
                    'stock_item': stock_item,
                    'quantity': take,
                })

                remaining -= take

            if remaining > 0:
                raise ValueError(
                    _(
                        'Insufficient stock for part %(part)s at location %(loc)s '
                        '(short by %(qty)s)'
                    )
                    % {'part': part.name, 'loc': stock_location.name, 'qty': remaining}
                )

        serializer_obj = serializers.SalesOrderShipmentAllocationSerializer(
            data={'items': allocation_items, 'shipment': shipment.pk},
            context={**self.request_context, 'order': sales_order},
        )
        serializer_obj.is_valid(raise_exception=True)
        serializer_obj.save()

    def _check_shipment(self, shipment: models.SalesOrderShipment) -> None:
        """Mark shipment as checked (required when SALESORDER_SHIPMENT_REQUIRES_CHECK)."""
        shipment.checked_by = self.user
        shipment.save(update_fields=['checked_by'])

    def _complete_shipment(self, shipment: models.SalesOrderShipment) -> str:
        """Complete shipment; returns background task id."""
        shipment.check_can_complete(raise_error=True)
        return shipment.complete_shipment(self.user)

    def _wait_for_background_task(
        self, task_id: str | bool | None, timeout_seconds: int = 120
    ) -> None:
        """Wait for django-q shipment completion task."""
        import time

        import django_q.models

        if task_id is None or isinstance(task_id, bool):
            return

        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            if django_q.models.Success.objects.filter(id=task_id).exists():
                return

            if django_q.models.Failure.objects.filter(id=task_id).exists():
                raise RuntimeError(
                    _('Background task %(task)s failed') % {'task': task_id}
                )

            time.sleep(1)

        raise TimeoutError(
            _('Timed out waiting for background task %(task)s') % {'task': task_id}
        )

    def _ship_sales_order(self, sales_order: models.SalesOrder) -> None:
        """Mark sales order as shipped (InvenTree 'Complete Order' UI action)."""
        sales_order.refresh_from_db()

        if sales_order.status in SalesOrderStatusGroups.COMPLETE:
            return

        serializer_obj = serializers.SalesOrderCompleteSerializer(
            data={'accept_incomplete': False},
            context={**self.request_context, 'order': sales_order},
        )
        serializer_obj.is_valid(raise_exception=True)
        serializer_obj.save()

    def _complete_sales_order(self, sales_order: models.SalesOrder) -> None:
        """Transition order to COMPLETE status when still open after shipping."""
        sales_order.refresh_from_db()

        if sales_order.status == SalesOrderStatus.COMPLETE.value:
            return

        if sales_order.status == SalesOrderStatus.SHIPPED.value:
            sales_order.complete_order(self.user)


class _FakeRequest:
    """Minimal request object for serializer context."""

    def __init__(self, user: User):
        """Initialize with a user."""
        self.user = user


class PosSalesWebhook(CreateAPI):
    """API endpoint for POS sales webhook.

    Receives POS webhook events and orchestrates the sales order workflow.

    POST /api/sales/pos-webhook/
    """

    queryset = models.SalesOrder.objects.none()
    serializer_class = serializers.PosWebhookInboundSerializer

    def create(self, request, *args, **kwargs):
        """Process incoming POS webhook and orchestrate sales order creation."""
        try:
            receipt_id, location_id = self._parse_inbound_webhook(request.data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            'POS webhook received', receipt_id=receipt_id, location_id=location_id
        )

        try:
            user = self._get_service_user()
        except Exception as exc:
            logger.exception('POS service user misconfigured')
            return Response(
                {'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            orchestrator = PosSalesOrchestrator(user)
            sales_order = orchestrator.process_sale(receipt_id, location_id)
        except (ValueError, DRFValidationError) as exc:
            logger.warning('POS sale rejected', error=str(exc))
            detail = exc.detail if isinstance(exc, DRFValidationError) else str(exc)
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception('POS sale failed')
            return Response(
                {'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        payload = {
            'success': True,
            'receipt_id': receipt_id,
            'location_id': location_id,
            'sales_order_id': sales_order.pk,
            'sales_order_reference': sales_order.reference,
            'message': _('POS sale processed successfully'),
        }

        return Response(payload, status=status.HTTP_201_CREATED)

    @staticmethod
    def _parse_inbound_webhook(data: dict) -> tuple[str, str]:
        """Extract receipt and location identifiers from the inbound webhook body."""
        receipt_id = data.get('receipt_id') or data.get('id')
        location_id = data.get('location_id') or data.get('location')

        if not receipt_id:
            raise ValueError(_('Missing receipt_id in webhook payload'))
        if not location_id:
            raise ValueError(_('Missing location_id in webhook payload'))

        return str(receipt_id), str(location_id)

    @staticmethod
    def _get_service_user() -> User:
        """Return the configured service account (defaults to 'admin')."""
        User = get_user_model()

        try:
            return User.objects.get(username='admin')
        except User.DoesNotExist as exc:
            raise ValueError(_('Service user "admin" does not exist')) from exc
