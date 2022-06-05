"""Part database model definitions."""

from __future__ import annotations

import decimal
import hashlib
import logging
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q, Sum, UniqueConstraint
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_cleanup import cleanup
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from jinja2 import Template
from markdownx.models import MarkdownxField
from mptt.exceptions import InvalidMove
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from stdimage.models import StdImageField

import common.models
import InvenTree.ready
import InvenTree.tasks
import part.settings as part_settings
from build import models as BuildModels
from common.models import InvenTreeSetting
from common.settings import currency_code_default
from company.models import SupplierPart
from InvenTree import helpers, validators
from InvenTree.fields import InvenTreeURLField
from InvenTree.helpers import decimal2money, decimal2string, normalize
from InvenTree.models import (DataImportMixin, InvenTreeAttachment,
                              InvenTreeTree)
from InvenTree.status_codes import (BuildStatus, PurchaseOrderStatus,
                                    SalesOrderStatus)
from order import models as OrderModels
from plugin.models import MetadataMixin
from stock import models as StockModels

logger = logging.getLogger("inventree")


class PartCategory(MetadataMixin, InvenTreeTree):
    """PartCategory provides hierarchical organization of Part objects.

    Attributes:
        name: Name of this category
        parent: Parent category
        default_location: Default storage location for parts in this category or child categories
        default_keywords: Default keywords for parts created in this category
    """

    def delete(self, *args, **kwargs):
        """Custom model deletion routine, which updates any child categories or parts.

        This must be handled within a transaction.atomic(), otherwise the tree structure is damaged
        """
        with transaction.atomic():

            parent = self.parent
            tree_id = self.tree_id

            # Update each part in this category to point to the parent category
            for part in self.parts.all():
                part.category = self.parent
                part.save()

            # Update each child category
            for child in self.children.all():
                child.parent = self.parent
                child.save()

            super().delete(*args, **kwargs)

            if parent is not None:
                # Partially rebuild the tree (cheaper than a complete rebuild)
                PartCategory.objects.partial_rebuild(tree_id)
            else:
                PartCategory.objects.rebuild()

    default_location = TreeForeignKey(
        'stock.StockLocation', related_name="default_categories",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Default Location'),
        help_text=_('Default location for parts in this category')
    )

    default_keywords = models.CharField(null=True, blank=True, max_length=250, verbose_name=_('Default keywords'), help_text=_('Default keywords for parts in this category'))

    @staticmethod
    def get_api_url():
        """Return the API url associated with the PartCategory model"""
        return reverse('api-part-category-list')

    def get_absolute_url(self):
        """Return the web URL associated with the detail view for this PartCategory instance"""
        return reverse('category-detail', kwargs={'pk': self.id})

    class Meta:
        """Metaclass defines extra model properties"""
        verbose_name = _("Part Category")
        verbose_name_plural = _("Part Categories")

    def get_parts(self, cascade=True) -> set[Part]:
        """Return a queryset for all parts under this category.

        Args:
            cascade (bool, optional): If True, also look under subcategories. Defaults to True.

        Returns:
            set[Part]: All matching parts
        """
        if cascade:
            """Select any parts which exist in this category or any child categories."""
            queryset = Part.objects.filter(category__in=self.getUniqueChildren(include_self=True))
        else:
            queryset = Part.objects.filter(category=self.pk)

        return queryset

    @property
    def item_count(self):
        """Return the number of parts contained in this PartCategory"""
        return self.partcount()

    def partcount(self, cascade=True, active=False):
        """Return the total part count under this category (including children of child categories)."""
        query = self.get_parts(cascade=cascade)

        if active:
            query = query.filter(active=True)

        return query.count()

    def prefetch_parts_parameters(self, cascade=True):
        """Prefectch parts parameters."""
        return self.get_parts(cascade=cascade).prefetch_related('parameters', 'parameters__template').all()

    def get_unique_parameters(self, cascade=True, prefetch=None):
        """Get all unique parameter names for all parts from this category."""
        unique_parameters_names = []

        if prefetch:
            parts = prefetch
        else:
            parts = self.prefetch_parts_parameters(cascade=cascade)

        for part in parts:
            for parameter in part.parameters.all():
                parameter_name = parameter.template.name
                if parameter_name not in unique_parameters_names:
                    unique_parameters_names.append(parameter_name)

        return sorted(unique_parameters_names)

    def get_parts_parameters(self, cascade=True, prefetch=None):
        """Get all parameter names and values for all parts from this category."""
        category_parameters = []

        if prefetch:
            parts = prefetch
        else:
            parts = self.prefetch_parts_parameters(cascade=cascade)

        for part in parts:
            part_parameters = {
                'pk': part.pk,
                'name': part.name,
                'description': part.description,
            }
            # Add IPN only if it exists
            if part.IPN:
                part_parameters['IPN'] = part.IPN

            for parameter in part.parameters.all():
                parameter_name = parameter.template.name
                parameter_value = parameter.data
                part_parameters[parameter_name] = parameter_value

            category_parameters.append(part_parameters)

        return category_parameters

    @classmethod
    def get_parent_categories(cls):
        """Return tuple list of parent (root) categories."""
        # Get root nodes
        root_categories = cls.objects.filter(level=0)

        parent_categories = []
        for category in root_categories:
            parent_categories.append((category.id, category.name))

        return parent_categories

    def get_parameter_templates(self):
        """Return parameter templates associated to category."""
        prefetch = PartCategoryParameterTemplate.objects.prefetch_related('category', 'parameter_template')

        return prefetch.filter(category=self.id)

    def get_subscribers(self, include_parents=True):
        """Return a list of users who subscribe to this PartCategory."""
        cats = self.get_ancestors(include_self=True)

        subscribers = set()

        if include_parents:
            queryset = PartCategoryStar.objects.filter(
                category__pk__in=[cat.pk for cat in cats]
            )
        else:
            queryset = PartCategoryStar.objects.filter(
                category=self,
            )

        for result in queryset:
            subscribers.add(result.user)

        return [s for s in subscribers]

    def is_starred_by(self, user, **kwargs):
        """Returns True if the specified user subscribes to this category."""
        return user in self.get_subscribers(**kwargs)

    def set_starred(self, user, status):
        """Set the "subscription" status of this PartCategory against the specified user."""
        if not user:
            return

        if self.is_starred_by(user) == status:
            return

        if status:
            PartCategoryStar.objects.create(
                category=self,
                user=user
            )
        else:
            # Note that this won't actually stop the user being subscribed,
            # if the user is subscribed to a parent category
            PartCategoryStar.objects.filter(
                category=self,
                user=user,
            ).delete()


def rename_part_image(instance, filename):
    """Function for renaming a part image file.

    Args:
        instance: Instance of a Part object
        filename: Name of original uploaded file

    Returns:
        Cleaned filename in format part_<n>_img
    """
    base = 'part_images'
    fname = os.path.basename(filename)

    return os.path.join(base, fname)


class PartManager(TreeManager):
    """Defines a custom object manager for the Part model.

    The main purpose of this manager is to reduce the number of database hits,
    as the Part model has a large number of ForeignKey fields!
    """

    def get_queryset(self):
        """Perform default prefetch operations when accessing Part model from the database"""
        return super().get_queryset().prefetch_related(
            'category',
            'category__parent',
            'stock_items',
            'builds',
        )


@cleanup.ignore
class Part(MetadataMixin, MPTTModel):
    """The Part object represents an abstract part, the 'concept' of an actual entity.

    An actual physical instance of a Part is a StockItem which is treated separately.

    Parts can be used to create other parts (as part of a Bill of Materials or BOM).

    Attributes:
        name: Brief name for this part
        variant: Optional variant number for this part - Must be unique for the part name
        category: The PartCategory to which this part belongs
        description: Longer form description of the part
        keywords: Optional keywords for improving part search results
        IPN: Internal part number (optional)
        revision: Part revision
        is_template: If True, this part is a 'template' part
        link: Link to an external page with more information about this part (e.g. internal Wiki)
        image: Image of this part
        default_location: Where the item is normally stored (may be null)
        default_supplier: The default SupplierPart which should be used to procure and stock this part
        default_expiry: The default expiry duration for any StockItem instances of this part
        minimum_stock: Minimum preferred quantity to keep in stock
        units: Units of measure for this part (default='pcs')
        salable: Can this part be sold to customers?
        assembly: Can this part be build from other parts?
        component: Can this part be used to make other parts?
        purchaseable: Can this part be purchased from suppliers?
        trackable: Trackable parts can have unique serial numbers assigned, etc, etc
        active: Is this part active? Parts are deactivated instead of being deleted
        virtual: Is this part "virtual"? e.g. a software product or similar
        notes: Additional notes field for this part
        creation_date: Date that this part was added to the database
        creation_user: User who added this part to the database
        responsible: User who is responsible for this part (optional)
    """

    objects = PartManager()

    class Meta:
        """Metaclass defines extra model properties"""
        verbose_name = _("Part")
        verbose_name_plural = _("Parts")
        ordering = ['name', ]
        constraints = [
            UniqueConstraint(fields=['name', 'IPN', 'revision'], name='unique_part')
        ]

    class MPTTMeta:
        """MPTT metaclass definitions"""
        # For legacy reasons the 'variant_of' field is used to indicate the MPTT parent
        parent_attr = 'variant_of'

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the Part model"""
        return reverse('api-part-list')

    def api_instance_filters(self):
        """Return API query filters for limiting field results against this instance."""
        return {
            'variant_of': {
                'exclude_tree': self.pk,
            }
        }

    def get_context_data(self, request, **kwargs):
        """Return some useful context data about this part for template rendering."""
        context = {}

        context['disabled'] = not self.active

        # Subscription status
        context['starred'] = self.is_starred_by(request.user)
        context['starred_directly'] = context['starred'] and self.is_starred_by(
            request.user,
            include_variants=False,
            include_categories=False
        )

        # Pre-calculate complex queries so they only need to be performed once
        context['total_stock'] = self.total_stock

        context['quantity_being_built'] = self.quantity_being_built

        context['required_build_order_quantity'] = self.required_build_order_quantity()
        context['allocated_build_order_quantity'] = self.build_order_allocation_count()

        context['required_sales_order_quantity'] = self.required_sales_order_quantity()
        context['allocated_sales_order_quantity'] = self.sales_order_allocation_count(pending=True)

        context['available'] = self.available_stock
        context['on_order'] = self.on_order

        context['required'] = context['required_build_order_quantity'] + context['required_sales_order_quantity']
        context['allocated'] = context['allocated_build_order_quantity'] + context['allocated_sales_order_quantity']

        return context

    def save(self, *args, **kwargs):
        """Overrides the save function for the Part model.

        If the part image has been updated, then check if the "old" (previous) image is still used by another part.
        If not, it is considered "orphaned" and will be deleted.
        """
        # Get category templates settings
        add_category_templates = kwargs.pop('add_category_templates', False)

        if self.pk:
            previous = Part.objects.get(pk=self.pk)

            # Image has been changed
            if previous.image is not None and self.image != previous.image:

                # Are there any (other) parts which reference the image?
                n_refs = Part.objects.filter(image=previous.image).exclude(pk=self.pk).count()

                if n_refs == 0:
                    logger.info(f"Deleting unused image file '{previous.image}'")
                    previous.image.delete(save=False)

        self.full_clean()

        try:
            super().save(*args, **kwargs)
        except InvalidMove:
            raise ValidationError({
                'variant_of': _('Invalid choice for parent part'),
            })

        if add_category_templates:
            # Get part category
            category = self.category

            if category is not None:

                template_list = []

                parent_categories = category.get_ancestors(include_self=True)

                for category in parent_categories:
                    for template in category.get_parameter_templates():
                        # Check that template wasn't already added
                        if template.parameter_template not in template_list:

                            template_list.append(template.parameter_template)

                            try:
                                PartParameter.create(
                                    part=self,
                                    template=template.parameter_template,
                                    data=template.default_value,
                                    save=True
                                )
                            except IntegrityError:
                                # PartParameter already exists
                                pass

    def __str__(self):
        """Return a string representation of the Part (for use in the admin interface)"""
        return f"{self.full_name} - {self.description}"

    def get_parts_in_bom(self, **kwargs):
        """Return a list of all parts in the BOM for this part.

        Takes into account substitutes, variant parts, and inherited BOM items
        """
        parts = set()

        for bom_item in self.get_bom_items(**kwargs):
            for part in bom_item.get_valid_parts_for_allocation():
                parts.add(part)

        return parts

    def check_if_part_in_bom(self, other_part, **kwargs):
        """Check if the other_part is in the BOM for *this* part.

        Note:
            - Accounts for substitute parts
            - Accounts for variant BOMs
        """
        return other_part in self.get_parts_in_bom(**kwargs)

    def check_add_to_bom(self, parent, raise_error=False, recursive=True):
        """Check if this Part can be added to the BOM of another part.

        This will fail if:

        a) The parent part is the same as this one
        b) The parent part is used in the BOM for *this* part
        c) The parent part is used in the BOM for any child parts under this one
        """
        result = True

        try:
            if self.pk == parent.pk:
                raise ValidationError({'sub_part': _("Part '{p1}' is  used in BOM for '{p2}' (recursive)").format(
                    p1=str(self),
                    p2=str(parent)
                )})

            bom_items = self.get_bom_items()

            # Ensure that the parent part does not appear under any child BOM item!
            for item in bom_items.all():

                # Check for simple match
                if item.sub_part == parent:
                    raise ValidationError({'sub_part': _("Part '{p1}' is  used in BOM for '{p2}' (recursive)").format(
                        p1=str(parent),
                        p2=str(self)
                    )})

                # And recursively check too
                if recursive:
                    result = result and item.sub_part.check_add_to_bom(
                        parent,
                        recursive=True,
                        raise_error=raise_error
                    )

        except ValidationError as e:
            if raise_error:
                raise e
            else:
                return False

        return result

    def checkIfSerialNumberExists(self, sn, exclude_self=False):
        """Check if a serial number exists for this Part.

        Note: Serial numbers must be unique across an entire Part "tree", so here we filter by the entire tree.
        """
        parts = Part.objects.filter(tree_id=self.tree_id)

        stock = StockModels.StockItem.objects.filter(part__in=parts, serial=sn)

        if exclude_self:
            stock = stock.exclude(pk=self.pk)

        return stock.exists()

    def find_conflicting_serial_numbers(self, serials):
        """For a provided list of serials, return a list of those which are conflicting."""
        conflicts = []

        for serial in serials:
            if self.checkIfSerialNumberExists(serial, exclude_self=True):
                conflicts.append(serial)

        return conflicts

    def getLatestSerialNumber(self):
        """Return the "latest" serial number for this Part.

        If *all* the serial numbers are integers, then this will return the highest one.
        Otherwise, it will simply return the serial number most recently added.

        Note: Serial numbers must be unique across an entire Part "tree",
        so we filter by the entire tree.
        """
        parts = Part.objects.filter(tree_id=self.tree_id)
        stock = StockModels.StockItem.objects.filter(part__in=parts).exclude(serial=None)

        # There are no matchin StockItem objects (skip further tests)
        if not stock.exists():
            return None

        # Attempt to coerce the returned serial numbers to integers
        # If *any* are not integers, fail!
        try:
            ordered = sorted(stock.all(), reverse=True, key=lambda n: int(n.serial))

            if len(ordered) > 0:
                return ordered[0].serial

        # One or more of the serial numbers was non-numeric
        # In this case, the "best" we can do is return the most recent
        except ValueError:
            return stock.last().serial

        # No serial numbers found
        return None

    def getLatestSerialNumberInt(self):
        """Return the "latest" serial number for this Part as a integer.

        If it is not an integer the result is 0
        """
        latest = self.getLatestSerialNumber()

        # No serial number = > 0
        if latest is None:
            latest = 0

        # Attempt to turn into an integer and return
        try:
            latest = int(latest)
            return latest
        except Exception:
            # not an integer so 0
            return 0

    def getSerialNumberString(self, quantity=1):
        """Return a formatted string representing the next available serial numbers, given a certain quantity of items."""
        latest = self.getLatestSerialNumber()

        quantity = int(quantity)

        # No serial numbers can be found, assume 1 as the first serial
        if latest is None:
            latest = 0

        # Attempt to turn into an integer
        try:
            latest = int(latest)
        except Exception:
            pass

        if type(latest) is int:

            if quantity >= 2:
                text = '{n} - {m}'.format(n=latest + 1, m=latest + 1 + quantity)

                return _('Next available serial numbers are') + ' ' + text
            else:
                text = str(latest + 1)

                return _('Next available serial number is') + ' ' + text

        else:
            # Non-integer values, no option but to return latest

            return _('Most recent serial number is') + ' ' + str(latest)

    @property
    def full_name(self):
        """Format a 'full name' for this Part based on the format PART_NAME_FORMAT defined in Inventree settings.

        As a failsafe option, the following is done:

        - IPN (if not null)
        - Part name
        - Part variant (if not null)

        Elements are joined by the | character
        """
        full_name_pattern = InvenTreeSetting.get_setting('PART_NAME_FORMAT')

        try:
            context = {'part': self}
            template_string = Template(full_name_pattern)
            full_name = template_string.render(context)

            return full_name

        except AttributeError as attr_err:

            logger.warning(f"exception while trying to create full name for part {self.name}", attr_err)

            # Fallback to default format
            elements = []

            if self.IPN:
                elements.append(self.IPN)

            elements.append(self.name)

            if self.revision:
                elements.append(self.revision)

            return ' | '.join(elements)

    def get_absolute_url(self):
        """Return the web URL for viewing this part."""
        return reverse('part-detail', kwargs={'pk': self.id})

    def get_image_url(self):
        """Return the URL of the image for this part."""
        if self.image:
            return helpers.getMediaUrl(self.image.url)
        else:
            return helpers.getBlankImage()

    def get_thumbnail_url(self):
        """Return the URL of the image thumbnail for this part."""
        if self.image:
            return helpers.getMediaUrl(self.image.thumbnail.url)
        else:
            return helpers.getBlankThumbnail()

    def validate_unique(self, exclude=None):
        """Validate that a part is 'unique'.

        Uniqueness is checked across the following (case insensitive) fields:
        - Name
        - IPN
        - Revision

        e.g. there can exist multiple parts with the same name, but only if
        they have a different revision or internal part number.
        """
        super().validate_unique(exclude)

        # User can decide whether duplicate IPN (Internal Part Number) values are allowed
        allow_duplicate_ipn = common.models.InvenTreeSetting.get_setting('PART_ALLOW_DUPLICATE_IPN')

        # Raise an error if an IPN is set, and it is a duplicate
        if self.IPN and not allow_duplicate_ipn:
            parts = Part.objects.filter(IPN__iexact=self.IPN)
            parts = parts.exclude(pk=self.pk)

            if parts.exists():
                raise ValidationError({
                    'IPN': _('Duplicate IPN not allowed in part settings'),
                })

    def clean(self):
        """Perform cleaning operations for the Part model.

        Update trackable status:
            If this part is trackable, and it is used in the BOM
            for a parent part which is *not* trackable,
            then we will force the parent part to be trackable.
        """
        super().clean()

        # Strip IPN field
        if type(self.IPN) is str:
            self.IPN = self.IPN.strip()

        if self.trackable:
            for part in self.get_used_in().all():

                if not part.trackable:
                    part.trackable = True
                    part.clean()
                    part.save()

    name = models.CharField(
        max_length=100, blank=False,
        help_text=_('Part name'),
        verbose_name=_('Name'),
        validators=[validators.validate_part_name]
    )

    is_template = models.BooleanField(
        default=part_settings.part_template_default,
        verbose_name=_('Is Template'),
        help_text=_('Is this part a template part?')
    )

    variant_of = models.ForeignKey(
        'part.Part', related_name='variants',
        null=True, blank=True,
        limit_choices_to={
            'is_template': True,
        },
        on_delete=models.SET_NULL,
        help_text=_('Is this part a variant of another part?'),
        verbose_name=_('Variant Of'),
    )

    description = models.CharField(
        max_length=250, blank=False,
        verbose_name=_('Description'),
        help_text=_('Part description')
    )

    keywords = models.CharField(
        max_length=250, blank=True, null=True,
        verbose_name=_('Keywords'),
        help_text=_('Part keywords to improve visibility in search results')
    )

    category = TreeForeignKey(
        PartCategory, related_name='parts',
        null=True, blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_('Category'),
        help_text=_('Part category')
    )

    IPN = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name=_('IPN'),
        help_text=_('Internal Part Number'),
        validators=[validators.validate_part_ipn]
    )

    revision = models.CharField(
        max_length=100, blank=True, null=True,
        help_text=_('Part revision or version number'),
        verbose_name=_('Revision'),
    )

    link = InvenTreeURLField(
        blank=True, null=True,
        verbose_name=_('Link'),
        help_text=_('Link to external URL')
    )

    image = StdImageField(
        upload_to=rename_part_image,
        null=True,
        blank=True,
        variations={'thumbnail': (128, 128)},
        delete_orphans=False,
        verbose_name=_('Image'),
    )

    default_location = TreeForeignKey(
        'stock.StockLocation',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        help_text=_('Where is this item normally stored?'),
        related_name='default_parts',
        verbose_name=_('Default Location'),
    )

    def get_default_location(self):
        """Get the default location for a Part (may be None).

        If the Part does not specify a default location,
        look at the Category this part is in.
        The PartCategory object may also specify a default stock location
        """
        if self.default_location:
            return self.default_location
        elif self.category:
            # Traverse up the category tree until we find a default location
            cats = self.category.get_ancestors(ascending=True, include_self=True)

            for cat in cats:
                if cat.default_location:
                    return cat.default_location

        # Default case - no default category found
        return None

    def get_default_supplier(self):
        """Get the default supplier part for this part (may be None).

        - If the part specifies a default_supplier, return that
        - If there is only one supplier part available, return that
        - Else, return None
        """
        if self.default_supplier:
            return self.default_supplier

        if self.supplier_count == 1:
            return self.supplier_parts.first()

        # Default to None if there are multiple suppliers to choose from
        return None

    default_supplier = models.ForeignKey(
        SupplierPart,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Default Supplier'),
        help_text=_('Default supplier part'),
        related_name='default_parts'
    )

    default_expiry = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Default Expiry'),
        help_text=_('Expiry time (in days) for stock items of this part'),
    )

    minimum_stock = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)],
        verbose_name=_('Minimum Stock'),
        help_text=_('Minimum allowed stock level')
    )

    units = models.CharField(
        max_length=20, default="",
        blank=True, null=True,
        verbose_name=_('Units'),
        help_text=_('Stock keeping units for this part')
    )

    assembly = models.BooleanField(
        default=part_settings.part_assembly_default,
        verbose_name=_('Assembly'),
        help_text=_('Can this part be built from other parts?')
    )

    component = models.BooleanField(
        default=part_settings.part_component_default,
        verbose_name=_('Component'),
        help_text=_('Can this part be used to build other parts?')
    )

    trackable = models.BooleanField(
        default=part_settings.part_trackable_default,
        verbose_name=_('Trackable'),
        help_text=_('Does this part have tracking for unique items?'))

    purchaseable = models.BooleanField(
        default=part_settings.part_purchaseable_default,
        verbose_name=_('Purchaseable'),
        help_text=_('Can this part be purchased from external suppliers?'))

    salable = models.BooleanField(
        default=part_settings.part_salable_default,
        verbose_name=_('Salable'),
        help_text=_("Can this part be sold to customers?"))

    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Is this part active?'))

    virtual = models.BooleanField(
        default=part_settings.part_virtual_default,
        verbose_name=_('Virtual'),
        help_text=_('Is this a virtual part, such as a software product or license?'))

    notes = MarkdownxField(
        blank=True, null=True,
        verbose_name=_('Notes'),
        help_text=_('Part notes - supports Markdown formatting')
    )

    bom_checksum = models.CharField(max_length=128, blank=True, verbose_name=_('BOM checksum'), help_text=_('Stored BOM checksum'))

    bom_checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                       verbose_name=_('BOM checked by'), related_name='boms_checked')

    bom_checked_date = models.DateField(blank=True, null=True, verbose_name=_('BOM checked date'))

    creation_date = models.DateField(auto_now_add=True, editable=False, blank=True, null=True, verbose_name=_('Creation Date'))

    creation_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('Creation User'), related_name='parts_created')

    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('Responsible'), related_name='parts_responible')

    def format_barcode(self, **kwargs):
        """Return a JSON string for formatting a barcode for this Part object."""
        return helpers.MakeBarcode(
            "part",
            self.id,
            {
                "name": self.full_name,
                "url": reverse('api-part-detail', kwargs={'pk': self.id}),
            },
            **kwargs
        )

    @property
    def category_path(self):
        """Return the category path of this Part instance"""
        if self.category:
            return self.category.pathstring
        return ''

    @property
    def available_stock(self):
        """Return the total available stock.

        - This subtracts stock which is already allocated to builds
        """
        total = self.total_stock
        total -= self.allocation_count()

        return max(total, 0)

    def requiring_build_orders(self):
        """Return list of outstanding build orders which require this part."""
        # List parts that this part is required for
        parts = self.get_used_in().all()

        part_ids = [part.pk for part in parts]

        # Now, get a list of outstanding build orders which require this part
        builds = BuildModels.Build.objects.filter(
            part__in=part_ids,
            status__in=BuildStatus.ACTIVE_CODES
        )

        return builds

    def required_build_order_quantity(self):
        """Return the quantity of this part required for active build orders."""
        # List active build orders which reference this part
        builds = self.requiring_build_orders()

        quantity = 0

        for build in builds:

            bom_item = None

            # List the bom lines required to make the build (including inherited ones!)
            bom_items = build.part.get_bom_items().filter(sub_part=self)

            # Match BOM item to build
            for bom_item in bom_items:

                build_quantity = build.quantity * bom_item.quantity

                quantity += build_quantity

        return quantity

    def requiring_sales_orders(self):
        """Return a list of sales orders which require this part."""
        orders = set()

        # Get a list of line items for open orders which match this part
        open_lines = OrderModels.SalesOrderLineItem.objects.filter(
            order__status__in=SalesOrderStatus.OPEN,
            part=self
        )

        for line in open_lines:
            orders.add(line.order)

        return orders

    def required_sales_order_quantity(self):
        """Return the quantity of this part required for active sales orders."""
        # Get a list of line items for open orders which match this part
        open_lines = OrderModels.SalesOrderLineItem.objects.filter(
            order__status__in=SalesOrderStatus.OPEN,
            part=self
        )

        quantity = 0

        for line in open_lines:
            # Determine the quantity "remaining" to be shipped out
            remaining = max(line.quantity - line.shipped, 0)
            quantity += remaining

        return quantity

    def required_order_quantity(self):
        """Return total required to fulfil orders."""
        return self.required_build_order_quantity() + self.required_sales_order_quantity()

    @property
    def quantity_to_order(self):
        """Return the quantity needing to be ordered for this part.

        Here, an "order" could be one of:
        - Build Order
        - Sales Order

        To work out how many we need to order:

        Stock on hand = self.total_stock
        Required for orders = self.required_order_quantity()
        Currently on order = self.on_order
        Currently building = self.quantity_being_built
        """
        # Total requirement
        required = self.required_order_quantity()

        # Subtract stock levels
        required -= max(self.total_stock, self.minimum_stock)

        # Subtract quantity on order
        required -= self.on_order

        # Subtract quantity being built
        required -= self.quantity_being_built

        return max(required, 0)

    @property
    def net_stock(self):
        """Return the 'net' stock.

        It takes into account:
        - Stock on hand (total_stock)
        - Stock on order (on_order)
        - Stock allocated (allocation_count)

        This number (unlike 'available_stock') can be negative.
        """
        return self.total_stock - self.allocation_count() + self.on_order

    def get_subscribers(self, include_variants=True, include_categories=True):
        """Return a list of users who are 'subscribed' to this part.

        A user may 'subscribe' to this part in the following ways:

        a) Subscribing to the part instance directly
        b) Subscribing to a template part "above" this part (if it is a variant)
        c) Subscribing to the part category that this part belongs to
        d) Subscribing to a parent category of the category in c)
        """
        subscribers = set()

        # Start by looking at direct subscriptions to a Part model
        queryset = PartStar.objects.all()

        if include_variants:
            queryset = queryset.filter(
                part__pk__in=[part.pk for part in self.get_ancestors(include_self=True)]
            )
        else:
            queryset = queryset.filter(part=self)

        for star in queryset:
            subscribers.add(star.user)

        if include_categories and self.category:

            for sub in self.category.get_subscribers():
                subscribers.add(sub)

        return [s for s in subscribers]

    def is_starred_by(self, user, **kwargs):
        """Return True if the specified user subscribes to this part."""
        return user in self.get_subscribers(**kwargs)

    def set_starred(self, user, status):
        """Set the "subscription" status of this Part against the specified user."""
        if not user:
            return

        # Already subscribed?
        if self.is_starred_by(user) == status:
            return

        if status:
            PartStar.objects.create(part=self, user=user)
        else:
            # Note that this won't actually stop the user being subscribed,
            # if the user is subscribed to a parent part or category
            PartStar.objects.filter(part=self, user=user).delete()

    @property
    def can_build(self):
        """Return the number of units that can be build with available stock."""
        # If this part does NOT have a BOM, result is simply the currently available stock
        if not self.has_bom:
            return 0

        total = None

        bom_items = self.get_bom_items().prefetch_related('sub_part__stock_items')

        # Calculate the minimum number of parts that can be built using each sub-part
        for item in bom_items.all():
            stock = item.sub_part.available_stock

            # If (by some chance) we get here but the BOM item quantity is invalid,
            # ignore!
            if item.quantity <= 0:
                continue

            n = int(stock / item.quantity)

            if total is None or n < total:
                total = n

        if total is None:
            total = 0

        return max(total, 0)

    @property
    def active_builds(self):
        """Return a list of outstanding builds.

        Builds marked as 'complete' or 'cancelled' are ignored
        """
        return self.builds.filter(status__in=BuildStatus.ACTIVE_CODES)

    @property
    def quantity_being_built(self):
        """Return the current number of parts currently being built.

        Note: This is the total quantity of Build orders, *not* the number of build outputs.
              In this fashion, it is the "projected" quantity of builds
        """
        builds = self.active_builds

        quantity = 0

        for build in builds:
            # The remaining items in the build
            quantity += build.remaining

        return quantity

    def build_order_allocations(self, **kwargs):
        """Return all 'BuildItem' objects which allocate this part to Build objects."""
        include_variants = kwargs.get('include_variants', True)

        queryset = BuildModels.BuildItem.objects.all()

        if include_variants:
            variants = self.get_descendants(include_self=True)
            queryset = queryset.filter(
                stock_item__part__in=variants,
            )
        else:
            queryset = queryset.filter(stock_item__part=self)

        return queryset

    def build_order_allocation_count(self, **kwargs):
        """Return the total amount of this part allocated to build orders."""
        query = self.build_order_allocations(**kwargs).aggregate(
            total=Coalesce(
                Sum(
                    'quantity',
                    output_field=models.DecimalField()
                ),
                0,
                output_field=models.DecimalField(),
            )
        )

        return query['total']

    def sales_order_allocations(self, **kwargs):
        """Return all sales-order-allocation objects which allocate this part to a SalesOrder."""
        include_variants = kwargs.get('include_variants', True)

        queryset = OrderModels.SalesOrderAllocation.objects.all()

        if include_variants:
            # Include allocations for all variants
            variants = self.get_descendants(include_self=True)
            queryset = queryset.filter(
                item__part__in=variants,
            )
        else:
            # Only look at this part
            queryset = queryset.filter(item__part=self)

        # Default behaviour is to only return *pending* allocations
        pending = kwargs.get('pending', True)

        if pending is True:
            # Look only for 'open' orders which have not shipped
            queryset = queryset.filter(
                line__order__status__in=SalesOrderStatus.OPEN,
                shipment__shipment_date=None,
            )
        elif pending is False:
            # Look only for 'closed' orders or orders which have shipped
            queryset = queryset.exclude(
                line__order__status__in=SalesOrderStatus.OPEN,
                shipment__shipment_date=None,
            )

        return queryset

    def sales_order_allocation_count(self, **kwargs):
        """Return the total quantity of this part allocated to sales orders."""
        query = self.sales_order_allocations(**kwargs).aggregate(
            total=Coalesce(
                Sum(
                    'quantity',
                    output_field=models.DecimalField(),
                ),
                0,
                output_field=models.DecimalField(),
            )
        )

        return query['total']

    def allocation_count(self, **kwargs):
        """Return the total quantity of stock allocated for this part, against both build orders and sales orders."""
        return sum(
            [
                self.build_order_allocation_count(**kwargs),
                self.sales_order_allocation_count(**kwargs),
            ],
        )

    def stock_entries(self, include_variants=True, in_stock=None):
        """Return all stock entries for this Part.

        - If this is a template part, include variants underneath this.

        Note: To return all stock-entries for all part variants under this one,
        we need to be creative with the filtering.
        """
        if include_variants:
            query = StockModels.StockItem.objects.filter(part__in=self.get_descendants(include_self=True))
        else:
            query = self.stock_items

        if in_stock is True:
            query = query.filter(StockModels.StockItem.IN_STOCK_FILTER)
        elif in_stock is False:
            query = query.exclude(StockModels.StockItem.IN_STOCK_FILTER)

        return query

    def get_stock_count(self, include_variants=True):
        """Return the total "in stock" count for this part."""
        entries = self.stock_entries(in_stock=True, include_variants=include_variants)

        query = entries.aggregate(t=Coalesce(Sum('quantity'), Decimal(0)))

        return query['t']

    @property
    def total_stock(self):
        """Return the total stock quantity for this part.

        - Part may be stored in multiple locations
        - If this part is a "template" (variants exist) then these are counted too
        """
        return self.get_stock_count(include_variants=True)

    def get_bom_item_filter(self, include_inherited=True):
        """Returns a query filter for all BOM items associated with this Part.

        There are some considerations:

        a) BOM items can be defined against *this* part
        b) BOM items can be inherited from a *parent* part

        We will construct a filter to grab *all* the BOM items!

        Note: This does *not* return a queryset, it returns a Q object,
              which can be used by some other query operation!
              Because we want to keep our code DRY!
        """
        bom_filter = Q(part=self)

        if include_inherited:
            # We wish to include parent parts

            parents = self.get_ancestors(include_self=False)

            # There are parents available
            if parents.count() > 0:
                parent_ids = [p.pk for p in parents]

                parent_filter = Q(
                    part__id__in=parent_ids,
                    inherited=True
                )

                # OR the filters together
                bom_filter |= parent_filter

        return bom_filter

    def get_bom_items(self, include_inherited=True):
        """Return a queryset containing all BOM items for this part.

        By default, will include inherited BOM items
        """
        queryset = BomItem.objects.filter(self.get_bom_item_filter(include_inherited=include_inherited))

        return queryset.prefetch_related('sub_part')

    def get_installed_part_options(self, include_inherited: bool = True, include_variants: bool = True):
        """Return a set of all Parts which can be "installed" into this part, based on the BOM.

        Arguments:
            include_inherited (bool): If set, include BomItem entries defined for parent parts
            include_variants (bool): If set, include variant parts for BomItems which allow variants
        """
        parts = set()

        for bom_item in self.get_bom_items(include_inherited=include_inherited):

            if include_variants and bom_item.allow_variants:
                for part in bom_item.sub_part.get_descendants(include_self=True):
                    parts.add(part)
            else:
                parts.add(bom_item.sub_part)

        return parts

    def get_used_in_filter(self, include_inherited=True):
        """Return a query filter for all parts that this part is used in.

        There are some considerations:

        a) This part may be directly specified against a BOM for a part
        b) This part may be specifed in a BOM which is then inherited by another part

        Note: This function returns a Q object, not an actual queryset.
              The Q object is used to filter against a list of Part objects
        """
        # This is pretty expensive - we need to traverse multiple variant lists!
        # TODO - In the future, could this be improved somehow?

        # Keep a set of Part ID values
        parts = set()

        # First, grab a list of all BomItem objects which "require" this part
        bom_items = BomItem.objects.filter(sub_part=self)

        for bom_item in bom_items:

            # Add the directly referenced part
            parts.add(bom_item.part)

            # Traverse down the variant tree?
            if include_inherited and bom_item.inherited:

                part_variants = bom_item.part.get_descendants(include_self=False)

                for variant in part_variants:
                    parts.add(variant)

        # Turn into a list of valid IDs (for matching against a Part query)
        part_ids = [part.pk for part in parts]

        return Q(id__in=part_ids)

    def get_used_in(self, include_inherited=True):
        """Return a queryset containing all parts this part is used in.

        Includes consideration of inherited BOMs
        """
        return Part.objects.filter(self.get_used_in_filter(include_inherited=include_inherited))

    @property
    def has_bom(self):
        """Return True if this Part instance has any BOM items"""
        return self.get_bom_items().count() > 0

    def get_trackable_parts(self):
        """Return a queryset of all trackable parts in the BOM for this part."""
        queryset = self.get_bom_items()
        queryset = queryset.filter(sub_part__trackable=True)

        return queryset

    @property
    def has_trackable_parts(self):
        """Return True if any parts linked in the Bill of Materials are trackable.

        This is important when building the part.
        """
        return self.get_trackable_parts().count() > 0

    @property
    def bom_count(self):
        """Return the number of items contained in the BOM for this part."""
        return self.get_bom_items().count()

    @property
    def used_in_count(self):
        """Return the number of part BOMs that this part appears in."""
        return self.get_used_in().count()

    def get_bom_hash(self):
        """Return a checksum hash for the BOM for this part.

        Used to determine if the BOM has changed (and needs to be signed off!)
        The hash is calculated by hashing each line item in the BOM. Returns a string representation of a hash object which can be compared with a stored value
        """
        result_hash = hashlib.md5(str(self.id).encode())

        # List *all* BOM items (including inherited ones!)
        bom_items = self.get_bom_items().all().prefetch_related('sub_part')

        for item in bom_items:
            result_hash.update(str(item.get_item_hash()).encode())

        return str(result_hash.digest())

    def is_bom_valid(self):
        """Check if the BOM is 'valid' - if the calculated checksum matches the stored value."""
        return self.get_bom_hash() == self.bom_checksum or not self.has_bom

    @transaction.atomic
    def validate_bom(self, user):
        """Validate the BOM (mark the BOM as validated by the given User.

        - Calculates and stores the hash for the BOM
        - Saves the current date and the checking user
        """
        # Validate each line item, ignoring inherited ones
        bom_items = self.get_bom_items(include_inherited=False)

        for item in bom_items.all():
            item.validate_hash()

        self.bom_checksum = self.get_bom_hash()
        self.bom_checked_by = user
        self.bom_checked_date = datetime.now().date()

        self.save()

    @transaction.atomic
    def clear_bom(self):
        """Clear the BOM items for the part (delete all BOM lines).

        Note: Does *NOT* delete inherited BOM items!
        """
        self.bom_items.all().delete()

    def getRequiredParts(self, recursive=False, parts=None):
        """Return a list of parts required to make this part (i.e. BOM items).

        Args:
            recursive: If True iterate down through sub-assemblies
            parts: Set of parts already found (to prevent recursion issues)
        """
        if parts is None:
            parts = set()

        bom_items = self.get_bom_items().all()

        for bom_item in bom_items:

            sub_part = bom_item.sub_part

            if sub_part not in parts:

                parts.add(sub_part)

                if recursive:
                    sub_part.getRequiredParts(recursive=True, parts=parts)

        return parts

    @property
    def supplier_count(self):
        """Return the number of supplier parts available for this part."""
        return self.supplier_parts.count()

    @property
    def has_pricing_info(self, internal=False):
        """Return true if there is pricing information for this part."""
        return self.get_price_range(internal=internal) is not None

    @property
    def has_complete_bom_pricing(self):
        """Return true if there is pricing information for each item in the BOM."""
        use_internal = common.models.get_setting('PART_BOM_USE_INTERNAL_PRICE', False)
        for item in self.get_bom_items().all().select_related('sub_part'):
            if not item.sub_part.has_pricing_info(use_internal):
                return False

        return True

    def get_price_info(self, quantity=1, buy=True, bom=True, internal=False):
        """Return a simplified pricing string for this part.

        Args:
            quantity: Number of units to calculate price for
            buy: Include supplier pricing (default = True)
            bom: Include BOM pricing (default = True)
            internal: Include internal pricing (default = False)
        """
        price_range = self.get_price_range(quantity, buy, bom, internal)

        if price_range is None:
            return None

        min_price, max_price = price_range

        if min_price == max_price:
            return min_price

        min_price = normalize(min_price)
        max_price = normalize(max_price)

        return "{a} - {b}".format(a=min_price, b=max_price)

    def get_supplier_price_range(self, quantity=1):
        """Return the supplier price range of this part:

        - Checks if there is any supplier pricing information associated with this Part
        - Iterate through available supplier pricing and select (min, max)
        - Returns tuple of (min, max)

        Arguments:
            quantity: Quantity at which to calculate price (default=1)

        Returns: (min, max) tuple or (None, None) if no supplier pricing available
        """
        min_price = None
        max_price = None

        for supplier in self.supplier_parts.all():

            price = supplier.get_price(quantity)

            if price is None:
                continue

            if min_price is None or price < min_price:
                min_price = price

            if max_price is None or price > max_price:
                max_price = price

        if min_price is None or max_price is None:
            return None

        min_price = normalize(min_price)
        max_price = normalize(max_price)

        return (min_price, max_price)

    def get_bom_price_range(self, quantity=1, internal=False, purchase=False):
        """Return the price range of the BOM for this part.

        Adds the minimum price for all components in the BOM.
        Note: If the BOM contains items without pricing information,
        these items cannot be included in the BOM!
        """
        min_price = None
        max_price = None

        for item in self.get_bom_items().all().select_related('sub_part'):

            if item.sub_part.pk == self.pk:
                logger.warning(f"WARNING: BomItem ID {item.pk} contains itself in BOM")
                continue

            q = decimal.Decimal(quantity)
            i = decimal.Decimal(item.quantity)

            prices = item.sub_part.get_price_range(q * i, internal=internal, purchase=purchase)

            if prices is None:
                continue

            low, high = prices

            if min_price is None:
                min_price = 0

            if max_price is None:
                max_price = 0

            min_price += low
            max_price += high

        if min_price is None or max_price is None:
            return None

        min_price = normalize(min_price)
        max_price = normalize(max_price)

        return (min_price, max_price)

    def get_price_range(self, quantity=1, buy=True, bom=True, internal=False, purchase=False):
        """Return the price range for this part.

        This price can be either:
        - Supplier price (if purchased from suppliers)
        - BOM price (if built from other parts)
        - Internal price (if set for the part)
        - Purchase price (if set for the part)

        Returns:
            Minimum of the supplier, BOM, internal or purchase price. If no pricing available, returns None
        """
        # only get internal price if set and should be used
        if internal and self.has_internal_price_breaks:
            internal_price = self.get_internal_price(quantity)
            return internal_price, internal_price

        # only get purchase price if set and should be used
        if purchase:
            purchase_price = self.get_purchase_price(quantity)
            if purchase_price:
                return purchase_price

        buy_price_range = self.get_supplier_price_range(quantity) if buy else None
        bom_price_range = self.get_bom_price_range(quantity, internal=internal) if bom else None

        if buy_price_range is None:
            return bom_price_range

        elif bom_price_range is None:
            return buy_price_range

        else:
            return (
                min(buy_price_range[0], bom_price_range[0]),
                max(buy_price_range[1], bom_price_range[1])
            )

    base_cost = models.DecimalField(max_digits=10, decimal_places=3, default=0, validators=[MinValueValidator(0)], verbose_name=_('base cost'), help_text=_('Minimum charge (e.g. stocking fee)'))

    multiple = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name=_('multiple'), help_text=_('Sell multiple'))

    get_price = common.models.get_price

    @property
    def has_price_breaks(self):
        """Return True if this part has sale price breaks"""
        return self.price_breaks.count() > 0

    @property
    def price_breaks(self):
        """Return the associated price breaks in the correct order."""
        return self.salepricebreaks.order_by('quantity').all()

    @property
    def unit_pricing(self):
        """Returns the price of this Part at quantity=1"""
        return self.get_price(1)

    def add_price_break(self, quantity, price):
        """Create a new price break for this part.

        Args:
            quantity: Numerical quantity
            price: Must be a Money object
        """
        # Check if a price break at that quantity already exists...
        if self.price_breaks.filter(quantity=quantity, part=self.pk).exists():
            return

        PartSellPriceBreak.objects.create(
            part=self,
            quantity=quantity,
            price=price
        )

    def get_internal_price(self, quantity, moq=True, multiples=True, currency=None):
        """Return the internal price of this Part at the specified quantity"""
        return common.models.get_price(self, quantity, moq, multiples, currency, break_name='internal_price_breaks')

    @property
    def has_internal_price_breaks(self):
        """Return True if this Part has internal pricing information"""
        return self.internal_price_breaks.count() > 0

    @property
    def internal_price_breaks(self):
        """Return the associated price breaks in the correct order."""
        return self.internalpricebreaks.order_by('quantity').all()

    def get_purchase_price(self, quantity):
        """Calculate the purchase price for this part at the specified quantity

        - Looks at available supplier pricing data
        - Calculates the price base on the closest price point
        """
        currency = currency_code_default()
        try:
            prices = [convert_money(item.purchase_price, currency).amount for item in self.stock_items.all() if item.purchase_price]
        except MissingRate:
            prices = None

        if prices:
            return min(prices) * quantity, max(prices) * quantity

        return None

    @transaction.atomic
    def copy_bom_from(self, other, clear=True, **kwargs):
        """Copy the BOM from another part.

        Args:
            other: The part to copy the BOM from
            clear (bool, optional): Remove existing BOM items first. Defaults to True.
        """
        # Ignore if the other part is actually this part?
        if other == self:
            return

        if clear:
            # Remove existing BOM items
            # Note: Inherited BOM items are *not* deleted!
            self.bom_items.all().delete()

        # List of "ancestor" parts above this one
        my_ancestors = self.get_ancestors(include_self=False)

        raise_error = not kwargs.get('skip_invalid', True)

        include_inherited = kwargs.get('include_inherited', False)

        # Should substitute parts be duplicated?
        copy_substitutes = kwargs.get('copy_substitutes', True)

        # Copy existing BOM items from another part
        # Note: Inherited BOM Items will *not* be duplicated!!
        for bom_item in other.get_bom_items(include_inherited=include_inherited).all():
            # If this part already has a BomItem pointing to the same sub-part,
            # delete that BomItem from this part first!

            # Ignore invalid BomItem objects
            if not bom_item.part or not bom_item.sub_part:
                continue

            # Ignore ancestor parts which are inherited
            if bom_item.part in my_ancestors and bom_item.inherited:
                continue

            # Skip if already exists
            if BomItem.objects.filter(part=self, sub_part=bom_item.sub_part).exists():
                continue

            # Skip (or throw error) if BomItem is not valid
            if not bom_item.sub_part.check_add_to_bom(self, raise_error=raise_error):
                continue

            # Obtain a list of direct substitute parts against this BomItem
            substitutes = BomItemSubstitute.objects.filter(bom_item=bom_item)

            # Construct a new BOM item
            bom_item.part = self
            bom_item.pk = None

            bom_item.save()
            bom_item.refresh_from_db()

            if copy_substitutes:
                for sub in substitutes:
                    # Duplicate the substitute (and point to the *new* BomItem object)
                    sub.pk = None
                    sub.bom_item = bom_item
                    sub.save()

    @transaction.atomic
    def copy_parameters_from(self, other, **kwargs):
        """Copy all parameter values from another Part instance"""
        clear = kwargs.get('clear', True)

        if clear:
            self.get_parameters().delete()

        for parameter in other.get_parameters():

            # If this part already has a parameter pointing to the same template,
            # delete that parameter from this part first!

            try:
                existing = PartParameter.objects.get(part=self, template=parameter.template)
                existing.delete()
            except (PartParameter.DoesNotExist):
                pass

            parameter.part = self
            parameter.pk = None

            parameter.save()

    @transaction.atomic
    def deep_copy(self, other, **kwargs):
        """Duplicates non-field data from another part.

        Does not alter the normal fields of this part, but can be used to copy other data linked by ForeignKey refernce.

        Keyword Args:
            image: If True, copies Part image (default = True)
            bom: If True, copies BOM data (default = False)
            parameters: If True, copies Parameters data (default = True)
        """
        # Copy the part image
        if kwargs.get('image', True):
            if other.image:
                # Reference the other image from this Part
                self.image = other.image

        # Copy the BOM data
        if kwargs.get('bom', False):
            self.copy_bom_from(other)

        # Copy the parameters data
        if kwargs.get('parameters', True):
            self.copy_parameters_from(other)

        # Copy the fields that aren't available in the duplicate form
        self.salable = other.salable
        self.assembly = other.assembly
        self.component = other.component
        self.purchaseable = other.purchaseable
        self.trackable = other.trackable
        self.virtual = other.virtual

        self.save()

    def getTestTemplates(self, required=None, include_parent=True):
        """Return a list of all test templates associated with this Part.

        These are used for validation of a StockItem.

        Args:
            required: Set to True or False to filter by "required" status
            include_parent: Set to True to traverse upwards
        """
        if include_parent:
            tests = PartTestTemplate.objects.filter(part__in=self.get_ancestors(include_self=True))
        else:
            tests = self.test_templates

        if required is not None:
            tests = tests.filter(required=required)

        return tests

    def getRequiredTests(self):
        """Return the tests which are required by this part"""
        return self.getTestTemplates(required=True)

    @property
    def attachment_count(self):
        """Count the number of attachments for this part.

        If the part is a variant of a template part,
        include the number of attachments for the template part.
        """
        return self.part_attachments.count()

    @property
    def part_attachments(self):
        """Return *all* attachments for this part, potentially including attachments for template parts above this one."""
        ancestors = self.get_ancestors(include_self=True)

        attachments = PartAttachment.objects.filter(part__in=ancestors)

        return attachments

    def sales_orders(self):
        """Return a list of sales orders which reference this part."""
        orders = []

        for line in self.sales_order_line_items.all().prefetch_related('order'):
            if line.order not in orders:
                orders.append(line.order)

        return orders

    def purchase_orders(self):
        """Return a list of purchase orders which reference this part."""
        orders = []

        for part in self.supplier_parts.all().prefetch_related('purchase_order_line_items'):
            for order in part.purchase_orders():
                if order not in orders:
                    orders.append(order)

        return orders

    @property
    def on_order(self):
        """Return the total number of items on order for this part."""
        orders = self.supplier_parts.filter(purchase_order_line_items__order__status__in=PurchaseOrderStatus.OPEN).aggregate(
            quantity=Sum('purchase_order_line_items__quantity'),
            received=Sum('purchase_order_line_items__received')
        )

        quantity = orders['quantity']
        received = orders['received']

        if quantity is None:
            quantity = 0

        if received is None:
            received = 0

        return quantity - received

    def get_parameters(self):
        """Return all parameters for this part, ordered by name."""
        return self.parameters.order_by('template__name')

    def parameters_map(self):
        """Return a map (dict) of parameter values assocaited with this Part instance, of the form.

        Example:
        {
            "name_1": "value_1",
            "name_2": "value_2",
        }
        """
        params = {}

        for parameter in self.parameters.all():
            params[parameter.template.name] = parameter.data

        return params

    @property
    def has_variants(self):
        """Check if this Part object has variants underneath it."""
        return self.get_all_variants().count() > 0

    def get_all_variants(self):
        """Return all Part object which exist as a variant under this part."""
        return self.get_descendants(include_self=False)

    @property
    def can_convert(self):
        """Check if this Part can be "converted" to a different variant.

        It can be converted if:
        a) It has non-virtual variant parts underneath it
        b) It has non-virtual template parts above it
        c) It has non-virtual sibling variants
        """
        return self.get_conversion_options().count() > 0

    def get_conversion_options(self):
        """Return options for converting this part to a "variant" within the same tree.

        a) Variants underneath this one
        b) Immediate parent
        c) Siblings
        """
        parts = []

        # Child parts
        children = self.get_descendants(include_self=False)

        for child in children:
            parts.append(child)

        # Immediate parent, and siblings
        if self.variant_of:
            parts.append(self.variant_of)

            siblings = self.get_siblings(include_self=False)

            for sib in siblings:
                parts.append(sib)

        filtered_parts = Part.objects.filter(pk__in=[part.pk for part in parts])

        # Ensure this part is not in the queryset, somehow
        filtered_parts = filtered_parts.exclude(pk=self.pk)

        filtered_parts = filtered_parts.filter(
            active=True,
            virtual=False,
        )

        return filtered_parts

    def get_related_parts(self):
        """Return list of tuples for all related parts.

        Includes:
        - first value is PartRelated object
        - second value is matching Part object
        """
        related_parts = []

        related_parts_1 = self.related_parts_1.filter(part_1__id=self.pk)

        related_parts_2 = self.related_parts_2.filter(part_2__id=self.pk)

        related_parts.append()

        for related_part in related_parts_1:
            # Add to related parts list
            related_parts.append(related_part.part_2)

        for related_part in related_parts_2:
            # Add to related parts list
            related_parts.append(related_part.part_1)

        return related_parts

    @property
    def related_count(self):
        """Return the number of 'related parts' which point to this Part"""
        return len(self.get_related_parts())

    def is_part_low_on_stock(self):
        """Returns True if the total stock for this part is less than the minimum stock level."""
        return self.get_stock_count() < self.minimum_stock


@receiver(post_save, sender=Part, dispatch_uid='part_post_save_log')
def after_save_part(sender, instance: Part, created, **kwargs):
    """Function to be executed after a Part is saved."""
    from part import tasks as part_tasks

    if not created and not InvenTree.ready.isImportingData():
        # Check part stock only if we are *updating* the part (not creating it)

        # Run this check in the background
        InvenTree.tasks.offload_task(part_tasks.notify_low_stock_if_required, instance)


class PartAttachment(InvenTreeAttachment):
    """Model for storing file attachments against a Part object."""

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartAttachment model"""
        return reverse('api-part-attachment-list')

    def getSubdir(self):
        """Returns the media subdirectory where part attachments are stored"""
        return os.path.join("part_files", str(self.part.id))

    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             verbose_name=_('Part'), related_name='attachments')


class PartSellPriceBreak(common.models.PriceBreak):
    """Represents a price break for selling this part."""

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartSellPriceBreak model"""
        return reverse('api-part-sale-price-list')

    part = models.ForeignKey(
        Part, on_delete=models.CASCADE,
        related_name='salepricebreaks',
        limit_choices_to={'salable': True},
        verbose_name=_('Part')
    )

    class Meta:
        """Metaclass providing extra model definition"""
        unique_together = ('part', 'quantity')


class PartInternalPriceBreak(common.models.PriceBreak):
    """Represents a price break for internally selling this part."""

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartInternalPriceBreak model"""
        return reverse('api-part-internal-price-list')

    part = models.ForeignKey(
        Part, on_delete=models.CASCADE,
        related_name='internalpricebreaks',
        verbose_name=_('Part')
    )

    class Meta:
        """Metaclass providing extra model definition"""
        unique_together = ('part', 'quantity')


class PartStar(models.Model):
    """A PartStar object creates a subscription relationship between a User and a Part.

    It is used to designate a Part as 'subscribed' for a given User.

    Attributes:
        part: Link to a Part object
        user: Link to a User object
    """

    part = models.ForeignKey(Part, on_delete=models.CASCADE, verbose_name=_('Part'), related_name='starred_users')

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('User'), related_name='starred_parts')

    class Meta:
        """Metaclass providing extra model definition"""
        unique_together = [
            'part',
            'user'
        ]


class PartCategoryStar(models.Model):
    """A PartCategoryStar creates a subscription relationship between a User and a PartCategory.

    Attributes:
        category: Link to a PartCategory object
        user: Link to a User object
    """

    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE, verbose_name=_('Category'), related_name='starred_users')

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('User'), related_name='starred_categories')

    class Meta:
        """Metaclass providing extra model definition"""
        unique_together = [
            'category',
            'user',
        ]


class PartTestTemplate(models.Model):
    """A PartTestTemplate defines a 'template' for a test which is required to be run against a StockItem (an instance of the Part).

    The test template applies "recursively" to part variants, allowing tests to be
    defined in a heirarchy.

    Test names are simply strings, rather than enforcing any sort of structure or pattern.
    It is up to the user to determine what tests are defined (and how they are run).

    To enable generation of unique lookup-keys for each test, there are some validation tests
    run on the model (refer to the validate_unique function).
    """

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartTestTemplate model"""
        return reverse('api-part-test-template-list')

    def save(self, *args, **kwargs):
        """Enforce 'clean' operation when saving a PartTestTemplate instance"""
        self.clean()

        super().save(*args, **kwargs)

    def clean(self):
        """Clean fields for the PartTestTemplate model"""
        self.test_name = self.test_name.strip()

        self.validate_unique()
        super().clean()

    def validate_unique(self, exclude=None):
        """Test that this test template is 'unique' within this part tree."""
        if not self.part.trackable:
            raise ValidationError({
                'part': _('Test templates can only be created for trackable parts')
            })

        # Get a list of all tests "above" this one
        tests = PartTestTemplate.objects.filter(
            part__in=self.part.get_ancestors(include_self=True)
        )

        # If this item is already in the database, exclude it from comparison!
        if self.pk is not None:
            tests = tests.exclude(pk=self.pk)

        key = self.key

        for test in tests:
            if test.key == key:
                raise ValidationError({
                    'test_name': _("Test with this name already exists for this part")
                })

        super().validate_unique(exclude)

    @property
    def key(self):
        """Generate a key for this test."""
        return helpers.generateTestKey(self.test_name)

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='test_templates',
        limit_choices_to={'trackable': True},
        verbose_name=_('Part'),
    )

    test_name = models.CharField(
        blank=False, max_length=100,
        verbose_name=_("Test Name"),
        help_text=_("Enter a name for the test")
    )

    description = models.CharField(
        blank=False, null=True, max_length=100,
        verbose_name=_("Test Description"),
        help_text=_("Enter description for this test")
    )

    required = models.BooleanField(
        default=True,
        verbose_name=_("Required"),
        help_text=_("Is this test required to pass?")
    )

    requires_value = models.BooleanField(
        default=False,
        verbose_name=_("Requires Value"),
        help_text=_("Does this test require a value when adding a test result?")
    )

    requires_attachment = models.BooleanField(
        default=False,
        verbose_name=_("Requires Attachment"),
        help_text=_("Does this test require a file attachment when adding a test result?")
    )


def validate_template_name(name):
    """Prevent illegal characters in "name" field for PartParameterTemplate."""
    for c in "!@#$%^&*()<>{}[].,?/\\|~`_+-=\'\"":  # noqa: P103
        if c in str(name):
            raise ValidationError(_(f"Illegal character in template name ({c})"))


class PartParameterTemplate(models.Model):
    """A PartParameterTemplate provides a template for key:value pairs for extra parameters fields/values to be added to a Part.

    This allows users to arbitrarily assign data fields to a Part beyond the built-in attributes.

    Attributes:
        name: The name (key) of the Parameter [string]
        units: The units of the Parameter [string]
    """

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartParameterTemplate model"""
        return reverse('api-part-parameter-template-list')

    def __str__(self):
        """Return a string representation of a PartParameterTemplate instance"""
        s = str(self.name)
        if self.units:
            s += " ({units})".format(units=self.units)
        return s

    def validate_unique(self, exclude=None):
        """Ensure that PartParameterTemplates cannot be created with the same name.

        This test should be case-insensitive (which the unique caveat does not cover).
        """
        super().validate_unique(exclude)

        try:
            others = PartParameterTemplate.objects.filter(name__iexact=self.name).exclude(pk=self.pk)

            if others.exists():
                msg = _("Parameter template name must be unique")
                raise ValidationError({"name": msg})
        except PartParameterTemplate.DoesNotExist:
            pass

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Parameter Name'),
        unique=True,
        validators=[
            validate_template_name,
        ]
    )

    units = models.CharField(max_length=25, verbose_name=_('Units'), help_text=_('Parameter Units'), blank=True)


class PartParameter(models.Model):
    """A PartParameter is a specific instance of a PartParameterTemplate. It assigns a particular parameter <key:value> pair to a part.

    Attributes:
        part: Reference to a single Part object
        template: Reference to a single PartParameterTemplate object
        data: The data (value) of the Parameter [string]
    """

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartParameter model"""
        return reverse('api-part-parameter-list')

    def __str__(self):
        """String representation of a PartParameter (used in the admin interface)"""
        return "{part} : {param} = {data}{units}".format(
            part=str(self.part.full_name),
            param=str(self.template.name),
            data=str(self.data),
            units=str(self.template.units)
        )

    class Meta:
        """Metaclass providing extra model definition"""
        # Prevent multiple instances of a parameter for a single part
        unique_together = ('part', 'template')

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='parameters', verbose_name=_('Part'), help_text=_('Parent Part'))

    template = models.ForeignKey(PartParameterTemplate, on_delete=models.CASCADE, related_name='instances', verbose_name=_('Template'), help_text=_('Parameter Template'))

    data = models.CharField(max_length=500, verbose_name=_('Data'), help_text=_('Parameter Value'))

    @classmethod
    def create(cls, part, template, data, save=False):
        """Custom save method for the PartParameter class"""
        part_parameter = cls(part=part, template=template, data=data)
        if save:
            part_parameter.save()
        return part_parameter


class PartCategoryParameterTemplate(models.Model):
    """A PartCategoryParameterTemplate creates a unique relationship between a PartCategory and a PartParameterTemplate. Multiple PartParameterTemplate instances can be associated to a PartCategory to drive a default list of parameter templates attached to a Part instance upon creation.

    Attributes:
        category: Reference to a single PartCategory object
        parameter_template: Reference to a single PartParameterTemplate object
        default_value: The default value for the parameter in the context of the selected
                       category
    """

    class Meta:
        """Metaclass providing extra model definition"""
        constraints = [
            UniqueConstraint(fields=['category', 'parameter_template'],
                             name='unique_category_parameter_template_pair')
        ]

    def __str__(self):
        """String representation of a PartCategoryParameterTemplate (admin interface)."""
        if self.default_value:
            return f'{self.category.name} | {self.parameter_template.name} | {self.default_value}'
        else:
            return f'{self.category.name} | {self.parameter_template.name}'

    category = models.ForeignKey(PartCategory,
                                 on_delete=models.CASCADE,
                                 related_name='parameter_templates',
                                 verbose_name=_('Category'),
                                 help_text=_('Part Category'))

    parameter_template = models.ForeignKey(PartParameterTemplate,
                                           on_delete=models.CASCADE,
                                           related_name='part_categories',
                                           verbose_name=_('Parameter Template'),
                                           help_text=_('Parameter Template'))

    default_value = models.CharField(max_length=500,
                                     blank=True,
                                     verbose_name=_('Default Value'),
                                     help_text=_('Default Parameter Value'))


class BomItem(DataImportMixin, models.Model):
    """A BomItem links a part to its component items.

    A part can have a BOM (bill of materials) which defines
    which parts are required (and in what quantity) to make it.

    Attributes:
        part: Link to the parent part (the part that will be produced)
        sub_part: Link to the child part (the part that will be consumed)
        quantity: Number of 'sub_parts' consumed to produce one 'part'
        optional: Boolean field describing if this BomItem is optional
        reference: BOM reference field (e.g. part designators)
        overage: Estimated losses for a Build. Can be expressed as absolute value (e.g. '7') or a percentage (e.g. '2%')
        note: Note field for this BOM item
        checksum: Validation checksum for the particular BOM line item
        inherited: This BomItem can be inherited by the BOMs of variant parts
        allow_variants: Stock for part variants can be substituted for this BomItem
    """

    # Fields available for bulk import
    IMPORT_FIELDS = {
        'quantity': {
            'required': True
        },
        'reference': {},
        'overage': {},
        'allow_variants': {},
        'inherited': {},
        'optional': {},
        'note': {},
        'part': {
            'label': _('Part'),
            'help_text': _('Part ID or part name'),
        },
        'part_id': {
            'label': _('Part ID'),
            'help_text': _('Unique part ID value')
        },
        'part_name': {
            'label': _('Part Name'),
            'help_text': _('Part name'),
        },
        'part_ipn': {
            'label': _('Part IPN'),
            'help_text': _('Part IPN value'),
        },
        'level': {
            'label': _('Level'),
            'help_text': _('BOM level'),
        }
    }

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the BomItem model"""
        return reverse('api-bom-list')

    def get_valid_parts_for_allocation(self, allow_variants=True, allow_substitutes=True):
        """Return a list of valid parts which can be allocated against this BomItem.

        Includes:
        - The referenced sub_part
        - Any directly specvified substitute parts
        - If allow_variants is True, all variants of sub_part
        """
        # Set of parts we will allow
        parts = set()

        parts.add(self.sub_part)

        # Variant parts (if allowed)
        if allow_variants and self.allow_variants:
            for variant in self.sub_part.get_descendants(include_self=False):
                parts.add(variant)

        # Substitute parts
        if allow_substitutes:
            for sub in self.substitutes.all():
                parts.add(sub.part)

        valid_parts = []

        for p in parts:

            # Inactive parts cannot be 'auto allocated'
            if not p.active:
                continue

            # Trackable status must be the same as the sub_part
            if p.trackable != self.sub_part.trackable:
                continue

            valid_parts.append(p)

        return valid_parts

    def is_stock_item_valid(self, stock_item):
        """Check if the provided StockItem object is "valid" for assignment against this BomItem."""
        return stock_item.part in self.get_valid_parts_for_allocation()

    def get_stock_filter(self):
        """Return a queryset filter for selecting StockItems which match this BomItem.

        - Allow stock from all directly specified substitute parts
        - If allow_variants is True, allow all part variants
        """
        return Q(part__in=[part.pk for part in self.get_valid_parts_for_allocation()])

    def save(self, *args, **kwargs):
        """Enforce 'clean' operation when saving a BomItem instance"""
        self.clean()
        super().save(*args, **kwargs)

    # A link to the parent part
    # Each part will get a reverse lookup field 'bom_items'
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='bom_items',
                             verbose_name=_('Part'),
                             help_text=_('Select parent part'),
                             limit_choices_to={
                                 'assembly': True,
                             })

    # A link to the child item (sub-part)
    # Each part will get a reverse lookup field 'used_in'
    sub_part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='used_in',
                                 verbose_name=_('Sub part'),
                                 help_text=_('Select part to be used in BOM'),
                                 limit_choices_to={
                                     'component': True,
                                 })

    # Quantity required
    quantity = models.DecimalField(default=1.0, max_digits=15, decimal_places=5, validators=[MinValueValidator(0)], verbose_name=_('Quantity'), help_text=_('BOM quantity for this BOM item'))

    optional = models.BooleanField(default=False, verbose_name=_('Optional'), help_text=_("This BOM item is optional"))

    overage = models.CharField(max_length=24, blank=True, validators=[validators.validate_overage],
                               verbose_name=_('Overage'),
                               help_text=_('Estimated build wastage quantity (absolute or percentage)')
                               )

    reference = models.CharField(max_length=500, blank=True, verbose_name=_('Reference'), help_text=_('BOM item reference'))

    # Note attached to this BOM line item
    note = models.CharField(max_length=500, blank=True, verbose_name=_('Note'), help_text=_('BOM item notes'))

    checksum = models.CharField(max_length=128, blank=True, verbose_name=_('Checksum'), help_text=_('BOM line checksum'))

    inherited = models.BooleanField(
        default=False,
        verbose_name=_('Inherited'),
        help_text=_('This BOM item is inherited by BOMs for variant parts'),
    )

    allow_variants = models.BooleanField(
        default=False,
        verbose_name=_('Allow Variants'),
        help_text=_('Stock items for variant parts can be used for this BOM item')
    )

    def get_item_hash(self):
        """Calculate the checksum hash of this BOM line item.

        The hash is calculated from the following fields:
        - Part.full_name (if the part name changes, the BOM checksum is invalidated)
        - Quantity
        - Reference field
        - Note field
        - Optional field
        - Inherited field
        """
        # Seed the hash with the ID of this BOM item
        result_hash = hashlib.md5(str(self.id).encode())

        # Update the hash based on line information
        result_hash.update(str(self.sub_part.id).encode())
        result_hash.update(str(self.sub_part.full_name).encode())
        result_hash.update(str(self.quantity).encode())
        result_hash.update(str(self.note).encode())
        result_hash.update(str(self.reference).encode())
        result_hash.update(str(self.optional).encode())
        result_hash.update(str(self.inherited).encode())

        return str(result_hash.digest())

    def validate_hash(self, valid=True):
        """Mark this item as 'valid' (store the checksum hash).

        Args:
            valid: If true, validate the hash, otherwise invalidate it (default = True)
        """
        if valid:
            self.checksum = str(self.get_item_hash())
        else:
            self.checksum = ''

        self.save()

    @property
    def is_line_valid(self):
        """Check if this line item has been validated by the user."""
        # Ensure an empty checksum returns False
        if len(self.checksum) == 0:
            return False

        return self.get_item_hash() == self.checksum

    def clean(self):
        """Check validity of the BomItem model.

        Performs model checks beyond simple field validation.

        - A part cannot refer to itself in its BOM
        - A part cannot refer to a part which refers to it

        - If the "sub_part" is trackable, then the "part" must be trackable too!
        """
        super().clean()

        try:
            self.quantity = Decimal(self.quantity)
        except InvalidOperation:
            raise ValidationError({
                'quantity': _('Must be a valid number')
            })

        try:
            # Check for circular BOM references
            if self.sub_part:
                self.sub_part.check_add_to_bom(self.part, raise_error=True)

                # If the sub_part is 'trackable' then the 'quantity' field must be an integer
                if self.sub_part.trackable:
                    if self.quantity != int(self.quantity):
                        raise ValidationError({
                            "quantity": _("Quantity must be integer value for trackable parts")
                        })

                    # Force the upstream part to be trackable if the sub_part is trackable
                    if not self.part.trackable:
                        self.part.trackable = True
                        self.part.clean()
                        self.part.save()
            else:
                raise ValidationError({'sub_part': _('Sub part must be specified')})
        except Part.DoesNotExist:
            raise ValidationError({'sub_part': _('Sub part must be specified')})

    class Meta:
        """Metaclass providing extra model definition"""
        verbose_name = _("BOM Item")

    def __str__(self):
        """Return a string representation of this BomItem instance"""
        return "{n} x {child} to make {parent}".format(
            parent=self.part.full_name,
            child=self.sub_part.full_name,
            n=decimal2string(self.quantity))

    def get_overage_quantity(self, quantity):
        """Calculate overage quantity."""
        # Most of the time overage string will be empty
        if len(self.overage) == 0:
            return 0

        overage = str(self.overage).strip()

        # Is the overage a numerical value?
        try:
            ovg = float(overage)

            if ovg < 0:
                ovg = 0

            return ovg
        except ValueError:
            pass

        # Is the overage a percentage?
        if overage.endswith('%'):
            overage = overage[:-1].strip()

            try:
                percent = float(overage) / 100.0
                if percent > 1:
                    percent = 1
                if percent < 0:
                    percent = 0

                # Must be represented as a decimal
                percent = Decimal(percent)

                return float(percent * quantity)

            except ValueError:
                pass

        # Default = No overage
        return 0

    def get_required_quantity(self, build_quantity):
        """Calculate the required part quantity, based on the supplier build_quantity. Includes overage estimate in the returned value.

        Args:
            build_quantity: Number of parts to build

        Returns:
            Quantity required for this build (including overage)
        """
        # Base quantity requirement
        base_quantity = self.quantity * build_quantity

        # Overage requiremet
        ovrg_quantity = self.get_overage_quantity(base_quantity)

        required = float(base_quantity) + float(ovrg_quantity)

        return required

    @property
    def price_range(self, internal=False):
        """Return the price-range for this BOM item."""
        # get internal price setting
        use_internal = common.models.InvenTreeSetting.get_setting('PART_BOM_USE_INTERNAL_PRICE', False)
        prange = self.sub_part.get_price_range(self.quantity, internal=use_internal and internal)

        if prange is None:
            return prange

        pmin, pmax = prange

        if pmin == pmax:
            return decimal2money(pmin)

        # Convert to better string representation
        pmin = decimal2money(pmin)
        pmax = decimal2money(pmax)

        return "{pmin} to {pmax}".format(pmin=pmin, pmax=pmax)


class BomItemSubstitute(models.Model):
    """A BomItemSubstitute provides a specification for alternative parts, which can be used in a bill of materials.

    Attributes:
        bom_item: Link to the parent BomItem instance
        part: The part which can be used as a substitute
    """

    class Meta:
        """Metaclass providing extra model definition"""
        verbose_name = _("BOM Item Substitute")

        # Prevent duplication of substitute parts
        unique_together = ('part', 'bom_item')

    def save(self, *args, **kwargs):
        """Enforce a full_clean when saving the BomItemSubstitute model"""
        self.full_clean()

        super().save(*args, **kwargs)

    def validate_unique(self, exclude=None):
        """Ensure that this BomItemSubstitute is "unique".

        Ensure:
        - It cannot point to the same "part" as the "sub_part" of the parent "bom_item"
        """
        super().validate_unique(exclude=exclude)

        if self.part == self.bom_item.sub_part:
            raise ValidationError({
                "part": _("Substitute part cannot be the same as the master part"),
            })

    @staticmethod
    def get_api_url():
        """Returns the list API endpoint URL associated with this model"""
        return reverse('api-bom-substitute-list')

    bom_item = models.ForeignKey(
        BomItem,
        on_delete=models.CASCADE,
        related_name='substitutes',
        verbose_name=_('BOM Item'),
        help_text=_('Parent BOM item'),
    )

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='substitute_items',
        verbose_name=_('Part'),
        help_text=_('Substitute part'),
        limit_choices_to={
            'component': True,
        }
    )


class PartRelated(models.Model):
    """Store and handle related parts (eg. mating connector, crimps, etc.)."""

    part_1 = models.ForeignKey(Part, related_name='related_parts_1',
                               verbose_name=_('Part 1'), on_delete=models.DO_NOTHING)

    part_2 = models.ForeignKey(Part, related_name='related_parts_2',
                               on_delete=models.DO_NOTHING,
                               verbose_name=_('Part 2'), help_text=_('Select Related Part'))

    def __str__(self):
        """Return a string representation of this Part-Part relationship"""
        return f'{self.part_1} <--> {self.part_2}'

    def validate(self, part_1, part_2):
        """Validate that the two parts relationship is unique."""
        validate = True

        parts = Part.objects.all()
        related_parts = PartRelated.objects.all()

        # Check if part exist and there are not the same part
        if (part_1 in parts and part_2 in parts) and (part_1.pk != part_2.pk):
            # Check if relation exists already
            for relation in related_parts:
                if (part_1 == relation.part_1 and part_2 == relation.part_2) \
                   or (part_1 == relation.part_2 and part_2 == relation.part_1):
                    validate = False
                    break
        else:
            validate = False

        return validate

    def clean(self):
        """Overwrite clean method to check that relation is unique."""
        validate = self.validate(self.part_1, self.part_2)

        if not validate:
            error_message = _('Error creating relationship: check that '
                              'the part is not related to itself '
                              'and that the relationship is unique')

            raise ValidationError(error_message)
