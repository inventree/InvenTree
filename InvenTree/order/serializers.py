"""
Serializers for the RepairOrder and RepairOrderLineItem models.

Provides API serialization for repair orders and their line items,
following the existing patterns of PurchaseOrder and SalesOrder serializers.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Union, List, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, DatabaseError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from order.models import RepairOrder, RepairOrderLineItem, RepairOrderStatus
from order.serializers import OrderSerializer
from stock.serializers import StockItemSerializer
from stock.models import StockItem
from company.serializers import CompanySerializer
from company.models import Company
from part.serializers import PartBriefSerializer
from part.models import Part
from users.serializers import UserSerializer
from common.serializers import AttachmentSerializerMixin

# Configure module logger
logger = logging.getLogger(__name__)

# Constants for validation
MAX_QUANTITY = Decimal('9999999999')
MAX_PRICE = Decimal('999999999.99')
MIN_LINE_NUMBER = 1
MAX_LINE_NUMBER = 99999


class RepairOrderLineItemSerializer(serializers.ModelSerializer):
    """
    Serializer for RepairOrderLineItem model.

    Provides full serialization of repair order line items, including
    nested representations for related models. Handles validation,
    creation, and update operations with proper error handling and
    data integrity checks.

    Attributes:
        part_detail: Nested serialized part information (read-only)
        stock_item_detail: Nested serialized stock item information (read-only)
        repair_order: Primary key reference to parent repair order (read-only)
        line_item_type_display: Human-readable type description (read-only)
    """

    # Nested serializers for related fields
    part_detail = PartBriefSerializer(source='part', read_only=True)
    stock_item_detail = StockItemSerializer(source='stock_item', read_only=True)
    repair_order = serializers.PrimaryKeyRelatedField(read_only=True)

    # Readable field for the line item type
    line_item_type_display = serializers.SerializerMethodField()

    class Meta:
        """Meta configuration for RepairOrderLineItemSerializer."""

        model = RepairOrderLineItem
        fields = [
            'pk',
            'repair_order',
            'line_number',
            'part',
            'part_detail',
            'stock_item',
            'stock_item_detail',
            'quantity',
            'unit_price',
            'total_price',
            'line_item_type',
            'line_item_type_display',
            'description',
            'notes',
            'is_billable',
            'created_date',
            'modified_date',
        ]
        read_only_fields = [
            'pk',
            'repair_order',
            'created_date',
            'modified_date',
        ]

    def get_line_item_type_display(self, obj: RepairOrderLineItem) -> Optional[str]:
        """
        Return the human-readable display value for line_item_type.

        Args:
            obj: The RepairOrderLineItem instance

        Returns:
            Human-readable type string or None if not set

        Raises:
            AttributeError: If the model instance is invalid
        """
        try:
            if obj.line_item_type is None:
                return None
            return obj.get_line_item_type_display()
        except AttributeError as exc:
            logger.warning(
                "Failed to get line item type display for item %s: %s",
                getattr(obj, 'pk', 'unknown'),
                exc,
            )
            return None
        except Exception as exc:
            logger.error(
                "Unexpected error getting line item type display: %s",
                exc,
                exc_info=True,
            )
            return None

    def validate_quantity(self, value: Union[int, float, Decimal]) -> Decimal:
        """
        Ensure quantity is positive and within acceptable bounds.

        Args:
            value: The quantity value to validate

        Returns:
            Validated quantity as Decimal

        Raises:
            ValidationError: If quantity is not positive or exceeds maximum
        """
        try:
            decimal_value = Decimal(str(value))
        except (TypeError, ValueError, InvalidOperation) as exc:
            logger.warning("Invalid quantity value provided: %s", value)
            raise ValidationError(
                _("Invalid quantity value provided. Must be a positive number.")
            ) from exc

        if decimal_value <= Decimal('0'):
            raise ValidationError(_("Quantity must be greater than zero."))

        if decimal_value > MAX_QUANTITY:
            raise ValidationError(
                _("Quantity exceeds maximum allowed value of %(max)s.") % {'max': MAX_QUANTITY}
            )

        return decimal_value

    def validate_unit_price(self, value: Optional[Union[int, float, Decimal]]) -> Optional[Decimal]:
        """
        Ensure unit price is non-negative if provided.

        Args:
            value: The unit price value to validate

        Returns:
            Validated unit price as Decimal or None

        Raises:
            ValidationError: If unit price is negative or exceeds maximum
        """
        if value is None:
            return None

        try:
            decimal_value = Decimal(str(value))
        except (TypeError, ValueError, InvalidOperation) as exc:
            logger.warning("Invalid unit price value provided: %s", value)
            raise ValidationError(
                _("Invalid unit price value provided. Must be a non-negative number.")
            ) from exc

        if decimal_value < Decimal('0'):
            raise ValidationError(_("Unit price cannot be negative."))

        if decimal_value > MAX_PRICE:
            raise ValidationError(
                _("Unit price exceeds maximum allowed value of %(max)s.") % {'max': MAX_PRICE}
            )

        return decimal_value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the line item data with cross-field validation.

        Performs comprehensive validation including:
        - Ensuring at least part or stock_item is specified
        - Validating stock_item has associated part
        - Checking consistency between part and stock_item
        - Validating line number range

        Args:
            attrs: Dictionary of field values to validate

        Returns:
            Validated attributes dictionary

        Raises:
            ValidationError: If validation fails
        """
        validated_attrs = attrs.copy()

        try:
            # Extract and validate part and stock_item
            part = validated_attrs.get('part')
            stock_item = validated_attrs.get('stock_item')

            # Ensure at least one reference is provided
            if not part and not stock_item:
                error_msg = _("Either part or stock_item must be specified.")
                raise ValidationError({
                    'part': error_msg,
                    'stock_item': error_msg,
                })

            # Validate stock_item reference
            if stock_item is not None:
                if not isinstance(stock_item, StockItem):
                    raise ValidationError({
                        'stock_item': _("Invalid stock item reference."),
                    })

                if stock_item.part is None:
                    raise ValidationError({
                        'stock_item': _("The selected stock item does not have an associated part."),
                    })

                # Validate part consistency if both provided
                if part is not None and stock_item.part != part:
                    raise ValidationError({
                        'part': _("Part does not match the stock item's part."),
                        'stock_item': _("Stock item does not match the specified part."),
                    })

                # Auto-set part from stock_item if not explicitly provided
                if part is None:
                    validated_attrs['part'] = stock_item.part

            # Validate line number
            line_number = validated_attrs.get('line_number')
            if line_number is not None:
                if not isinstance(line_number, int):
                    raise ValidationError({
                        'line_number': _("Line number must be an integer."),
                    })
                if line_number < MIN_LINE_NUMBER or line_number > MAX_LINE_NUMBER:
                    raise ValidationError({
                        'line_number': _(
                            "Line number must be between %(min)s and %(max)s."
                        ) % {'min': MIN_LINE_NUMBER, 'max': MAX_LINE_NUMBER},
                    })

            # Validate quantity is provided
            if 'quantity' not in validated_attrs:
                raise ValidationError({
                    'quantity': _("Quantity is required."),
                })

        except ValidationError:
            raise
        except Exception as exc:
            logger.error(
                "Unexpected error during line item validation: %s",
                exc,
                exc_info=True,
            )
            raise ValidationError(
                _("An unexpected error occurred during validation.")
            ) from exc

        return validated_attrs

    def create(self, validated_data: Dict[str, Any]) -> RepairOrderLineItem:
        """
        Create a new RepairOrderLineItem instance with auto-numbering.

        Automatically assigns a line number if not provided, ensuring
        sequential ordering within the repair order. Uses atomic transaction
        to prevent race conditions.

        Args:
            validated_data: Validated data for creating the line item

        Returns:
            Created RepairOrderLineItem instance

        Raises:
            ValidationError: If creation fails due to database constraints
            DatabaseError: If a database error occurs during creation
        """
        try:
            with transaction.atomic():
                # Auto-assign line number if not provided
                if 'line_number' not in validated_data or validated_data['line_number'] is None:
                    repair_order = validated_data.get('repair_order')
                    if repair_order is not None:
                        last_line = RepairOrderLineItem.objects.filter(
                            repair_order=repair_order
                        ).order_by('-line_number').first()
                        
                        validated_data['line_number'] = (
                            (last_line.line_number + 1) if last_line else MIN_LINE_NUMBER
                        )
                    else:
                        validated_data['line_number'] = MIN_LINE_NUMBER

                # Create the line item
                instance = RepairOrderLineItem.objects.create(**validated_data)
                
                logger.info(
                    "Created repair order line item %s for order %s",
                    instance.pk,
                    instance.repair_order_id,
                )
                
                return instance

        except DjangoValidationError as exc:
            logger.warning(
                "Django validation error creating line item: %s",
                exc,
            )
            raise ValidationError(exc.message_dict) from exc
        except DatabaseError as exc:
            logger.error(
                "Database error creating line item: %s",
                exc,
                exc_info=True,
            )
            raise ValidationError(
                _("A database error occurred while creating the line item.")
            ) from exc
        except Exception as exc:
            logger.error(
                "Unexpected error creating line item: %s",
                exc,
                exc_info=True,
            )
            raise ValidationError(
                _("An unexpected error occurred while creating the line item.")
            ) from exc

    def update(self, instance: RepairOrderLineItem, validated_data: Dict[str, Any]) -> RepairOrderLineItem:
        """
        Update an existing RepairOrderLineItem instance.

        Performs atomic update with proper validation and error handling.

        Args:
            instance: Existing RepairOrderLineItem instance to update
            validated_data: Validated data for updating the line item

        Returns:
            Updated RepairOrderLineItem instance

        Raises:
            ValidationError: If update fails due to validation errors
            DatabaseError: If a database error occurs during update
        """
        try:
            with transaction.atomic():
                # Prevent changing repair_order after creation
                validated_data.pop('repair_order', None)

                # Update fields
                for field, value in validated_data.items():
                    setattr(instance, field, value)

                instance.full_clean()
                instance.save()

                logger.info(
                    "Updated repair order line item %s for order %s",
                    instance.pk,
                    instance.repair_order_id,
                )

                return instance

        except DjangoValidationError as exc:
            logger.warning(
                "Django validation error updating line item %s: %s",
                instance.pk,
                exc,
            )
            raise ValidationError(exc.message_dict) from exc
        except DatabaseError as exc:
            logger.error(
                "Database error updating line item %s: %s",
                instance.pk,
                exc,
                exc_info=True,
            )
            raise ValidationError(
                _("A database error occurred while updating the line item.")
            ) from exc
        except Exception as exc:
            logger.error(
                "Unexpected error updating line item %s: %s",
                instance.pk,
                exc,
                exc_info=True,
            )
            raise ValidationError(
                _("An unexpected error occurred while updating the line item.")
            ) from exc


class RepairOrderSerializer(OrderSerializer):
    """
    Serializer for RepairOrder model.

    Provides comprehensive serialization for repair orders, including
    nested line items, customer details, and status tracking. Extends
    the base OrderSerializer with repair-specific fields.

    Attributes:
        customer_detail: Nested serialized customer information (read-only)
        line_items: Nested serialized line items (read-only)
        responsible_detail: Nested serialized responsible user info (read-only)
        status_display: Human-readable status description (read-only)
    """

    # Nested serializers for related fields
    customer_detail = CompanySerializer(source='customer', read_only=True)
    line_items = RepairOrderLineItemSerializer(
        source='repairorderlineitem_set',
        many=True,
        read_only=True,
    )
    responsible_detail = UserSerializer(source='responsible', read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        """Meta configuration for RepairOrderSerializer."""

        model = RepairOrder
        fields = [
            'pk',
            'order_number',
            'reference',
            'description',
            'customer',
            'customer_detail',
            'status',
            'status_display',
            'line_items',
            'responsible',
            'responsible_detail',
            'target_date',
            'completion_date',
            'notes',
            'created_date',
            'modified_date',
            'issue_date',
            'completed_date',
            'total_cost',
            'currency',
        ]
        read_only_fields = [
            'pk',
            'order_number',
            'created_date',
            'modified_date',
            'issue_date',
            'completed_date',
            'total_cost',
        ]

    def get_status_display(self, obj: RepairOrder) -> str:
        """
        Return the human-readable display value for status.

        Args:
            obj: The RepairOrder instance

        Returns:
            Human-readable status string

        Raises:
            AttributeError: If the model instance is invalid
        """
        try:
            return obj.get_status_display()
        except AttributeError as exc:
            logger.warning(
                "Failed to get status display for order %s: %s",
                getattr(obj, 'pk', 'unknown'),
                exc,
            )
            return _("Unknown status")
        except Exception as exc:
            logger.error(
                "Unexpected error getting status display: %s",
                exc,
                exc_info=True,
            )
            return _("Error retrieving status")

    def validate_customer(self, value: Optional[Company]) -> Optional[Company]:
        """
        Validate the customer reference.

        Ensures the customer is a valid company and is marked as a customer.

        Args:
            value: The Company instance to validate

        Returns:
            Validated Company instance

        Raises:
            ValidationError: If customer is invalid or not a customer type
        """
        if value is not None:
            if not isinstance(value, Company):
                raise ValidationError(_("Invalid customer reference."))
            
            if not value.is_customer:
                raise ValidationError(
                    _("The selected company is not marked as a customer.")
                )

        return value

    def validate_responsible(self, value: Optional[Any]) -> Optional[Any]:
        """
        Validate the responsible user reference.

        Args:
            value: The user instance to validate

        Returns:
            Validated user instance or None

        Raises:
            ValidationError: If user reference is invalid
        """
        if value is not None:
            try:
                # Check if user exists and is active
                if hasattr(value, 'is_active') and not value.is_active:
                    raise ValidationError(
                        _("The selected user is not active.")
                    )
            except AttributeError as exc:
                raise ValidationError(
                    _("Invalid user reference.")
                ) from exc

        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the repair order data with cross-field validation.

        Performs comprehensive validation including:
        - Status transition validation
        - Date consistency checks
        - Customer and responsible user validation

        Args:
            attrs: Dictionary of field values to validate

        Returns:
            Validated attributes dictionary

        Raises:
            ValidationError: If validation fails
        """
        validated_attrs = attrs.copy()

        try:
            # Validate status transitions if this is an update
            if self.instance is not None:
                new_status = validated_attrs.get('status')
                if new_status is not None:
                    old_status = self.instance.status
                    
                    # Define valid status transitions
                    valid_transitions = {
                        RepairOrderStatus.PENDING: [RepairOrderStatus.IN_PROGRESS, RepairOrderStatus.CANCELLED],
                        RepairOrderStatus.IN_PROGRESS: [RepairOrderStatus.COMPLETED, RepairOrderStatus.CANCELLED],
                        RepairOrderStatus.COMPLETED: [RepairOrderStatus.CLOSED],
                        RepairOrderStatus.CANCELLED: [],
                        RepairOrderStatus.CLOSED: [],
                    }
                    
                    if new_status not in valid_transitions.get(old_status, []):
                        raise ValidationError({
                            'status': _(
                                "Cannot transition from %(old)s to %(new)s."
                            ) % {
                                'old': old_status,
                                'new': new_status,
                            },
                        })

            # Validate target_date is not in the past for new orders
            target_date = validated_attrs.get('target_date')
            if target_date is not None and self.instance is None:
                from django.utils import timezone
                if target_date < timezone.now().date():
                    raise ValidationError({
                        'target_date': _("Target date cannot be in the past."),
                    })

            # Validate completion_date is after target_date
            completion_date = validated_attrs.get('completion_date')
            if completion_date is not None and target_date is not None:
                if completion_date < target_date:
                    raise ValidationError({
                        'completion_date': _(
                            "Completion date cannot be before target date."
                        ),
                    })

        except ValidationError:
            raise
        except Exception as exc:
            logger.error(
                "Unexpected error during repair order validation: %s",
                exc,
                exc_info=True,
            )
            raise ValidationError(
                _("An unexpected error occurred during