"""
Admin configuration for RepairOrder model.

Registers the RepairOrder model and its related models (RepairOrderLineItem,
RepairOrderAttachment) in the Django admin interface for backend management.
Follows the same patterns as PurchaseOrder and SalesOrder admin registrations.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Type, Union

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from order.admin import OrderAdmin, OrderLineItemAdmin, OrderAttachmentAdmin
from order.models import RepairOrder, RepairOrderLineItem, RepairOrderAttachment

logger = logging.getLogger(__name__)


class RepairOrderLineItemInline(admin.TabularInline):
    """Inline admin for RepairOrder line items."""

    model: Type[RepairOrderLineItem] = RepairOrderLineItem
    extra: int = 0
    can_delete: bool = True
    fields: list[str] = [
        'order', 'part', 'quantity', 'reference', 'notes',
        'target_date', 'received_date',
    ]
    readonly_fields: list[str] = ['order']
    autocomplete_fields: list[str] = ['part']
    verbose_name: str = _('Line Item')
    verbose_name_plural: str = _('Line Items')

    def has_add_permission(
        self,
        request: HttpRequest,
        obj: Optional[RepairOrder] = None,
    ) -> bool:
        """
        Check if user has permission to add line items.

        Args:
            request: The HTTP request object
            obj: The parent RepairOrder instance, if any

        Returns:
            True if user has add permission, False otherwise
        """
        try:
            if obj is not None and not request.user.has_perm('order.add_repairorderlineitem'):
                return False
            return super().has_add_permission(request, obj)
        except PermissionDenied:
            logger.warning("Permission denied for user %s to add RepairOrderLineItem", request.user)
            return False
        except Exception as exc:
            logger.error("Error checking add permission for RepairOrderLineItem: %s", exc, exc_info=True)
            return False

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: Optional[RepairOrderLineItem] = None,
    ) -> bool:
        """
        Check if user has permission to change line items.

        Args:
            request: The HTTP request object
            obj: The RepairOrderLineItem instance, if any

        Returns:
            True if user has change permission, False otherwise
        """
        try:
            if obj is not None and not request.user.has_perm('order.change_repairorderlineitem'):
                return False
            return super().has_change_permission(request, obj)
        except PermissionDenied:
            logger.warning("Permission denied for user %s to change RepairOrderLineItem", request.user)
            return False
        except Exception as exc:
            logger.error("Error checking change permission for RepairOrderLineItem: %s", exc, exc_info=True)
            return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: Optional[RepairOrderLineItem] = None,
    ) -> bool:
        """
        Check if user has permission to delete line items.

        Args:
            request: The HTTP request object
            obj: The RepairOrderLineItem instance, if any

        Returns:
            True if user has delete permission, False otherwise
        """
        try:
            if obj is not None and not request.user.has_perm('order.delete_repairorderlineitem'):
                return False
            return super().has_delete_permission(request, obj)
        except PermissionDenied:
            logger.warning("Permission denied for user %s to delete RepairOrderLineItem", request.user)
            return False
        except Exception as exc:
            logger.error("Error checking delete permission for RepairOrderLineItem: %s", exc, exc_info=True)
            return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[RepairOrderLineItem]:
        """
        Get queryset with optimized query performance.

        Args:
            request: The HTTP request object

        Returns:
            Optimized QuerySet for RepairOrderLineItem
        """
        try:
            qs: QuerySet[RepairOrderLineItem] = super().get_queryset(request)
            return qs.select_related('part', 'order').only(
                'id', 'order_id', 'part_id', 'quantity', 'reference',
                'notes', 'target_date', 'received_date',
            )
        except Exception as exc:
            logger.error("Error getting queryset for RepairOrderLineItem: %s", exc, exc_info=True)
            return RepairOrderLineItem.objects.none()


class RepairOrderAttachmentInline(admin.TabularInline):
    """Inline admin for RepairOrder attachments."""

    model: Type[RepairOrderAttachment] = RepairOrderAttachment
    extra: int = 0
    can_delete: bool = True
    fields: list[str] = ['order', 'attachment', 'comment', 'upload_date']
    readonly_fields: list[str] = ['upload_date']
    verbose_name: str = _('Attachment')
    verbose_name_plural: str = _('Attachments')

    def has_add_permission(
        self,
        request: HttpRequest,
        obj: Optional[RepairOrder] = None,
    ) -> bool:
        """
        Check if user has permission to add attachments.

        Args:
            request: The HTTP request object
            obj: The parent RepairOrder instance, if any

        Returns:
            True if user has add permission, False otherwise
        """
        try:
            if obj is not None and not request.user.has_perm('order.add_repairorderattachment'):
                return False
            return super().has_add_permission(request, obj)
        except PermissionDenied:
            logger.warning("Permission denied for user %s to add RepairOrderAttachment", request.user)
            return False
        except Exception as exc:
            logger.error("Error checking add permission for RepairOrderAttachment: %s", exc, exc_info=True)
            return False

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: Optional[RepairOrderAttachment] = None,
    ) -> bool:
        """
        Check if user has permission to change attachments.

        Args:
            request: The HTTP request object
            obj: The RepairOrderAttachment instance, if any

        Returns:
            True if user has change permission, False otherwise
        """
        try:
            if obj is not None and not request.user.has_perm('order.change_repairorderattachment'):
                return False
            return super().has_change_permission(request, obj)
        except PermissionDenied:
            logger.warning("Permission denied for user %s to change RepairOrderAttachment", request.user)
            return False
        except Exception as exc:
            logger.error("Error checking change permission for RepairOrderAttachment: %s", exc, exc_info=True)
            return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: Optional[RepairOrderAttachment] = None,
    ) -> bool:
        """
        Check if user has permission to delete attachments.

        Args:
            request: The HTTP request object
            obj: The RepairOrderAttachment instance, if any

        Returns:
            True if user has delete permission, False otherwise
        """
        try:
            if obj is not None and not request.user.has_perm('order.delete_repairorderattachment'):
                return False
            return super().has_delete_permission(request, obj)
        except PermissionDenied:
            logger.warning("Permission denied for user %s to delete RepairOrderAttachment", request.user)
            return False
        except Exception as exc:
            logger.error("Error checking delete permission for RepairOrderAttachment: %s", exc, exc_info=True)
            return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[RepairOrderAttachment]:
        """
        Get queryset with optimized query performance.

        Args:
            request: The HTTP request object

        Returns:
            Optimized QuerySet for RepairOrderAttachment
        """
        try:
            qs: QuerySet[RepairOrderAttachment] = super().get_queryset(request)
            return qs.select_related('order').only(
                'id', 'order_id', 'attachment', 'comment', 'upload_date',
            )
        except Exception as exc:
            logger.error("Error getting queryset for RepairOrderAttachment: %s", exc, exc_info=True)
            return RepairOrderAttachment.objects.none()


@admin.register(RepairOrder)
class RepairOrderAdmin(OrderAdmin):
    """
    Admin interface for RepairOrder model.

    Extends the base OrderAdmin to provide repair-specific fields and actions.
    Provides comprehensive management of repair orders including status tracking,
    customer information, and related line items and attachments.

    Attributes:
        list_display: Fields to display in the list view
        list_filter: Fields available for filtering
        search_fields: Fields included in search
        autocomplete_fields: Fields with autocomplete support
        readonly_fields: Fields that cannot be edited
        fieldsets: Organized field groupings
        inlines: Related model inline editors
        actions: Bulk actions available
    """

    list_display: list[str] = [
        'pk', 'reference', 'customer', 'customer_unit',
        'status', 'created_date', 'target_date', 'completed_date',
    ]
    list_filter: list[str] = [
        'status', 'created_date', 'target_date', 'completed_date',
    ]
    search_fields: list[str] = [
        'reference', 'customer__name', 'customer_unit__serial',
        'description',
    ]
    autocomplete_fields: list[str] = [
        'customer', 'customer_unit', 'created_by', 'responsible',
    ]
    readonly_fields: list[str] = [
        'creation_date', 'created_by', 'reference',
    ]
    fieldsets: tuple = (
        (None, {
            'fields': (
                'reference', 'description', 'status',
                'customer', 'customer_unit',
            ),
        }),
        (_('Dates'), {
            'fields': (
                'creation_date', 'created_by',
                'target_date', 'completed_date',
            ),
        }),
        (_('Additional Information'), {
            'fields': (
                'responsible', 'notes', 'link',
            ),
            'classes': ('collapse',),
        }),
    )
    inlines: list[Type[admin.TabularInline]] = [
        RepairOrderLineItemInline,
        RepairOrderAttachmentInline,
    ]
    actions: list[str] = [
        'mark_as_completed',
        'mark_as_cancelled',
    ]
    date_hierarchy: str = 'created_date'
    list_per_page: int = 25
    list_max_show_all: int = 200
    preserve_filters: bool = True
    show_full_result_count: bool = True

    def get_queryset(self, request: HttpRequest) -> QuerySet[RepairOrder]:
        """
        Get queryset with optimized query performance.

        Args:
            request: The HTTP request object

        Returns:
            Optimized QuerySet for RepairOrder
        """
        try:
            qs: QuerySet[RepairOrder] = super().get_queryset(request)
            return qs.select_related(
                'customer', 'customer_unit', 'created_by', 'responsible',
            ).prefetch_related(
                'line_items', 'attachments',
            )
        except Exception as exc:
            logger.error("Error getting queryset for RepairOrder: %s", exc, exc_info=True)
            return RepairOrder.objects.none()

    def get_readonly_fields(
        self,
        request: HttpRequest,
        obj: Optional[RepairOrder] = None,
    ) -> list[str]:
        """
        Get readonly fields based on object state.

        Args:
            request: The HTTP request object
            obj: The RepairOrder instance, if any

        Returns:
            List of readonly field names
        """
        try:
            readonly_fields: list[str] = list(self.readonly_fields)
            if obj is not None and obj.status in [
                RepairOrder.STATUS_COMPLETED,
                RepairOrder.STATUS_CANCELLED,
            ]:
                readonly_fields.extend(['status', 'description', 'customer', 'customer_unit'])
            return readonly_fields
        except Exception as exc:
            logger.error("Error getting readonly fields: %s", exc, exc_info=True)
            return list(self.readonly_fields)

    def save_model(
        self,
        request: HttpRequest,
        obj: RepairOrder,
        form: Any,
        change: bool,
    ) -> None:
        """
        Save model with validation and logging.

        Args:
            request: The HTTP request object
            obj: The RepairOrder instance to save
            form: The form instance
            change: Whether this is a change or creation
        """
        try:
            if not change:
                obj.created_by = request.user
            obj.full_clean()
            super().save_model(request, obj, form, change)
            action: str = 'created' if not change else 'updated'
            logger.info(
                "RepairOrder %s %s by user %s",
                obj.reference, action, request.user,
            )
        except ValidationError as exc:
            logger.error("Validation error saving RepairOrder: %s", exc, exc_info=True)
            self.message_user(
                request,
                _('Validation error: %(error)s') % {'error': force_str(exc)},
                level=messages.ERROR,
            )
        except Exception as exc:
            logger.error("Error saving RepairOrder: %s", exc, exc_info=True)
            self.message_user(
                request,
                _('Error saving repair order: %(error)s') % {'error': force_str(exc)},
                level=messages.ERROR,
            )

    def delete_model(self, request: HttpRequest, obj: RepairOrder) -> None:
        """
        Delete model with logging and validation.

        Args:
            request: The HTTP request object
            obj: The RepairOrder instance to delete
        """
        try:
            reference: str = obj.reference
            super().delete_model(request, obj)
            logger.info(
                "RepairOrder %s deleted by user %s",
                reference, request.user,
            )
        except Exception as exc:
            logger.error("Error deleting RepairOrder: %s", exc, exc_info=True)
            self.message_user(
                request,
                _('Error deleting repair order: %(error)s') % {'error': force_str(exc)},
                level=messages.ERROR,
            )

    def mark_as_completed(
        self,
        request: HttpRequest,
        queryset: QuerySet[RepairOrder],
    ) -> Optional[HttpResponse]:
        """
        Admin action to mark selected orders as completed.

        Args:
            request: The HTTP request object
            queryset: QuerySet of RepairOrder instances to update

        Returns:
            None if successful, or error response if exception occurs
        """
        try:
            if not queryset.exists():
                self.message_user(
                    request,
                    _('No orders selected.'),
                    level=messages.WARNING,
                )
                return None

            # Validate all orders can be completed
            invalid_orders: list[str] = []
            for order in queryset:
                if order.status == RepairOrder.STATUS_COMPLETED:
                    invalid_orders.append(str(order.reference))
                elif order.status == RepairOrder.STATUS_CANCELLED:
                    invalid_orders.append(str(order.reference))

            if invalid_orders:
                self.message_user(
                    request,
                    _('Cannot complete orders: %(orders)s - already completed or cancelled') % {
                        'orders': ', '.join(invalid_orders),
                    },
                    level=messages.WARNING,
                )
                # Filter out invalid orders
                queryset = queryset.exclude(
                    status__in=[
                        RepairOrder.STATUS_COMPLETED,
                        RepairOrder.STATUS_CANCELLED,
                    ],
                )

            if not queryset.exists():
                return None

            updated_count: int = queryset.update(
                status=RepairOrder.STATUS_COMPLETED,
                completed_date=timezone.now(),
            )
            message: str = _(
                '%(count)d repair order(s) marked as completed.',
            ) % {'count': updated_count}
            self.message_user(request, message, level=messages.SUCCESS)
            logger.info(
                "Marked %d repair orders as completed by user %s",
                updated_count, request.user,
            )

        except AttributeError as exc:
            error_msg: str = _('Invalid status attribute on RepairOrder model.')
            logger.error("Failed to mark orders as completed: %s", exc, exc_info=True)
            self.message_user(request, error_msg, level=messages.ERROR)
        except ValidationError as exc:
            error_msg: str = _('Validation error: %(error)s') % {'error': force_str(exc)}
            logger.error("Validation error in mark_as_completed: %s", exc, exc_info=True)
            self.message_user(request, error_msg, level=messages.ERROR)
        except Exception as exc:
            error_msg: str = _('An unexpected error occurred while marking orders as completed.')
            logger.exception("Unexpected error in mark_as_completed: %s", exc)
            self.message_user(request, error_msg, level=messages.ERROR)

        return None

    mark_as_completed.short_description = _('Mark selected orders as completed')
    mark_as_completed.allowed_permissions = ('change',)

    def mark_as_cancelled(
        self,
        request: HttpRequest,
        queryset: QuerySet[RepairOrder],
    ) -> Optional[HttpResponse]:
        """
        Admin action to mark selected orders as cancelled.

        Args:
            request: The HTTP request object
            queryset: QuerySet of RepairOrder instances to update

        Returns:
            None if successful, or error response if exception occurs
        """
        try:
            if not queryset.exists():
                self.message_user(
                    request,
                    _('No orders selected.'),
                    level=messages.WARNING,
                )
                return None

            # Validate all orders can be cancelled
            invalid_orders: list[str] = []
            for order in queryset:
                if order.status == RepairOrder.STATUS_COMPLETED:
                    invalid_orders.append(str(order.reference))
                elif order.status == RepairOrder.STATUS_CANCELLED:
                    invalid_orders.append(str(order.reference))

            if invalid_orders:
                self.message_user(
                    request,
                    _('Cannot cancel orders: %(orders)s