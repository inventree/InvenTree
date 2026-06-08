"""
Repair Order API views for InvenTree order management.

Provides CRUD endpoints for RepairOrder and RepairOrderLineItem models,
following the established pattern of PurchaseOrder and SalesOrder views.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpRequest
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from common.models import InvenTreeSetting
from company.models import Company
from order.models import RepairOrder, RepairOrderLineItem, Order, OrderStatus
from order.serializers import (
    RepairOrderSerializer,
    RepairOrderLineItemSerializer,
    RepairOrderCreateSerializer,
    RepairOrderLineItemCreateSerializer,
)
from part.models import Part
from stock.models import StockItem
from InvenTree.views import TreeView, ListCreateAPI, RetrieveUpdateDestroyAPI
from InvenTree.mixins import (
    ListAPI,
    CreateAPI,
    RetrieveAPI,
    UpdateAPI,
    DestroyAPI,
    RetrieveUpdateDestroyAPI as StandardRetrieveUpdateDestroyAPI,
)

# Configure logger
logger = logging.getLogger(__name__)


class RepairOrderViewSet(
    ListCreateAPI,
    RetrieveUpdateDestroyAPI,
):
    """
    API endpoint for managing Repair Orders.

    Provides list, create, retrieve, update, and destroy operations
    for RepairOrder instances. Supports filtering, searching, and ordering.

    Attributes:
        queryset: Base queryset for all RepairOrder instances
        serializer_class: Default serializer for RepairOrder
        permission_classes: Required permissions for accessing this endpoint
        filter_backends: List of filter backends for querying
        filterset_fields: Fields available for exact filtering
        search_fields: Fields available for text search
        ordering_fields: Fields available for ordering results
        ordering: Default ordering for results
    """

    queryset = RepairOrder.objects.all()
    serializer_class = RepairOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends: List[Type] = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields: List[str] = [
        'status',
        'customer',
        'customer_unit',
        'created_by',
        'creation_date',
        'target_date',
        'responsible',
    ]
    search_fields: List[str] = [
        'reference',
        'description',
        'customer__name',
        'customer_unit__serial',
        'notes',
    ]
    ordering_fields: List[str] = [
        'reference',
        'creation_date',
        'target_date',
        'status',
        'customer__name',
    ]
    ordering: List[str] = ['-creation_date']

    def get_serializer_class(self) -> Type[Serializer]:
        """
        Return appropriate serializer based on action.

        Returns:
            Type[Serializer]: The serializer class appropriate for the current action

        Raises:
            ValueError: If action is not recognized
        """
        try:
            if self.action == 'create':
                return RepairOrderCreateSerializer
            elif self.action in ('retrieve', 'update', 'partial_update', 'list'):
                return RepairOrderSerializer
            else:
                logger.warning(f"Unknown action '{self.action}', using default serializer")
                return RepairOrderSerializer
        except Exception as e:
            logger.error(f"Error determining serializer class: {str(e)}")
            raise

    def perform_create(self, serializer: Serializer) -> None:
        """
        Create a new RepairOrder with additional business logic.

        Args:
            serializer: Validated serializer instance for creating the order

        Raises:
            PermissionDenied: If user is not authenticated
            ValidationError: If business logic validation fails
            IntegrityError: If database integrity constraints are violated
        """
        try:
            with transaction.atomic():
                # Validate user is authenticated
                if not self.request.user or not self.request.user.is_authenticated:
                    raise PermissionDenied("User must be authenticated to create repair orders")

                repair_order = serializer.save(
                    created_by=self.request.user,
                    order_type=Order.REPAIR_ORDER,
                )

                # Auto-assign reference number if not provided
                if not repair_order.reference:
                    try:
                        repair_order.reference = repair_order.generate_reference()
                        repair_order.save()
                        logger.info(
                            f"Auto-generated reference {repair_order.reference} "
                            f"for repair order {repair_order.pk}"
                        )
                    except Exception as ref_error:
                        logger.error(
                            f"Failed to generate reference for repair order: {str(ref_error)}"
                        )
                        raise ValidationError(
                            f"Failed to generate reference: {str(ref_error)}"
                        )

                logger.info(
                    f"Created repair order {repair_order.reference} "
                    f"by user {self.request.user.username}"
                )

        except PermissionDenied:
            logger.error("Permission error creating repair order")
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create repair order: {str(e)}")
            raise ValidationError(f"Failed to create repair order: {str(e)}")

    def get_object(self) -> RepairOrder:
        """
        Retrieve a single RepairOrder instance with error handling.

        Returns:
            RepairOrder: The requested repair order instance

        Raises:
            NotFound: If the repair order does not exist
        """
        try:
            return super().get_object()
        except Http404:
            logger.warning(f"RepairOrder with pk={self.kwargs.get('pk')} not found")
            raise NotFound("Repair order not found")
        except Exception as e:
            logger.error(f"Error retrieving repair order: {str(e)}")
            raise

    def _validate_order_status_transition(
        self,
        repair_order: RepairOrder,
        allowed_statuses: List[OrderStatus],
        action_name: str
    ) -> Optional[Response]:
        """
        Validate if the order status allows the requested action.

        Args:
            repair_order: The repair order to validate
            allowed_statuses: List of statuses that allow the action
            action_name: Name of the action for error messages

        Returns:
            Optional[Response]: Error response if validation fails, None otherwise
        """
        if repair_order.status not in allowed_statuses:
            error_msg = (
                f"Cannot {action_name} repair order {repair_order.reference}: "
                f"current status '{repair_order.status}' not in allowed statuses "
                f"{[s.value for s in allowed_statuses]}"
            )
            logger.warning(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None

    @action(detail=True, methods=['post'])
    def issue(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        Issue the repair order, changing status to 'In Progress'.

        Args:
            request: HTTP request object
            pk: Primary key of the repair order

        Returns:
            Response: Updated repair order data or error message

        Raises:
            NotFound: If repair order not found
            ValidationError: If status transition is invalid
        """
        try:
            repair_order = self.get_object()
            
            # Validate status transition
            validation_error = self._validate_order_status_transition(
                repair_order,
                [OrderStatus.PENDING, OrderStatus.ON_HOLD],
                'issue'
            )
            if validation_error:
                return validation_error

            with transaction.atomic():
                repair_order.status = OrderStatus.IN_PROGRESS
                repair_order.save()
                
                logger.info(
                    f"Repair order {repair_order.reference} issued by "
                    f"user {request.user.username}"
                )
                
                serializer = self.get_serializer(repair_order)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except NotFound:
            raise
        except Exception as e:
            logger.error(f"Failed to issue repair order: {str(e)}")
            return Response(
                {'error': f"Failed to issue repair order: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def complete(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        Complete the repair order, changing status to 'Completed'.

        Args:
            request: HTTP request object
            pk: Primary key of the repair order

        Returns:
            Response: Updated repair order data or error message

        Raises:
            NotFound: If repair order not found
            ValidationError: If status transition is invalid
        """
        try:
            repair_order = self.get_object()
            
            # Validate status transition
            validation_error = self._validate_order_status_transition(
                repair_order,
                [OrderStatus.IN_PROGRESS],
                'complete'
            )
            if validation_error:
                return validation_error

            with transaction.atomic():
                repair_order.status = OrderStatus.COMPLETED
                repair_order.save()
                
                logger.info(
                    f"Repair order {repair_order.reference} completed by "
                    f"user {request.user.username}"
                )
                
                serializer = self.get_serializer(repair_order)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except NotFound:
            raise
        except Exception as e:
            logger.error(f"Failed to complete repair order: {str(e)}")
            return Response(
                {'error': f"Failed to complete repair order: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        Cancel the repair order, changing status to 'Cancelled'.

        Args:
            request: HTTP request object
            pk: Primary key of the repair order

        Returns:
            Response: Updated repair order data or error message

        Raises:
            NotFound: If repair order not found
            ValidationError: If status transition is invalid
        """
        try:
            repair_order = self.get_object()
            
            # Validate status transition
            validation_error = self._validate_order_status_transition(
                repair_order,
                [OrderStatus.PENDING, OrderStatus.ON_HOLD, OrderStatus.IN_PROGRESS],
                'cancel'
            )
            if validation_error:
                return validation_error

            with transaction.atomic():
                repair_order.status = OrderStatus.CANCELLED
                repair_order.save()
                
                logger.info(
                    f"Repair order {repair_order.reference} cancelled by "
                    f"user {request.user.username}"
                )
                
                serializer = self.get_serializer(repair_order)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except NotFound:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel repair order: {str(e)}")
            return Response(
                {'error': f"Failed to cancel repair order: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def hold(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        Place the repair order on hold.

        Args:
            request: HTTP request object
            pk: Primary key of the repair order

        Returns:
            Response: Updated repair order data or error message

        Raises:
            NotFound: If repair order not found
            ValidationError: If status transition is invalid
        """
        try:
            repair_order = self.get_object()
            
            # Validate status transition
            validation_error = self._validate_order_status_transition(
                repair_order,
                [OrderStatus.PENDING, OrderStatus.IN_PROGRESS],
                'hold'
            )
            if validation_error:
                return validation_error

            with transaction.atomic():
                repair_order.status = OrderStatus.ON_HOLD
                repair_order.save()
                
                logger.info(
                    f"Repair order {repair_order.reference} placed on hold by "
                    f"user {request.user.username}"
                )
                
                serializer = self.get_serializer(repair_order)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except NotFound:
            raise
        except Exception as e:
            logger.error(f"Failed to hold repair order: {str(e)}")
            return Response(
                {'error': f"Failed to hold repair order: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RepairOrderLineItemViewSet(
    ListCreateAPI,
    RetrieveUpdateDestroyAPI,
):
    """
    API endpoint for managing Repair Order Line Items.

    Provides list, create, retrieve, update, and destroy operations
    for RepairOrderLineItem instances. Supports filtering and searching.

    Attributes:
        queryset: Base queryset for all RepairOrderLineItem instances
        serializer_class: Default serializer for RepairOrderLineItem
        permission_classes: Required permissions for accessing this endpoint
        filter_backends: List of filter backends for querying
        filterset_fields: Fields available for exact filtering
        search_fields: Fields available for text search
        ordering_fields: Fields available for ordering results
        ordering: Default ordering for results
    """

    queryset = RepairOrderLineItem.objects.all()
    serializer_class = RepairOrderLineItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends: List[Type] = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields: List[str] = [
        'order',
        'part',
        'stock_item',
        'quantity',
        'unit_price',
        'total_price',
    ]
    search_fields: List[str] = [
        'order__reference',
        'part__name',
        'part__IPN',
        'stock_item__serial',
        'notes',
    ]
    ordering_fields: List[str] = [
        'order__reference',
        'part__name',
        'quantity',
        'unit_price',
        'total_price',
    ]
    ordering: List[str] = ['order__reference', 'part__name']

    def get_serializer_class(self) -> Type[Serializer]:
        """
        Return appropriate serializer based on action.

        Returns:
            Type[Serializer]: The serializer class appropriate for the current action

        Raises:
            ValueError: If action is not recognized
        """
        try:
            if self.action == 'create':
                return RepairOrderLineItemCreateSerializer
            elif self.action in ('retrieve', 'update', 'partial_update', 'list'):
                return RepairOrderLineItemSerializer
            else:
                logger.warning(f"Unknown action '{self.action}', using default serializer")
                return RepairOrderLineItemSerializer
        except Exception as e:
            logger.error(f"Error determining serializer class: {str(e)}")
            raise

    def perform_create(self, serializer: Serializer) -> None:
        """
        Create a new RepairOrderLineItem with additional business logic.

        Args:
            serializer: Validated serializer instance for creating the line item

        Raises:
            PermissionDenied: If user is not authenticated
            ValidationError: If business logic validation fails
            IntegrityError: If database integrity constraints are violated
        """
        try:
            with transaction.atomic():
                # Validate user is authenticated
                if not self.request.user or not self.request.user.is_authenticated:
                    raise PermissionDenied("User must be authenticated to create line items")

                # Validate order exists and is in valid status
                order = serializer.validated_data.get('order')
                if order and order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
                    raise ValidationError(
                        f"Cannot add line items to order {order.reference} "
                        f"with status '{order.status}'"
                    )

                line_item = serializer.save()
                
                logger.info(
                    f"Created line item {line_item.pk} for repair order "
                    f"{line_item.order.reference} by user {self.request.user.username}"
                )

        except PermissionDenied:
            logger.error("Permission error creating line item")
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create line item: {str(e)}")
            raise ValidationError(f"Failed to create line item: {str(e)}")

    def get_object(self) -> RepairOrderLineItem:
        """
        Retrieve a single RepairOrderLineItem instance with error handling.

        Returns:
            RepairOrderLineItem: The requested line item instance

        Raises:
            NotFound: If the line item does not exist
        """
        try:
            return super().get_object()
        except Http404:
            logger.warning(f"RepairOrderLineItem with pk={self.kwargs.get('pk')} not found")
            raise NotFound("Line item not found")
        except Exception as e:
            logger.error(f"Error retrieving line item: {str(e)}")
            raise

    def perform_update(self, serializer: Serializer) -> None:
        """
        Update a RepairOrderLineItem with validation.

        Args:
            serializer: Validated serializer instance for updating the line item

        Raises:
            ValidationError: If business logic validation fails
        """
        try:
            with transaction.atomic():
                # Get the existing line item
                line_item = self.get_object()
                
                # Validate order status allows updates
                if line_item.order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
                    raise ValidationError(
                        f"Cannot update line items for order {line_item.order.reference} "
                        f"with status '{line_item.order.status}'"
                    )
                
                serializer.save()
                
                logger.info(
                    f"Updated line item {line_item.pk} for repair order "
                    f"{line_item.order.reference} by user {self.request.user.username}"
                )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to update line item: {str(e)}")
            raise ValidationError(f"Failed to update line item: {str(e)}")

    def perform_destroy(self, instance: RepairOrderLineItem) -> None:
        """
        Delete a RepairOrderLineItem with validation.

        Args:
            instance: The line item instance to delete

        Raises:
            ValidationError: If business logic validation fails
        """
        try:
            with transaction.atomic():
                # Validate order status allows deletion
                if instance.order.status not