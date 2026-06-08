"""
RepairOrder model for InvenTree order management system.

Extends the base Order model to support repair service workflows,
including customer unit tracking, repair descriptions, parts usage,
and labor tracking.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, ClassVar, Optional, Union

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import MetadataMixin
from order.models import Order, OrderLineItem
from stock.models import StockItem
from user.models import Owner

logger = logging.getLogger(__name__)


class RepairOrderStatus:
    """Constants for repair order status codes."""

    PENDING: int = 10
    IN_PROGRESS: int = 20
    ON_HOLD: int = 30
    COMPLETED: int = 40
    CANCELLED: int = 50
    AWAITING_PARTS: int = 60
    AWAITING_CUSTOMER: int = 70

    CHOICES: ClassVar[list[tuple[int, str]]] = [
        (PENDING, _("Pending")),
        (IN_PROGRESS, _("In Progress")),
        (ON_HOLD, _("On Hold")),
        (COMPLETED, _("Completed")),
        (CANCELLED, _("Cancelled")),
        (AWAITING_PARTS, _("Awaiting Parts")),
        (AWAITING_CUSTOMER, _("Awaiting Customer Approval")),
    ]

    @classmethod
    def is_valid_status(cls, status: int) -> bool:
        """Check if status code is valid.

        Args:
            status: The status code to validate.

        Returns:
            True if the status is a valid RepairOrderStatus, False otherwise.
        """
        try:
            return status in dict(cls.CHOICES)
        except (TypeError, ValueError) as exc:
            logger.warning("Invalid status check attempted: %s", exc)
            return False

    @classmethod
    def get_status_label(cls, status: int) -> str:
        """Get the human-readable label for a status code.

        Args:
            status: The status code.

        Returns:
            The label for the status, or 'Unknown' if not found.
        """
        try:
            status_dict = dict(cls.CHOICES)
            return status_dict.get(status, _("Unknown"))
        except (TypeError, ValueError) as exc:
            logger.error("Error getting status label for %d: %s", status, exc)
            return _("Unknown")


class RepairOrderManager(models.Manager["RepairOrder"]):
    """Custom manager for RepairOrder with query helpers."""

    def get_pending(self) -> QuerySet[RepairOrder]:
        """Get all pending repair orders.

        Returns:
            QuerySet of RepairOrder objects with PENDING status.
        """
        return self.filter(repair_status=RepairOrderStatus.PENDING)

    def get_in_progress(self) -> QuerySet[RepairOrder]:
        """Get all in-progress repair orders.

        Returns:
            QuerySet of RepairOrder objects with IN_PROGRESS status.
        """
        return self.filter(repair_status=RepairOrderStatus.IN_PROGRESS)

    def get_completed(self) -> QuerySet[RepairOrder]:
        """Get all completed repair orders.

        Returns:
            QuerySet of RepairOrder objects with COMPLETED status.
        """
        return self.filter(repair_status=RepairOrderStatus.COMPLETED)

    def get_by_technician(self, technician: Owner) -> QuerySet[RepairOrder]:
        """Get repair orders assigned to a specific technician.

        Args:
            technician: The Owner instance representing the technician.

        Returns:
            QuerySet of RepairOrder objects assigned to the technician.

        Raises:
            ValueError: If technician is None or invalid.
        """
        if technician is None:
            raise ValueError("Technician cannot be None")
        return self.filter(technician=technician)

    def get_by_customer_unit(self, unit: StockItem) -> QuerySet[RepairOrder]:
        """Get repair orders for a specific customer unit.

        Args:
            unit: The StockItem instance representing the customer unit.

        Returns:
            QuerySet of RepairOrder objects for the customer unit.

        Raises:
            ValueError: If unit is None or invalid.
        """
        if unit is None:
            raise ValueError("Customer unit cannot be None")
        return self.filter(customer_unit=unit)

    def get_active_repairs(self) -> QuerySet[RepairOrder]:
        """Get all active (non-completed, non-cancelled) repair orders.

        Returns:
            QuerySet of active RepairOrder objects.
        """
        active_statuses = [
            RepairOrderStatus.PENDING,
            RepairOrderStatus.IN_PROGRESS,
            RepairOrderStatus.ON_HOLD,
            RepairOrderStatus.AWAITING_PARTS,
            RepairOrderStatus.AWAITING_CUSTOMER,
        ]
        return self.filter(repair_status__in=active_statuses)


class RepairOrder(MetadataMixin, Order):
    """
    A RepairOrder tracks repair work performed on a customer's unit.

    Extends the base Order model with fields specific to repair operations:
    - Customer unit (the item being repaired)
    - Description of the repair work
    - Labor tracking (hours and rate)
    - Status tracking for repair workflow

    Attributes:
        order_type: Fixed to 'repair' for all repair orders
        customer_unit: The stock item being repaired
        repair_description: Detailed description of work performed
        customer_issue: Issue reported by customer
        diagnosis: Technician's diagnosis
        repair_status: Current status in repair workflow
        labor_hours: Total labor hours spent
        labor_rate: Hourly labor rate
        additional_costs: Extra costs (shipping, handling, etc.)
        technician: Assigned repair technician
        completion_date: When repair was completed
        warranty_claim: Whether covered under warranty
        customer_notes: Notes visible to customer
        internal_notes: Internal notes only
    """

    # Override order_type to be non-editable and fixed
    order_type = models.CharField(
        max_length=20,
        default="repair",
        editable=False,
        help_text=_("Order type is fixed to repair"),
    )

    # The customer unit being repaired (StockItem)
    customer_unit = models.ForeignKey(
        StockItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repair_orders",
        verbose_name=_("Customer Unit"),
        help_text=_("The stock item representing the customer unit being repaired"),
    )

    # Detailed description of the repair work
    repair_description = models.TextField(
        blank=True,
        verbose_name=_("Repair Description"),
        help_text=_("Detailed description of the repair work performed"),
    )

    # Customer-reported issue
    customer_issue = models.TextField(
        blank=True,
        verbose_name=_("Customer Issue"),
        help_text=_("Issue reported by the customer"),
    )

    # Diagnosis notes from the repair technician
    diagnosis = models.TextField(
        blank=True,
        verbose_name=_("Diagnosis"),
        help_text=_("Technician diagnosis of the issue"),
    )

    # Repair status
    repair_status = models.PositiveIntegerField(
        choices=RepairOrderStatus.CHOICES,
        default=RepairOrderStatus.PENDING,
        verbose_name=_("Repair Status"),
        help_text=_("Current status of the repair order"),
    )

    # Labor tracking fields
    labor_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Labor Hours"),
        help_text=_("Total labor hours spent on this repair"),
    )

    labor_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Labor Rate"),
        help_text=_("Hourly labor rate for this repair"),
    )

    # Additional costs (e.g., shipping, handling)
    additional_costs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Additional Costs"),
        help_text=_("Any additional costs associated with the repair"),
    )

    # Technician assigned to the repair
    technician = models.ForeignKey(
        Owner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repair_orders_technician",
        verbose_name=_("Technician"),
        help_text=_("Technician assigned to perform the repair"),
    )

    # Date the repair was completed
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completion Date"),
        help_text=_("Date when the repair was completed"),
    )

    # Warranty information
    warranty_claim = models.BooleanField(
        default=False,
        verbose_name=_("Warranty Claim"),
        help_text=_("Is this repair covered under warranty?"),
    )

    # Notes visible to customer
    customer_notes = models.TextField(
        blank=True,
        verbose_name=_("Customer Notes"),
        help_text=_("Notes to share with the customer about the repair"),
    )

    # Internal notes (not visible to customer)
    internal_notes = models.TextField(
        blank=True,
        verbose_name=_("Internal Notes"),
        help_text=_("Internal notes about the repair (not visible to customer)"),
    )

    objects = RepairOrderManager()

    class Meta:
        """Meta options for RepairOrder."""

        app_label = "order"
        db_table = "order_repair_order"
        verbose_name = _("Repair Order")
        verbose_name_plural = _("Repair Orders")
        ordering = ["-creation_date", "-pk"]
        permissions = [
            ("view_repair_order", _("Can view repair orders")),
            ("add_repair_order", _("Can add repair orders")),
            ("change_repair_order", _("Can change repair orders")),
            ("delete_repair_order", _("Can delete repair orders")),
            ("complete_repair_order", _("Can complete repair orders")),
            ("cancel_repair_order", _("Can cancel repair orders")),
        ]

    def __str__(self) -> str:
        """String representation of the RepairOrder.

        Returns:
            Formatted string with repair order reference number.
        """
        try:
            return _("Repair Order {ref}").format(ref=self.reference or _("No Reference"))
        except (AttributeError, ValueError) as exc:
            logger.error("Error generating string representation: %s", exc)
            return _("Repair Order (Error)")

    def clean(self) -> None:
        """Validate the RepairOrder model fields.

        Raises:
            ValidationError: If any validation checks fail.
        """
        super().clean()

        errors: dict[str, list[str]] = {}

        # Validate labor hours
        if self.labor_hours < Decimal("0.00"):
            errors.setdefault("labor_hours", []).append(
                _("Labor hours cannot be negative.")
            )

        # Validate labor rate
        if self.labor_rate < Decimal("0.00"):
            errors.setdefault("labor_rate", []).append(
                _("Labor rate cannot be negative.")
            )

        # Validate additional costs
        if self.additional_costs < Decimal("0.00"):
            errors.setdefault("additional_costs", []).append(
                _("Additional costs cannot be negative.")
            )

        # Validate repair status
        if not RepairOrderStatus.is_valid_status(self.repair_status):
            errors.setdefault("repair_status", []).append(
                _("Invalid repair status: {status}").format(status=self.repair_status)
            )

        # Validate completion date
        if self.completion_date and self.completion_date > timezone.now():
            errors.setdefault("completion_date", []).append(
                _("Completion date cannot be in the future.")
            )

        # Validate customer unit exists if set
        if self.customer_unit and not StockItem.objects.filter(pk=self.customer_unit.pk).exists():
            errors.setdefault("customer_unit", []).append(
                _("Customer unit does not exist.")
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the RepairOrder with validation.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Raises:
            ValidationError: If model validation fails.
        """
        try:
            self.full_clean()
            super().save(*args, **kwargs)
        except ValidationError as exc:
            logger.error("Validation error saving RepairOrder: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Unexpected error saving RepairOrder: %s", exc)
            raise

    def complete_repair(self, completion_date: Optional[timezone.datetime] = None) -> None:
        """Mark the repair order as completed.

        Args:
            completion_date: Optional completion date. Defaults to now.

        Raises:
            ValidationError: If the repair order cannot be completed.
        """
        if self.repair_status == RepairOrderStatus.COMPLETED:
            raise ValidationError(_("Repair order is already completed."))

        if self.repair_status == RepairOrderStatus.CANCELLED:
            raise ValidationError(_("Cannot complete a cancelled repair order."))

        try:
            with transaction.atomic():
                self.repair_status = RepairOrderStatus.COMPLETED
                self.completion_date = completion_date or timezone.now()
                self.save()
                logger.info(
                    "Repair order %s completed on %s",
                    self.reference,
                    self.completion_date,
                )
        except Exception as exc:
            logger.exception("Failed to complete repair order %s: %s", self.reference, exc)
            raise

    def cancel_repair(self, reason: str = "") -> None:
        """Cancel the repair order.

        Args:
            reason: Optional reason for cancellation.

        Raises:
            ValidationError: If the repair order cannot be cancelled.
        """
        if self.repair_status == RepairOrderStatus.COMPLETED:
            raise ValidationError(_("Cannot cancel a completed repair order."))

        if self.repair_status == RepairOrderStatus.CANCELLED:
            raise ValidationError(_("Repair order is already cancelled."))

        try:
            with transaction.atomic():
                self.repair_status = RepairOrderStatus.CANCELLED
                if reason:
                    self.internal_notes = (
                        f"{self.internal_notes}\n\nCancellation Reason: {reason}"
                        if self.internal_notes
                        else f"Cancellation Reason: {reason}"
                    )
                self.save()
                logger.info(
                    "Repair order %s cancelled. Reason: %s",
                    self.reference,
                    reason or _("No reason provided"),
                )
        except Exception as exc:
            logger.exception("Failed to cancel repair order %s: %s", self.reference, exc)
            raise

    def calculate_total_cost(self) -> Decimal:
        """Calculate the total cost of the repair.

        Returns:
            Decimal representing the total cost (labor + additional costs).
        """
        try:
            labor_cost = self.labor_hours * self.labor_rate
            total = labor_cost + self.additional_costs
            return total.quantize(Decimal("0.01"))
        except (TypeError, ValueError, ArithmeticError) as exc:
            logger.error("Error calculating total cost for repair %s: %s", self.reference, exc)
            return Decimal("0.00")

    def get_status_display(self) -> str:
        """Get the display label for the current repair status.

        Returns:
            String representation of the current status.
        """
        return RepairOrderStatus.get_status_label(self.repair_status)

    def is_active(self) -> bool:
        """Check if the repair order is currently active.

        Returns:
            True if the repair is in an active state, False otherwise.
        """
        return self.repair_status not in [
            RepairOrderStatus.COMPLETED,
            RepairOrderStatus.CANCELLED,
        ]

    def add_labor_hours(self, hours: Decimal) -> None:
        """Add labor hours to the repair order.

        Args:
            hours: The number of labor hours to add.

        Raises:
            ValidationError: If hours is negative or the repair is not active.
        """
        if not self.is_active():
            raise ValidationError(_("Cannot add labor hours to a completed or cancelled repair."))

        if hours < Decimal("0.00"):
            raise ValidationError(_("Cannot add negative labor hours."))

        try:
            self.labor_hours += hours
            self.save()
            logger.info("Added %s labor hours to repair %s", hours, self.reference)
        except Exception as exc:
            logger.exception("Failed to add labor hours to repair %s: %s", self.reference, exc)
            raise

    def update_repair_status(self, new_status: int) -> None:
        """Update the repair status with validation.

        Args:
            new_status: The new status code.

        Raises:
            ValidationError: If the status transition is invalid.
        """
        if not RepairOrderStatus.is_valid_status(new_status):
            raise ValidationError(
                _("Invalid repair status: {status}").format(status=new_status)
            )

        if self.repair_status == RepairOrderStatus.COMPLETED and new_status != RepairOrderStatus.COMPLETED:
            raise ValidationError(_("Cannot change status of a completed repair order."))

        if self.repair_status == RepairOrderStatus.CANCELLED:
            raise ValidationError(_("Cannot change status of a cancelled repair order."))

        try:
            with transaction.atomic():
                old_status = self.repair_status
                self.repair_status = new_status
                self.save()
                logger.info(
                    "Repair %s status changed from %s to %s",
                    self.reference,
                    RepairOrderStatus.get_status_label(old_status),
                    RepairOrderStatus.get_status_label(new_status),
                )
        except Exception as exc:
            logger.exception("Failed to update repair status for %s: %s", self.reference, exc)
            raise