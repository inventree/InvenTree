"""Part database model definitions."""

from __future__ import annotations

import decimal
import hashlib
import inspect
import math
import os
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import cast

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, QuerySet, Sum, UniqueConstraint
from django.db.models.functions import Coalesce
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from django_cleanup import cleanup
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money
from mptt.managers import TreeManager
from mptt.models import TreeForeignKey
from taggit.managers import TaggableManager

import common.currency
import common.models
import InvenTree.conversion
import InvenTree.fields
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import part.helpers as part_helpers
import part.settings as part_settings
import report.mixins
import users.models
from build import models as BuildModels
from build.status_codes import BuildStatusGroups
from common.currency import currency_code_default
from common.icons import validate_icon
from common.settings import get_global_setting
from company.models import SupplierPart
from InvenTree import helpers, validators
from InvenTree.exceptions import log_error
from InvenTree.fields import InvenTreeURLField
from InvenTree.helpers import decimal2money, decimal2string, normalize
from order import models as OrderModels
from order.status_codes import (
    PurchaseOrderStatus,
    PurchaseOrderStatusGroups,
    SalesOrderStatusGroups,
)
from stock import models as StockModels

logger = structlog.get_logger('inventree')


class PartCategory(
    InvenTree.models.PluginValidationMixin,
    InvenTree.models.MetadataMixin,
    InvenTree.models.PathStringMixin,
    InvenTree.models.InvenTreeTree,
):
    """PartCategory provides hierarchical organization of Part objects.

    Attributes:
        name: Name of this category
        parent: Parent category
        default_location: Default storage location for parts in this category or child categories
        default_keywords: Default keywords for parts created in this category
    """

    ITEM_PARENT_KEY = 'category'

    EXTRA_PATH_FIELDS = ['icon']

    class Meta:
        """Metaclass defines extra model properties."""

        verbose_name = _('Part Category')
        verbose_name_plural = _('Part Categories')

    def delete(self, *args, **kwargs):
        """Custom model deletion routine, which updates any child categories or parts.

        This must be handled within a transaction.atomic(), otherwise the tree structure is damaged
        """
        super().delete(
            delete_children=kwargs.get('delete_child_categories', False),
            delete_items=kwargs.get('delete_parts', False),
        )

    default_location = TreeForeignKey(
        'stock.StockLocation',
        related_name='default_categories',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Default Location'),
        help_text=_('Default location for parts in this category'),
    )

    structural = models.BooleanField(
        default=False,
        verbose_name=_('Structural'),
        help_text=_(
            'Parts may not be directly assigned to a structural category, '
            'but may be assigned to child categories.'
        ),
    )

    default_keywords = models.CharField(
        null=True,
        blank=True,
        max_length=250,
        verbose_name=_('Default keywords'),
        help_text=_('Default keywords for parts in this category'),
    )

    _icon = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        verbose_name=_('Icon'),
        help_text=_('Icon (optional)'),
        validators=[validate_icon],
        db_column='icon',
    )

    @property
    def icon(self):
        """Return the icon associated with this PartCategory or the default icon."""
        if self._icon:
            return self._icon

        if default_icon := get_global_setting('PART_CATEGORY_DEFAULT_ICON', cache=True):
            return default_icon

        return ''

    @icon.setter
    def icon(self, value):
        """Setter for icon field."""
        default_icon = get_global_setting('PART_CATEGORY_DEFAULT_ICON', cache=True)

        # if icon is not defined previously and new value is default icon, do not save it
        if not self._icon and value == default_icon:
            return

        self._icon = value

    @staticmethod
    def get_api_url():
        """Return the API url associated with the PartCategory model."""
        return reverse('api-part-category-list')

    def get_absolute_url(self):
        """Return the web URL associated with the detail view for this PartCategory instance."""
        return helpers.pui_url(f'/part/category/{self.id}')

    def clean(self):
        """Custom clean action for the PartCategory model.

        Ensure that the structural parameter cannot get set if products already assigned to the category
        """
        if self.pk and self.structural and self.partcount(False, False) > 0:
            raise ValidationError(
                _(
                    'You cannot make this part category structural because some parts '
                    'are already assigned to it!'
                )
            )
        super().clean()

    def get_parts(self, cascade=True) -> set[Part]:
        """Return a queryset for all parts under this category.

        Args:
            cascade (bool, optional): If True, also look under subcategories. Defaults to True.

        Returns:
            set[Part]: All matching parts
        """
        if cascade:
            """Select any parts which exist in this category or any child categories."""
            queryset = Part.objects.filter(
                category__in=self.getUniqueChildren(include_self=True)
            )
        else:
            queryset = Part.objects.filter(category=self.pk)

        return queryset

    @property
    def item_count(self):
        """Return the number of parts contained in this PartCategory."""
        return self.partcount()

    def get_items(self, cascade=False):
        """Return a queryset containing the parts which exist in this category."""
        return self.get_parts(cascade=cascade)

    def partcount(self, cascade=True, active=False):
        """Return the total part count under this category (including children of child categories)."""
        query = self.get_parts(cascade=cascade)

        if active:
            query = query.filter(active=True)

        return query.count()

    def prefetch_parts_parameters(self, cascade=True):
        """Prefectch parts parameters."""
        return (
            self.get_parts(cascade=cascade)
            .prefetch_related('parameters_list', 'parameters_list__template')
            .all()
        )

    def get_unique_parameters(self, cascade=True, prefetch=None):
        """Get all unique parameter names for all parts from this category."""
        unique_parameters_names = []

        parts = prefetch or self.prefetch_parts_parameters(cascade=cascade)

        for part in parts:
            for parameter in part.parameters_list.all():
                parameter_name = parameter.template.name
                if parameter_name not in unique_parameters_names:
                    unique_parameters_names.append(parameter_name)

        return sorted(unique_parameters_names)

    def get_parts_parameters(self, cascade=True, prefetch=None):
        """Get all parameter names and values for all parts from this category."""
        category_parameters = []

        parts = prefetch or self.prefetch_parts_parameters(cascade=cascade)

        for part in parts:
            part_parameters = {
                'pk': part.pk,
                'name': part.name,
                'description': part.description,
            }
            # Add IPN only if it exists
            if part.IPN:
                part_parameters['IPN'] = part.IPN

            for parameter in part.parameters_list.all():
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
        prefetch = PartCategoryParameterTemplate.objects.prefetch_related(
            'category', 'parameter'
        )

        return prefetch.filter(category=self.id)

    def get_subscribers(self, include_parents: bool = True) -> list[User]:
        """Return a list of users who subscribe to this PartCategory.

        Arguments:
            include_parents (bool): If True, include users who subscribe to parent categories.

        Returns:
            list[User]: List of users who subscribe to this category.
        """
        subscribers = set()

        if include_parents:
            cats = self.get_ancestors(include_self=True)
            queryset = PartCategoryStar.objects.filter(category__in=cats)
        else:
            queryset = PartCategoryStar.objects.filter(category=self)

        for result in queryset:
            subscribers.add(result.user)

        return list(subscribers)

    def is_starred_by(self, user, **kwargs):
        """Returns True if the specified user subscribes to this category."""
        return user in self.get_subscribers(**kwargs)

    def set_starred(self, user, status: bool, **kwargs) -> None:
        """Set the "subscription" status of this PartCategory against the specified user."""
        if not user:
            return

        if self.is_starred_by(user, **kwargs) == status:
            return

        if status:
            PartCategoryStar.objects.create(category=self, user=user)
        else:
            # Note that this won't actually stop the user being subscribed,
            # if the user is subscribed to a parent category
            PartCategoryStar.objects.filter(category=self, user=user).delete()


def rename_part_image(instance, filename):
    """Function for renaming a part image file.

    Args:
        instance: Instance of a Part object
        filename: Name of original uploaded file

    Returns:
        Cleaned filename in format part_<n>_img
    """
    base = part_helpers.PART_IMAGE_DIR
    fname = os.path.basename(filename)

    return os.path.join(base, fname)


class PartCategoryParameterTemplate(InvenTree.models.InvenTreeMetadataModel):
    """A PartCategoryParameterTemplate creates a unique relationship between a PartCategory and a ParameterTemplate.

    Multiple ParameterTemplate instances can be associated to a PartCategory to drive a default list of parameter templates attached to a Part instance upon creation.

    Attributes:
        category: Reference to a single PartCategory object
        template: Reference to a single ParameterTemplate object
        default_value: The default value for the parameter in the context of the selected category
    """

    @staticmethod
    def get_api_url():
        """Return the API endpoint URL associated with the PartCategoryParameterTemplate model."""
        return reverse('api-part-category-parameter-list')

    class Meta:
        """Metaclass providing extra model definition."""

        verbose_name = _('Part Category Parameter Template')

        constraints = [
            UniqueConstraint(
                fields=['category', 'template'], name='unique_category_parameter_pair'
            )
        ]

    def __str__(self):
        """String representation of a PartCategoryParameterTemplate (admin interface)."""
        if self.default_value:
            return f'{self.category.name} | {self.template.name} | {self.default_value}'
        return f'{self.category.name} | {self.template.name}'

    def clean(self):
        """Validate this PartCategoryParameterTemplate instance.

        Checks the provided 'default_value', and (if not blank), ensure it is valid.
        """
        super().clean()

        self.default_value = (
            '' if self.default_value is None else str(self.default_value.strip())
        )

        if (
            self.default_value
            and get_global_setting(
                'PARAMETER_ENFORCE_UNITS', True, cache=False, create=False
            )
            and self.template.units
        ):
            try:
                InvenTree.conversion.convert_physical_value(
                    self.default_value, self.template.units
                )
            except ValidationError as e:
                raise ValidationError({'default_value': e.message})

    category = models.ForeignKey(
        PartCategory,
        on_delete=models.CASCADE,
        related_name='parameter_templates',
        verbose_name=_('Category'),
        help_text=_('Part Category'),
    )

    template = models.ForeignKey(
        common.models.ParameterTemplate,
        on_delete=models.CASCADE,
        related_name='part_categories',
    )

    default_value = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Default Value'),
        help_text=_('Default Parameter Value'),
    )


class PartReportContext(report.mixins.BaseReportContext):
    """Report context for the Part model.

    Attributes:
        bom_items: Query set of all BomItem objects associated with the Part
        category: The PartCategory object associated with the Part
        description: The description field of the Part
        IPN: The IPN (internal part number) of the Part
        name: The name of the Part
        parameters: Dict object containing the parameters associated with the Part
        part: The Part object itself
        qr_data: Formatted QR code data for the Part
        qr_url: Generated URL for embedding in a QR code
        revision: The revision of the Part
        test_template_list: List of test templates associated with the Part
        test_templates: Dict object of test templates associated with the Part
    """

    bom_items: report.mixins.QuerySet[BomItem]
    category: PartCategory | None
    description: str
    IPN: str | None
    name: str
    parameters: dict[str, str]
    part: Part
    qr_data: str
    qr_url: str
    revision: str | None
    test_template_list: report.mixins.QuerySet[PartTestTemplate]
    test_templates: dict[str, PartTestTemplate]


@cleanup.ignore
class Part(
    InvenTree.models.PluginValidationMixin,
    InvenTree.models.InvenTreeParameterMixin,
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    InvenTree.models.InvenTreeNotesMixin,
    report.mixins.InvenTreeReportMixin,
    InvenTree.models.InvenTreeImageMixin,
    InvenTree.models.MetadataMixin,
    InvenTree.models.InvenTreeTree,
):
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
        testable: Testable parts can have test results recorded against their stock items
        active: Is this part active? Parts are deactivated instead of being deleted
        locked: This part is locked and cannot be edited
        virtual: Is this part "virtual"? e.g. a software product or similar
        notes: Additional notes field for this part
        creation_date: Date that this part was added to the database
        creation_user: User who added this part to the database
        responsible_owner: Owner (either user or group) which is responsible for this part (optional)

    BOM (Bill of Materials) related attributes:
        bom_checksum: Checksum for the BOM of this part
        bom_validated: Boolean field indicating if the BOM is valid (checksum matches)
        bom_checked_by: User who last checked the BOM for this part
        bom_checked_date: Date when the BOM was last checked
    """

    NODE_PARENT_KEY = 'variant_of'
    IMAGE_RENAME = rename_part_image

    objects = TreeManager()

    tags = TaggableManager(blank=True)

    class Meta:
        """Metaclass defines extra model properties."""

        verbose_name = _('Part')
        verbose_name_plural = _('Parts')
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name', 'IPN', 'revision'], name='unique_part')
        ]

    class MPTTMeta:
        """MPTT Metaclass options."""

        # For legacy reasons the 'variant_of' field is used to indicate the MPTT parent
        parent_attr = 'variant_of'

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the Part model."""
        return reverse('api-part-list')

    def api_instance_filters(self):
        """Return API query filters for limiting field results against this instance."""
        return {'variant_of': {'exclude_tree': self.pk}}

    @classmethod
    def barcode_model_type_code(cls):
        """Return the associated barcode model type code for this model."""
        return 'PA'

    def report_context(self) -> PartReportContext:
        """Return custom report context information."""
        return {
            'bom_items': cast(report.mixins.QuerySet['BomItem'], self.get_bom_items()),
            'category': self.category,
            'description': self.description,
            'IPN': self.IPN,
            'name': self.name,
            'parameters': self.parameters_map(),
            'part': self,
            'qr_data': self.barcode,
            'qr_url': self.get_absolute_url(),
            'revision': self.revision,
            'test_template_list': self.getTestTemplates(),
            'test_templates': self.getTestTemplateMap(),
        }

    def check_parameter_delete(self, parameter):
        """Custom delete check for Paramteter instances associated with this Part."""
        if self.locked:
            raise ValidationError(_('Cannot delete parameters of a locked part'))

    def check_parameter_save(self, parameter):
        """Custom save check for Parameter instances associated with this Part."""
        if self.locked:
            raise ValidationError(_('Cannot modify parameters of a locked part'))

    def delete(self, **kwargs):
        """Custom delete method for the Part model.

        Prevents deletion of a Part if any of the following conditions are met:

        - The part is still active
        - The part is used in a BOM for a different part.
        """
        if self.locked:
            raise ValidationError(_('Cannot delete this part as it is locked'))

        if self.active:
            raise ValidationError(_('Cannot delete this part as it is still active'))

        if not get_global_setting('PART_ALLOW_DELETE_FROM_ASSEMBLY', cache=False):
            if BomItem.objects.filter(sub_part=self).exists():
                raise ValidationError(
                    _('Cannot delete this part as it is used in an assembly')
                )

        super().delete()

    def save(self, *args, **kwargs):
        """Overrides the save function for the Part model.

        If the part image has been updated, then check if the "old" (previous) image is still used by another part.
        If not, it is considered "orphaned" and will be deleted.
        """
        _new = False
        if self.pk:
            try:
                previous = Part.objects.get(pk=self.pk)

                # Image has been changed
                if previous.image is not None and self.image != previous.image:
                    # Are there any (other) parts which reference the image?
                    n_refs = (
                        Part.objects.filter(image=previous.image)
                        .exclude(pk=self.pk)
                        .count()
                    )

                    if n_refs == 0:
                        logger.info("Deleting unused image file '%s'", previous.image)
                        previous.image.delete(save=False)
            except Part.DoesNotExist:
                pass
        else:
            _new = True

        self.full_clean()

        super().save(*args, **kwargs)

        if _new:
            # Only run if the check was not run previously (due to not existing in the database)
            self.ensure_trackable()

    def __str__(self):
        """Return a string representation of the Part (for use in the admin interface)."""
        return f'{self.full_name} - {self.description}'

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
        b) The parent part exists in the same variant tree as this one
        c) The parent part is used in the BOM for *this* part
        d) The parent part is used in the BOM for any child parts under this one
        """
        result = True

        try:
            if self.pk == parent.pk:
                raise ValidationError({
                    'sub_part': _(
                        f"Part '{self}' cannot be used in BOM for '{parent}' (recursive)"
                    )
                })

            if self.tree_id == parent.tree_id:
                raise ValidationError({
                    'sub_part': _(
                        f"Part '{self}' cannot be used in BOM for '{parent}' (recursive)"
                    )
                })

            bom_items = self.get_bom_items()

            # Ensure that the parent part does not appear under any child BOM item!
            for item in bom_items.all():
                # Check for simple match
                if item.sub_part == parent:
                    raise ValidationError({
                        'sub_part': _(
                            f"Part '{parent}' is  used in BOM for '{self}' (recursive)"
                        )
                    })

                # And recursively check too
                if recursive:
                    result = result and item.sub_part.check_add_to_bom(
                        parent, recursive=True, raise_error=raise_error
                    )

        except ValidationError as e:
            if raise_error:
                raise e
            else:
                return False

        return result

    def validate_name(self, raise_error=True):
        """Validate the name field for this Part instance.

        This function is exposed to any Validation plugins, and thus can be customized.
        """
        from plugin import PluginMixinEnum, registry

        for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
            # Run the name through each custom validator
            # If the plugin returns 'True' we will skip any subsequent validation

            try:
                result = plugin.validate_part_name(self.name, self)
                if result:
                    return
            except ValidationError as exc:
                if raise_error:
                    raise ValidationError({'name': exc.message})
            except Exception:
                log_error('validate_part_name', plugin=plugin.slug)

    def validate_ipn(self, raise_error=True):
        """Ensure that the IPN (internal part number) is valid for this Part".

        - Validation is handled by custom plugins
        - By default, no validation checks are performed
        """
        from plugin import PluginMixinEnum, registry

        for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
            try:
                result = plugin.validate_part_ipn(self.IPN, self)

                if result:
                    # A "true" result force skips any subsequent checks
                    break
            except ValidationError as exc:
                if raise_error:
                    raise ValidationError({'IPN': exc.message})
            except Exception:
                log_error('validate_part_ipn', plugin=plugin.slug)

        # If we get to here, none of the plugins have raised an error
        pattern = get_global_setting('PART_IPN_REGEX', '', create=False).strip()

        if pattern:
            match = re.search(pattern, self.IPN)

            if match is None:
                raise ValidationError(_(f'IPN must match regex pattern {pattern}'))

    def validate_revision(self):
        """Check the 'revision' and 'revision_of' fields."""
        # Part cannot be a revision of itself
        if self.revision_of:
            if self.revision_of == self:
                raise ValidationError({
                    'revision_of': _('Part cannot be a revision of itself')
                })

            # Part cannot be a revision of a part which is itself a revision
            if self.revision_of.revision_of:
                raise ValidationError({
                    'revision_of': _(
                        'Cannot make a revision of a part which is already a revision'
                    )
                })

            # If this part is a revision, it must have a revision code
            if not self.revision:
                raise ValidationError({
                    'revision': _('Revision code must be specified')
                })

            if get_global_setting('PART_REVISION_ASSEMBLY_ONLY'):
                if not self.assembly or not self.revision_of.assembly:
                    raise ValidationError({
                        'revision_of': _(
                            'Revisions are only allowed for assembly parts'
                        )
                    })

            # Cannot have a revision of a "template" part
            if self.revision_of.is_template:
                raise ValidationError({
                    'revision_of': _('Cannot make a revision of a template part')
                })

            # parent part must point to the same template (via variant_of)
            if self.variant_of != self.revision_of.variant_of:
                raise ValidationError({
                    'revision_of': _('Parent part must point to the same template')
                })

    def validate_serial_number(
        self,
        serial: str,
        stock_item=None,
        check_duplicates=True,
        raise_error=False,
        **kwargs,
    ):
        """Validate a serial number against this Part instance.

        Note: This function is exposed to any Validation plugins, and thus can be customized.

        Any plugins which implement the 'validate_serial_number' method have three possible outcomes:

        - Decide the serial is objectionable and raise a django.core.exceptions.ValidationError
        - Decide the serial is acceptable, and return None to proceed to other tests
        - Decide the serial is acceptable, and return True to skip any further tests

        Arguments:
            serial: The proposed serial number
            stock_item: (optional) A StockItem instance which has this serial number assigned (e.g. testing for duplicates)
            check_duplicates: If True, checks for duplicate serial numbers in the database.
            raise_error: If False, and ValidationError(s) will be handled

        Returns:
            True if serial number is 'valid' else False

        Raises:
            ValidationError if serial number is invalid and raise_error = True
        """
        serial = str(serial).strip()

        # First, throw the serial number against each of the loaded validation plugins
        from plugin import PluginMixinEnum, registry

        for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
            # Run the serial number through each custom validator
            # If the plugin returns 'True' we will skip any subsequent validation

            try:
                result = False

                if hasattr(plugin, 'validate_serial_number'):
                    signature = inspect.signature(plugin.validate_serial_number)

                    if 'stock_item' in signature.parameters:
                        # 2024-08-21: New method signature accepts a 'stock_item' parameter
                        result = plugin.validate_serial_number(
                            serial, self, stock_item=stock_item
                        )
                    else:
                        # Old method signature - does not accept a 'stock_item' parameter
                        result = plugin.validate_serial_number(serial, self)

                if result is True:
                    return True
            except ValidationError as exc:
                if raise_error:
                    # Re-throw the error
                    raise exc
                else:
                    return False
            except Exception:
                log_error('validate_serial_number', plugin=plugin.slug)

        """
        If we are here, none of the loaded plugins (if any) threw an error or exited early

        Now, we run the "default" serial number validation routine,
        which checks that the serial number is not duplicated
        """

        if not check_duplicates:
            return

        # from part.models import Part
        from stock.models import StockItem

        if get_global_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', False):
            # Serial number must be unique across *all* parts
            parts = Part.objects.all()
        else:
            # Serial number must only be unique across this part "tree"
            parts = Part.objects.filter(tree_id=self.tree_id)

        stock = StockItem.objects.filter(part__in=parts, serial=serial)

        if stock_item:
            # Exclude existing StockItem from query
            stock = stock.exclude(pk=stock_item.pk)

        if stock.exists():
            if raise_error:
                raise ValidationError(
                    _('Stock item with this serial number already exists')
                    + ': '
                    + serial
                )
            else:
                return False
        else:
            # This serial number is perfectly valid
            return True

    def find_conflicting_serial_numbers(self, serials: list) -> list:
        """For a provided list of serials, return a list of those which are conflicting."""
        # from part.models import Part
        from stock.models import StockItem

        conflicts = []

        # First, check for raw conflicts based on efficient database queries
        if get_global_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', False):
            # Serial number must be unique across *all* parts
            parts = Part.objects.all()
        else:
            # Serial number must only be unique across this part "tree"
            parts = Part.objects.filter(tree_id=self.tree_id)

        items = StockItem.objects.filter(part__in=parts, serial__in=serials)
        items = items.order_by('serial_int', 'serial')

        for item in items:
            conflicts.append(item.serial)

        for serial in serials:
            if serial in conflicts:
                # Already found a conflict, no need to check further
                continue

            try:
                self.validate_serial_number(
                    serial, raise_error=True, check_duplicates=False
                )
            except ValidationError:
                # Serial number is invalid (as determined by plugin)
                conflicts.append(serial)

        return conflicts

    def get_latest_serial_number(self, allow_plugins=True):
        """Find the 'latest' serial number for this Part.

        Here we attempt to find the "highest" serial number which exists for this Part.
        There are a number of edge cases where this method can fail,
        but this is accepted to keep database performance at a reasonable level.

        Note: Serial numbers must be unique across an entire Part "tree",
        so we filter by the entire tree.

        Returns:
            The latest serial number specified for this part, or None
        """
        from plugin import PluginMixinEnum, registry

        if allow_plugins:
            # Check with plugin system
            # If any plugin returns a non-null result, that takes priority
            for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
                try:
                    result = plugin.get_latest_serial_number(self)
                    if result is not None:
                        return str(result)
                except Exception:
                    log_error('get_latest_serial_number', plugin=plugin.slug)

        # No plugin returned a result, so we will run the default query
        stock = (
            StockModels.StockItem.objects.all().exclude(serial=None).exclude(serial='')
        )

        # Generate a query for any stock items for this part variant tree with non-empty serial numbers
        if not get_global_setting('SERIAL_NUMBER_GLOBALLY_UNIQUE', False):
            # Serial numbers are unique across part trees
            stock = stock.filter(part__tree_id=self.tree_id)

        # There are no matching StockItem objects (skip further tests)
        if not stock.exists():
            return None

        # Sort in descending order
        stock = stock.order_by('-serial_int', '-serial', '-pk')

        # Return the first serial value
        return stock[0].serial

    def get_next_serial_number(self):
        """Return the 'next' serial number in sequence."""
        sn = self.get_latest_serial_number()

        return InvenTree.helpers.increment_serial_number(sn, self)

    @property
    def full_name(self) -> str:
        """Format a 'full name' for this Part based on the format PART_NAME_FORMAT defined in InvenTree settings."""
        return part_helpers.render_part_full_name(self)

    def get_absolute_url(self):
        """Return the web URL for viewing this part."""
        return helpers.pui_url(f'/part/{self.id}')

    def validate_unique(self, exclude=None):
        """Validate that this Part instance is 'unique'.

        Uniqueness is checked across the following (case insensitive) fields:
        - Name
        - IPN
        - Revision

        e.g. there can exist multiple parts with the same name, but only if
        they have a different revision or internal part number.
        """
        super().validate_unique(exclude)

        # User can decide whether duplicate IPN (Internal Part Number) values are allowed
        allow_duplicate_ipn = get_global_setting('PART_ALLOW_DUPLICATE_IPN')

        # Raise an error if an IPN is set, and it is a duplicate
        if self.IPN and not allow_duplicate_ipn:
            parts = Part.objects.filter(IPN__iexact=self.IPN)
            parts = parts.exclude(pk=self.pk)

            if parts.exists():
                raise ValidationError({
                    'IPN': _('Duplicate IPN not allowed in part settings')
                })

        if (
            self.revision_of
            and self.revision
            and (
                Part.objects.exclude(pk=self.pk)
                .filter(revision_of=self.revision_of, revision=self.revision)
                .exists()
            )
        ):
            raise ValidationError(_('Duplicate part revision already exists.'))

        # Ensure unique across (Name, revision, IPN) (as specified)
        if (self.revision or self.IPN) and (
            Part.objects.exclude(pk=self.pk)
            .filter(name=self.name, revision=self.revision, IPN=self.IPN)
            .exists()
        ):
            raise ValidationError(
                _('Part with this Name, IPN and Revision already exists.')
            )

    def clean(self):
        """Perform cleaning operations for the Part model.

        - Check if the PartCategory is not structural

        - Update trackable status:
            If this part is trackable, and it is used in the BOM
            for a parent part which is *not* trackable,
            then we will force the parent part to be trackable.
        """
        if self.category is not None and self.category.structural:
            raise ValidationError({
                'category': _('Parts cannot be assigned to structural part categories!')
            })

        # Check the 'revision' and 'revision_of' fields
        self.validate_revision()

        super().clean()

        # Strip IPN field
        if type(self.IPN) is str:
            self.IPN = self.IPN.strip()

        # Run custom validation for the IPN field
        self.validate_ipn()

        # Run custom validation for the name field
        self.validate_name()

        if self.pk:
            # Only run if the part already exists in the database
            self.ensure_trackable()

    def ensure_trackable(self):
        """Ensure that trackable is set correctly downstream."""
        if self.trackable:
            for part in self.get_used_in():
                if not part.trackable:
                    part.trackable = True
                    part.clean()
                    part.save()

    name = models.CharField(
        max_length=100, blank=False, help_text=_('Part name'), verbose_name=_('Name')
    )

    is_template = models.BooleanField(
        default=part_settings.part_template_default,
        verbose_name=_('Is Template'),
        help_text=_('Is this part a template part?'),
    )

    variant_of = models.ForeignKey(
        'part.Part',
        related_name='variants',
        null=True,
        blank=True,
        limit_choices_to={'is_template': True},
        on_delete=models.SET_NULL,
        help_text=_('Is this part a variant of another part?'),
        verbose_name=_('Variant Of'),
    )

    description = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Part description (optional)'),
    )

    keywords = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name=_('Keywords'),
        help_text=_('Part keywords to improve visibility in search results'),
    )

    category = TreeForeignKey(
        PartCategory,
        related_name='parts',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_('Category'),
        help_text=_('Part category'),
    )

    IPN = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('IPN'),
        help_text=_('Internal Part Number'),
    )

    revision = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Part revision or version number'),
        verbose_name=_('Revision'),
    )

    revision_of = models.ForeignKey(
        'part.Part',
        related_name='revisions',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_('Is this part a revision of another part?'),
        verbose_name=_('Revision Of'),
    )

    link = InvenTreeURLField(
        blank=True,
        null=True,
        verbose_name=_('Link'),
        help_text=_('Link to external URL'),
        max_length=2000,
    )

    default_location = TreeForeignKey(
        'stock.StockLocation',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
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
        blank=True,
        null=True,
        verbose_name=_('Default Supplier'),
        help_text=_('Default supplier part'),
        related_name='default_parts',
    )

    default_expiry = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Default Expiry'),
        help_text=_('Expiry time (in days) for stock items of this part'),
    )

    minimum_stock = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Minimum Stock'),
        help_text=_('Minimum allowed stock level'),
    )

    units = models.CharField(
        max_length=20,
        default='',
        blank=True,
        null=True,
        verbose_name=_('Units'),
        help_text=_('Units of measure for this part'),
        validators=[validators.validate_physical_units],
    )

    assembly = models.BooleanField(
        default=part_settings.part_assembly_default,
        verbose_name=_('Assembly'),
        help_text=_('Can this part be built from other parts?'),
    )

    component = models.BooleanField(
        default=part_settings.part_component_default,
        verbose_name=_('Component'),
        help_text=_('Can this part be used to build other parts?'),
    )

    trackable = models.BooleanField(
        default=part_settings.part_trackable_default,
        verbose_name=_('Trackable'),
        help_text=_('Does this part have tracking for unique items?'),
    )

    testable = models.BooleanField(
        default=False,
        verbose_name=_('Testable'),
        help_text=_('Can this part have test results recorded against it?'),
    )

    purchaseable = models.BooleanField(
        default=part_settings.part_purchaseable_default,
        verbose_name=_('Purchaseable'),
        help_text=_('Can this part be purchased from external suppliers?'),
    )

    salable = models.BooleanField(
        default=part_settings.part_salable_default,
        verbose_name=_('Salable'),
        help_text=_('Can this part be sold to customers?'),
    )

    active = models.BooleanField(
        default=True, verbose_name=_('Active'), help_text=_('Is this part active?')
    )

    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Locked parts cannot be edited'),
    )

    virtual = models.BooleanField(
        default=part_settings.part_virtual_default,
        verbose_name=_('Virtual'),
        help_text=_('Is this a virtual part, such as a software product or license?'),
    )

    bom_validated = models.BooleanField(
        default=False,
        verbose_name=_('BOM Validated'),
        help_text=_('Is the BOM for this part valid?'),
    )

    bom_checksum = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_('BOM checksum'),
        help_text=_('Stored BOM checksum'),
    )

    bom_checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('BOM checked by'),
        related_name='boms_checked',
    )

    bom_checked_date = models.DateField(
        blank=True, null=True, verbose_name=_('BOM checked date')
    )

    creation_date = models.DateField(
        auto_now_add=True,
        editable=False,
        blank=True,
        null=True,
        verbose_name=_('Creation Date'),
    )

    creation_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Creation User'),
        related_name='parts_created',
    )

    responsible_owner = models.ForeignKey(
        users.models.Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Responsible'),
        help_text=_('Owner responsible for this part'),
        related_name='parts_responsible',
    )

    @property
    def category_path(self):
        """Return the category path of this Part instance."""
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

    def requiring_build_orders(self, include_variants: bool = True):
        """Return list of outstanding build orders which require this part.

        Arguments:
            include_variants: If True, include variants of this part in the calculation
        """
        # List parts that this part is required for

        if include_variants:
            # If we are including variants, get all parts in the variant tree
            parts = list(self.get_descendants(include_self=True))
        else:
            parts = [self]

        used_in_parts = set()

        for part in parts:
            # Get all assemblies which use this part
            used_in_parts.update(part.get_used_in())

        # Now, get a list of outstanding build orders which require this part
        builds = BuildModels.Build.objects.filter(
            part__in=list(used_in_parts), status__in=BuildStatusGroups.ACTIVE_CODES
        )

        return builds

    def required_build_order_quantity(self, include_variants: bool = True):
        """Return the quantity of this part required for active build orders.

        Arguments:
            include_variants: If True, include variants of this part in the calculation
        """
        # List active build orders which reference this part
        builds = self.requiring_build_orders(include_variants=include_variants)

        quantity = 0

        if include_variants:
            matching_parts = list(self.get_descendants(include_self=True))
        else:
            matching_parts = [self]

        # Cache the BOM items that we query
        # Keep a dict of part ID to BOM items
        cached_bom_items: dict = {}

        for build in builds:
            if build.part.pk not in cached_bom_items:
                # Get the BOM items for this part
                bom_items = build.part.get_bom_items().filter(
                    sub_part__in=matching_parts
                )
                cached_bom_items[build.part.pk] = bom_items
            else:
                bom_items = cached_bom_items[build.part.pk]

            # Match BOM item to build
            for bom_item in bom_items:
                build_line = build.build_lines.filter(bom_item=bom_item).first()

                if not build_line:
                    continue

                line_quantity = max(0, build_line.quantity - build_line.consumed)
                quantity += line_quantity

        return quantity

    def requiring_sales_orders(self, include_variants: bool = True):
        """Return a list of sales orders which require this part.

        Arguments:
            include_variants: If True, include variants of this part in the calculation
        """
        orders = set()

        if include_variants:
            parts = list(self.get_descendants(include_self=True))
        else:
            parts = [self]

        # Get a list of line items for open orders which match this part
        open_lines = OrderModels.SalesOrderLineItem.objects.filter(
            order__status__in=SalesOrderStatusGroups.OPEN, part__in=parts
        )

        for line in open_lines:
            orders.add(line.order)

        return orders

    def required_sales_order_quantity(self, include_variants: bool = True):
        """Return the quantity of this part required for active sales orders.

        Arguments:
            include_variants: If True, include variants of this part in the calculation
        """
        if include_variants:
            parts = list(self.get_descendants(include_self=True))
        else:
            parts = [self]

        # Get a list of line items for open orders which match this part
        open_lines = OrderModels.SalesOrderLineItem.objects.filter(
            order__status__in=SalesOrderStatusGroups.OPEN, part__in=parts
        )

        quantity = 0

        for line in open_lines:
            # Determine the quantity "remaining" to be shipped out

            if not line:
                continue

            remaining = max(line.quantity - line.shipped, 0)
            quantity += remaining

        return quantity

    def required_order_quantity(self, include_variants: bool = True):
        """Return total required to fulfil orders."""
        return self.required_build_order_quantity(
            include_variants=include_variants
        ) + self.required_sales_order_quantity(include_variants=include_variants)

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

    def get_subscribers(
        self, include_variants: bool = True, include_categories: bool = True
    ) -> list[User]:
        """Return a list of users who are 'subscribed' to this part.

        Arguments:
            include_variants: If True, include users who are subscribed to a variant part
            include_categories: If True, include users who are subscribed to the category

        Returns:
            list[User]: A list of users who are subscribed to this part

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
            queryset = queryset.filter(part__in=self.get_ancestors(include_self=True))
        else:
            queryset = queryset.filter(part=self)

        for star in queryset:
            subscribers.add(star.user)

        if include_categories and self.category:
            for sub in self.category.get_subscribers():
                subscribers.add(sub)

        return list(subscribers)

    def is_starred_by(self, user, **kwargs):
        """Return True if the specified user subscribes to this part."""
        return user in self.get_subscribers(**kwargs)

    def set_starred(self, user, status, **kwargs):
        """Set the "subscription" status of this Part against the specified user."""
        if not user:
            return

        # Already subscribed?
        if self.is_starred_by(user, **kwargs) == status:
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
        import part.filters

        # If this part does NOT have a BOM, result is simply the currently available stock
        if not self.has_bom:
            return 0

        # Prefetch related tables, to reduce query expense
        queryset = self.get_bom_items()

        # Ignore 'consumable' BOM items for this calculation
        queryset = queryset.filter(consumable=False)

        # Annotate the queryset with the 'can_build' quantity
        queryset = part.filters.annotate_bom_item_can_build(queryset)

        can_build_quantity = None

        for value in queryset.values_list('can_build', flat=True):
            if can_build_quantity is None:
                can_build_quantity = value
            else:
                can_build_quantity = min(can_build_quantity, value)

        if can_build_quantity is None:
            # No BOM items, or no items which can be built
            return 0

        return int(max(can_build_quantity, 0))

    @property
    def active_builds(self):
        """Return a list of outstanding builds.

        Builds marked as 'complete' or 'cancelled' are ignored
        """
        return self.builds.filter(status__in=BuildStatusGroups.ACTIVE_CODES)

    @property
    def quantity_being_built(self, include_variants: bool = True):
        """Return the current number of parts currently being built.

        Arguments:
            include_variants: If True, include variants of this part in the calculation

        Note: This is the total quantity of Build orders, *not* the number of build outputs.
              In this fashion, it is the "projected" quantity of builds
        """
        builds = BuildModels.Build.objects.filter(
            status__in=BuildStatusGroups.ACTIVE_CODES
        )

        if include_variants:
            # If we are including variants, get all parts in the variant tree
            builds = builds.filter(part__in=self.get_descendants(include_self=True))
        else:
            # Only look at this part
            builds = builds.filter(part=self)

        quantity = 0

        for build in builds:
            # The remaining items in the build
            quantity += build.remaining

        return quantity

    @property
    def quantity_in_production(self, include_variants: bool = True):
        """Quantity of this part currently actively in production.

        Arguments:
            include_variants: If True, include variants of this part in the calculation

        Note: This may return a different value to `quantity_being_built`
        """
        quantity = 0

        items = StockModels.StockItem.objects.filter(
            is_building=True, build__status__in=BuildStatusGroups.ACTIVE_CODES
        )

        if include_variants:
            # If we are including variants, get all parts in the variant tree
            items = items.filter(part__in=self.get_descendants(include_self=True))
        else:
            # Only look at this part
            items = items.filter(part=self)

        for item in items:
            # The remaining items in the build
            quantity += item.quantity

        return quantity

    def build_order_allocations(self, **kwargs):
        """Return all 'BuildItem' objects which allocate this part to Build objects."""
        include_variants = kwargs.get('include_variants', True)

        queryset = BuildModels.BuildItem.objects.all()

        if include_variants:
            variants = self.get_descendants(include_self=True)
            queryset = queryset.filter(stock_item__part__in=variants)
        else:
            queryset = queryset.filter(stock_item__part=self)

        return queryset

    def build_order_allocation_count(self, **kwargs):
        """Return the total amount of this part allocated to build orders."""
        query = self.build_order_allocations(**kwargs).aggregate(
            total=Coalesce(
                Sum('quantity', output_field=models.DecimalField()),
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
            queryset = queryset.filter(item__part__in=variants)
        else:
            # Only look at this part
            queryset = queryset.filter(item__part=self)

        # Default behaviour is to only return *pending* allocations
        pending = kwargs.get('pending', True)

        if pending is True:
            # Look only for 'open' orders which have not shipped
            queryset = queryset.filter(
                line__order__status__in=SalesOrderStatusGroups.OPEN,
                shipment__shipment_date=None,
            )
        elif pending is False:
            # Look only for 'closed' orders or orders which have shipped
            queryset = queryset.exclude(
                line__order__status__in=SalesOrderStatusGroups.OPEN,
                shipment__shipment_date=None,
            )

        return queryset

    def sales_order_allocation_count(self, **kwargs):
        """Return the total quantity of this part allocated to sales orders."""
        query = self.sales_order_allocations(**kwargs).aggregate(
            total=Coalesce(
                Sum('quantity', output_field=models.DecimalField()),
                0,
                output_field=models.DecimalField(),
            )
        )

        return query['total']

    def allocation_count(self, **kwargs):
        """Return the total quantity of stock allocated for this part, against both build orders and sales orders."""
        if self.id is None:
            # If this instance has not been saved, foreign-key lookups will fail
            return 0

        return sum([
            self.build_order_allocation_count(**kwargs),
            self.sales_order_allocation_count(**kwargs),
        ])

    def stock_entries(
        self, include_variants=True, include_external=True, in_stock=None, location=None
    ):
        """Return all stock entries for this Part.

        Arguments:
            include_variants: If True, include stock entries for all part variants
            include_external: If True, include stock entries which are in 'external' locations
            in_stock: If True, filter by stock entries which are 'in stock'
            location: If set, filter by stock entries in the specified location
        """
        if include_variants:
            query = StockModels.StockItem.objects.filter(
                part__in=self.get_descendants(include_self=True)
            )
        else:
            query = self.stock_items

        if in_stock is True:
            query = query.filter(StockModels.StockItem.IN_STOCK_FILTER)
        elif in_stock is False:
            query = query.exclude(StockModels.StockItem.IN_STOCK_FILTER)

        if include_external is False:
            # Exclude stock entries which are not 'internal'
            query = query.filter(external=False)

        if location:
            locations = location.get_descendants(include_self=True)
            query = query.filter(location__in=locations)

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

    def get_bom_item_filter(
        self, include_inherited: bool = True, include_virtual: bool = True
    ):
        """Returns a query filter for all BOM items associated with this Part.

        Arguments:
            include_inherited: If True, include BomItem entries defined for parent parts
            include_virtual: If True, include BomItem entries which are virtual

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
            if parents.exists():
                parent_filter = Q(part__in=parents, inherited=True)

                # OR the filters together
                bom_filter |= parent_filter

        if not include_virtual:
            bom_filter &= Q(sub_part__virtual=False)

        return bom_filter

    def get_bom_items(
        self, include_inherited: bool = True, include_virtual: bool = True
    ) -> QuerySet[BomItem]:
        """Return a queryset containing all BOM items for this part.

        Arguments:
            include_inherited (bool): If set, include BomItem entries defined for parent parts
            include_virtual (bool): If set, include BomItem entries which are virtual parts
        """
        queryset = BomItem.objects.filter(
            self.get_bom_item_filter(
                include_inherited=include_inherited, include_virtual=include_virtual
            )
        )

        return queryset.prefetch_related('part', 'sub_part')

    def get_installed_part_options(
        self, include_inherited: bool = True, include_variants: bool = True
    ):
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

    def get_used_in_bom_item_filter(
        self, include_variants=True, include_substitutes=True
    ):
        """Return a BomItem queryset which returns all BomItem instances which refer to *this* part.

        As the BOM allocation logic is somewhat complicated, there are some considerations:

        A) This part may be directly specified in a BomItem instance
        B) This part may be a *variant* of a part which is directly specified in a BomItem instance
        C) This part may be a *substitute* for a part which is directly specified in a BomItem instance

        So we construct a query for each case, and combine them...
        """
        # Cache all *parent* parts
        try:
            parents = self.get_ancestors(include_self=False)
        except ValueError:
            # If get_ancestors() fails, then this part is not saved yet
            parents = []

        # Case A: This part is directly specified in a BomItem (we always use this case)
        query = Q(sub_part=self)

        if include_variants:
            # Case B: This part is a *variant* of a part which is specified in a BomItem which allows variants
            query |= Q(allow_variants=True, sub_part__in=parents)

        # Case C: This part is a *substitute* of a part which is directly specified in a BomItem
        if include_substitutes:
            # Grab a list of BomItem substitutes which reference this part
            substitutes = self.substitute_items.all()

            query |= Q(pk__in=[substitute.bom_item.pk for substitute in substitutes])

        return query

    def get_used_in(self, include_inherited=True, include_substitutes=True):
        """Return a list containing all parts this part is used in.

        Includes consideration of inherited BOMs
        """
        # Grab a queryset of all BomItem objects which "require" this part
        bom_items = BomItem.objects.filter(
            self.get_used_in_bom_item_filter(include_substitutes=include_substitutes)
        )

        # Iterate through the returned items and construct a set of
        parts = set()

        for bom_item in bom_items:
            if bom_item.part in parts:
                continue

            parts.add(bom_item.part)

            # Include inherited BOMs?
            if include_inherited and bom_item.inherited:
                try:
                    descendants = bom_item.part.get_descendants(include_self=False)
                except ValueError:
                    # This part is not saved yet
                    descendants = []

                for variant in descendants:
                    parts.add(variant)

        return list(parts)

    @property
    def has_bom(self):
        """Return True if this Part instance has any BOM items."""
        return self.get_bom_items().exists()

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
        return self.get_trackable_parts().exists()

    @property
    def bom_count(self):
        """Return the number of items contained in the BOM for this part."""
        return self.get_bom_items().count()

    @property
    def used_in_count(self):
        """Return the number of part BOMs that this part appears in."""
        return len(self.get_used_in())

    def get_bom_hash(self):
        """Return a checksum hash for the BOM for this part.

        Used to determine if the BOM has changed (and needs to be signed off!)
        The hash is calculated by hashing each line item in the BOM. Returns a string representation of a hash object which can be compared with a stored value
        """
        result_hash = hashlib.md5(str(self.id).encode())

        # List *all* BOM items (including inherited ones!)
        bom_items = self.get_bom_items().all().prefetch_related('part', 'sub_part')

        for item in bom_items:
            result_hash.update(str(item.get_item_hash()).encode())

        return str(result_hash.digest())

    def is_bom_valid(self) -> bool:
        """Check if the BOM is 'valid'.

        To be "valid", the part must:
        - Have a stored "bom_checksum" value
        - The stored "bom_checksum" must match the calculated checksum.

        Returns:
            bool: True if the BOM is valid, False otherwise
        """
        if not self.bom_checksum or not self.bom_checked_date:
            # If there is no BOM checksum, then the BOM is not valid
            return False

        return self.get_bom_hash() == self.bom_checksum

    @transaction.atomic
    def validate_bom(self, user, valid: bool = True):
        """Validate the BOM (mark the BOM as validated by the given User.

        Arguments:
            user: User who is validating the BOM
            valid: If True, mark the BOM as valid (default=True)

        - Calculates and stores the hash for the BOM
        - Saves the current date and the checking user
        """
        # Validate each line item, ignoring inherited ones
        bom_items = self.get_bom_items(include_inherited=False).prefetch_related(
            'part', 'sub_part'
        )

        for item in bom_items:
            item.validate_hash(valid=valid)

        self.bom_validated = valid
        self.bom_checksum = self.get_bom_hash() if valid else ''
        self.bom_checked_by = user
        self.bom_checked_date = InvenTree.helpers.current_date()

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

        bom_items = self.get_bom_items()

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

    def update_pricing(self):
        """Recalculate cached pricing for this Part instance."""
        self.pricing.update_pricing()

    @property
    def pricing(self):
        """Return the PartPricing information for this Part instance.

        If there is no PartPricing database entry defined for this Part,
        it will first be created, and then returned.
        """
        try:
            pricing = PartPricing.objects.get(part=self)
        except PartPricing.DoesNotExist:
            pricing = PartPricing(part=self)

        return pricing

    def schedule_pricing_update(
        self, create: bool = False, force: bool = False, refresh: bool = True
    ):
        """Helper function to schedule a pricing update.

        Importantly, catches any errors which may occur during deletion of related objects,
        in particular due to post_delete signals.

        Ref: https://github.com/inventree/InvenTree/pull/3986

        Arguments:
            create: Whether or not a new PartPricing object should be created if it does not already exist
            force: If True, force the pricing to be updated even auto pricing is disabled
            refresh: If True, refresh the PartPricing object from the database
        """
        if not force and not get_global_setting(
            'PRICING_AUTO_UPDATE', backup_value=True
        ):
            return

        if refresh:
            try:
                self.refresh_from_db()
            except Part.DoesNotExist:
                return

        try:
            pricing = self.pricing

            if create or pricing.pk:
                pricing.schedule_for_update(refresh=refresh)
        except IntegrityError:
            # If this part instance has been deleted,
            # some post-delete or post-save signals may still be fired
            # which can cause issues down the track
            pass

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

        return f'{min_price} - {max_price}'

    def get_supplier_price_range(self, quantity=1):
        """Return the supplier price range of this part.

        Actions:
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

        for item in self.get_bom_items().select_related('sub_part'):
            if item.sub_part.pk == self.pk:
                logger.warning('WARNING: BomItem ID %s contains itself in BOM', item.pk)
                continue

            q = decimal.Decimal(quantity)
            i = decimal.Decimal(item.quantity)

            prices = item.sub_part.get_price_range(
                q * i, internal=internal, purchase=purchase
            )

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

    def get_price_range(
        self, quantity=1, buy=True, bom=True, internal=False, purchase=False
    ):
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
        bom_price_range = (
            self.get_bom_price_range(quantity, internal=internal) if bom else None
        )

        if buy_price_range is None:
            return bom_price_range

        elif bom_price_range is None:
            return buy_price_range
        return (
            min(buy_price_range[0], bom_price_range[0]),
            max(buy_price_range[1], bom_price_range[1]),
        )

    base_cost = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('base cost'),
        help_text=_('Minimum charge (e.g. stocking fee)'),
    )

    multiple = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('multiple'),
        help_text=_('Sell multiple'),
    )

    get_price = common.currency.get_price

    @property
    def has_price_breaks(self):
        """Return True if this part has sale price breaks."""
        return self.price_breaks.exists()

    @property
    def price_breaks(self):
        """Return the associated price breaks in the correct order."""
        return self.salepricebreaks.order_by('quantity').all()

    @property
    def unit_pricing(self):
        """Returns the price of this Part at quantity=1."""
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

        PartSellPriceBreak.objects.create(part=self, quantity=quantity, price=price)

    def get_internal_price(self, quantity, moq=True, multiples=True, currency=None):
        """Return the internal price of this Part at the specified quantity."""
        return common.currency.get_price(
            self, quantity, moq, multiples, currency, break_name='internal_price_breaks'
        )

    @property
    def has_internal_price_breaks(self):
        """Return True if this Part has internal pricing information."""
        return self.internal_price_breaks.exists()

    @property
    def internal_price_breaks(self):
        """Return the associated price breaks in the correct order."""
        return self.internalpricebreaks.order_by('quantity').all()

    def get_purchase_price(self, quantity):
        """Calculate the purchase price for this part at the specified quantity.

        - Looks at available supplier pricing data
        - Calculates the price base on the closest price point
        """
        currency = currency_code_default()
        try:
            prices = [
                convert_money(item.purchase_price, currency).amount
                for item in self.stock_items.all()
                if item.purchase_price
            ]
        except MissingRate:
            prices = None

        if prices:
            return min(prices) * quantity, max(prices) * quantity

        return None

    @transaction.atomic
    def copy_bom_from(self, other, clear: bool = True, **kwargs):
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
    def copy_tests_from(self, other: Part, **kwargs) -> None:
        """Copy all test templates from another Part instance.

        Note: We only copy the direct test templates, not ones inherited from parent parts.
        """
        templates = []
        parts = self.get_ancestors(include_self=True)

        # Prevent tests from being created for non-testable parts
        if not self.testable:
            return

        for template in other.test_templates.all():
            # Skip if a test template already exists for this part / key combination
            if PartTestTemplate.objects.filter(
                key=template.key, part__in=parts
            ).exists():
                continue

            template.pk = None
            template.part = self
            templates.append(template)

        if len(templates) > 0:
            PartTestTemplate.objects.bulk_create(templates)

    @transaction.atomic
    def copy_category_parameters(self, category: PartCategory):
        """Copy parameter templates from the specified PartCategory.

        This function is normally called when the Part is first created.
        """
        from common.models import Parameter

        categories = category.get_ancestors(include_self=True)

        category_templates = PartCategoryParameterTemplate.objects.filter(
            category__in=categories
        ).order_by('-category__level')

        parameters = []
        content_type = ContentType.objects.get_for_model(Part)

        for category_template in category_templates:
            # First ensure that the part doesn't have that parameter
            if self.parameters_list.filter(
                template=category_template.template
            ).exists():
                continue

            parameters.append(
                Parameter(
                    template=category_template.template,
                    model_type=content_type,
                    model_id=self.pk,
                    data=category_template.default_value,
                )
            )

        if len(parameters) > 0:
            Parameter.objects.bulk_create(parameters)

    def getTestTemplates(
        self, required=None, include_parent: bool = True, enabled=None
    ) -> QuerySet[PartTestTemplate]:
        """Return a list of all test templates associated with this Part.

        These are used for validation of a StockItem.


        Args:
            required (bool, optional): Filter templates by whether they are required. Defaults to None.
            include_parent (bool, optional): Include templates from parent parts. Defaults to True.
            enabled (bool, optional): Filter templates by their enabled status. Defaults to None.

        Returns:
            QuerySet: A queryset of matching test templates.
        """
        if include_parent:
            tests = PartTestTemplate.objects.filter(
                part__in=self.get_ancestors(include_self=True)
            )
        else:
            tests = self.test_templates

        if required is not None:
            tests = tests.filter(required=required)

        if enabled is not None:
            tests = tests.filter(enabled=enabled)

        return tests

    def getTestTemplateMap(self, **kwargs):
        """Return a map of all test templates associated with this Part."""
        templates = {}

        for template in self.getTestTemplates(**kwargs):
            templates[template.key] = template

        return templates

    def getRequiredTests(self, include_parent=True, enabled=True):
        """Return the tests which are required by this part.

        Arguments:
            include_parent: If True, include tests which are defined for parent parts
            enabled: If set (either True or False), filter by template "enabled" status
        """
        return self.getTestTemplates(
            required=True, enabled=enabled, include_parent=include_parent
        )

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

        for part in self.supplier_parts.all().prefetch_related(
            'purchase_order_line_items'
        ):
            for order in part.purchase_orders():
                if order not in orders:
                    orders.append(order)

        return orders

    @property
    def on_order(self):
        """Return the total number of items on order for this part.

        Note that some supplier parts may have a different pack_quantity attribute,
        and this needs to be taken into account!
        """
        quantity = 0

        # Iterate through all supplier parts
        for sp in self.supplier_parts.all():
            # Look at any incomplete line item for open orders
            lines = sp.purchase_order_line_items.filter(
                order__status__in=PurchaseOrderStatusGroups.OPEN,
                quantity__gt=F('received'),
            )

            for line in lines:
                remaining = line.quantity - line.received

                if remaining > 0:
                    quantity += sp.base_quantity(remaining)

        return quantity

    @property
    def has_variants(self):
        """Check if this Part object has variants underneath it."""
        return self.get_all_variants().exists()

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
        return self.get_conversion_options().exists()

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

        filtered_parts = filtered_parts.filter(active=True, virtual=False)

        return filtered_parts

    def get_related_parts(self):
        """Return a set of all related parts for this part."""
        related_parts = set()

        related_parts_1 = self.related_parts_1.filter(part_1__id=self.pk)

        related_parts_2 = self.related_parts_2.filter(part_2__id=self.pk)

        for related_part in related_parts_1:
            # Add to related parts list
            related_parts.add(related_part.part_2)

        for related_part in related_parts_2:
            # Add to related parts list
            related_parts.add(related_part.part_1)

        return related_parts

    @property
    def related_count(self):
        """Return the number of 'related parts' which point to this Part."""
        return len(self.get_related_parts())

    def is_part_low_on_stock(self):
        """Returns True if the total stock for this part is less than the minimum stock level."""
        return self.get_stock_count() < self.minimum_stock


@receiver(post_save, sender=Part, dispatch_uid='part_post_save_log')
def after_save_part(sender, instance: Part, created, **kwargs):
    """Function to be executed after a Part is saved."""
    from django.conf import settings

    from part import tasks as part_tasks

    if instance and not created and not InvenTree.ready.isImportingData():
        # Check part stock only if we are *updating* the part (not creating it)

        # Run this check in the background
        InvenTree.tasks.offload_task(
            part_tasks.notify_low_stock_if_required,
            instance.pk,
            group='notification',
            force_async=not settings.TESTING,  # Force async unless in testing mode
        )

        # Schedule a background task to rebuild any supplier parts
        InvenTree.tasks.offload_task(
            part_tasks.rebuild_supplier_parts,
            instance.pk,
            force_async=True,
            group='part',
        )


class PartPricing(common.models.MetaMixin):
    """Model for caching min/max pricing information for a particular Part.

    It is prohibitively expensive to calculate min/max pricing for a part "on the fly".
    As min/max pricing does not change very often, we pre-calculate and cache these values.

    Whenever pricing is updated, these values are re-calculated and stored.

    Pricing information is cached for:

    - BOM cost (min / max cost of component items)
    - Purchase cost (based on purchase history)
    - Internal cost (based on user-specified InternalPriceBreak data)
    - Supplier price (based on supplier part data)
    - Variant price (min / max cost of any variants)
    - Overall best / worst (based on the values listed above)
    - Sale price break min / max values
    - Historical sale pricing min / max values

    Note that this pricing information does not take "quantity" into account:
    - This provides a simple min / max pricing range, which is quite valuable in a lot of situations
    - Quantity pricing still needs to be calculated
    - Quantity pricing can be viewed from the part detail page
    - Detailed pricing information is very context specific in any case
    """

    # When calculating assembly pricing, we limit the depth of the calculation
    MAX_PRICING_DEPTH = 50

    @property
    def is_valid(self):
        """Return True if the cached pricing is valid."""
        return self.updated is not None

    def convert(self, money):
        """Attempt to convert money value to default currency.

        If a MissingRate error is raised, ignore it and return None
        """
        if money is None:
            return None

        target_currency = currency_code_default()

        try:
            result = convert_money(money, target_currency)
        except MissingRate:
            logger.warning(
                'No currency conversion rate available for %s -> %s',
                money.currency,
                target_currency,
            )
            result = None

        return result

    def schedule_for_update(self, counter: int = 0, refresh: bool = True):
        """Schedule this pricing to be updated.

        Arguments:
            counter: Recursion counter (used to prevent infinite recursion)
            refresh: If specified, the PartPricing object will be refreshed from the database
        """
        import InvenTree.ready

        # If importing data, skip pricing update
        if InvenTree.ready.isImportingData():
            return

        # If running data migrations, skip pricing update
        if InvenTree.ready.isRunningMigrations():
            return

        if (
            not self.part
            or not self.part.pk
            or not Part.objects.filter(pk=self.part.pk).exists()
        ):
            logger.warning(
                'Referenced part instance does not exist - skipping pricing update.'
            )
            return

        try:
            if refresh and self.pk:
                self.refresh_from_db()
        except (PartPricing.DoesNotExist, IntegrityError):
            # Error thrown if this PartPricing instance has already been removed
            logger.warning(
                "Error refreshing PartPricing instance for part '%s'", self.part
            )
            return

        # Ensure that the referenced part still exists in the database
        try:
            p = self.part
            if True:  # refresh and p.pk:
                p.refresh_from_db()
        except IntegrityError:
            logger.exception(
                "Could not update PartPricing as Part '%s' does not exist", self.part
            )
            return

        if self.scheduled_for_update:
            # Ignore if the pricing is already scheduled to be updated
            logger.debug('Pricing for %s already scheduled for update - skipping', p)
            return

        if counter > self.MAX_PRICING_DEPTH:
            # Prevent infinite recursion / stack depth issues
            logger.debug(
                counter, f'Skipping pricing update for {p} - maximum depth exceeded'
            )
            return

        try:
            self.scheduled_for_update = True
            self.save()
        except IntegrityError:
            # An IntegrityError here likely indicates that the referenced part has already been deleted
            logger.exception(
                "Could not save PartPricing for part '%s' to the database", self.part
            )
            return

        import part.tasks as part_tasks

        # Pricing calculations are performed in the background,
        # unless the TESTING_PRICING flag is set
        background = not settings.TESTING or not settings.TESTING_PRICING

        # Offload task to update the pricing
        # Force async, to prevent running in the foreground (unless in testing mode)
        InvenTree.tasks.offload_task(
            part_tasks.update_part_pricing,
            self,
            counter=counter,
            force_async=background,
            group='pricing',
        )

    def update_pricing(
        self,
        counter: int = 0,
        cascade: bool = True,
        previous_min=None,
        previous_max=None,
    ):
        """Recalculate all cost data for the referenced Part instance.

        Arguments:
            counter: Recursion counter (used to prevent infinite recursion)
            cascade: If True, update pricing for all assemblies and templates which use this part
            previous_min: Previous minimum price (used to prevent further updates if unchanged)
            previous_max: Previous maximum price (used to prevent further updates if unchanged)

        """
        # If importing data, skip pricing update
        if InvenTree.ready.isImportingData():
            return

        # If running data migrations, skip pricing update
        if InvenTree.ready.isRunningMigrations():
            return

        if self.pk is not None:
            try:
                self.refresh_from_db()
            except PartPricing.DoesNotExist:
                pass

        self.update_bom_cost(save=False)
        self.update_purchase_cost(save=False)
        self.update_internal_cost(save=False)
        self.update_supplier_cost(save=False)
        self.update_variant_cost(save=False)
        self.update_sale_cost(save=False)

        # Clear scheduling flag
        self.scheduled_for_update = False

        # Note: save method calls update_overall_cost
        try:
            self.save()
        except IntegrityError:
            # Background worker processes may try to concurrently update
            pass

        pricing_changed = False

        # Without previous pricing data, we assume that the pricing has changed
        if previous_min != self.overall_min or previous_max != self.overall_max:
            pricing_changed = True

        # Update parent assemblies and templates
        if pricing_changed and cascade:
            self.update_assemblies(counter)
            self.update_templates(counter)

    def update_assemblies(self, counter: int = 0):
        """Schedule updates for any assemblies which use this part."""
        # If the linked Part is used in any assemblies, schedule a pricing update for those assemblies

        used_in_parts = self.part.get_used_in()

        for p in used_in_parts:
            p.pricing.schedule_for_update(counter=counter + 1)

    def update_templates(self, counter: int = 0):
        """Schedule updates for any template parts above this part."""
        templates = self.part.get_ancestors(include_self=False)

        for p in templates:
            p.pricing.schedule_for_update(counter + 1)

    def save(self, *args, **kwargs):
        """Whenever pricing model is saved, automatically update overall prices."""
        # Update the currency which was used to perform the calculation
        self.currency = currency_code_default()

        try:
            self.update_overall_cost()
        except Exception:
            # If something has happened to the Part model, might throw an error
            pass

        try:
            super().save(*args, **kwargs)
        except Exception:
            # This error may be thrown if there is already duplicate pricing data
            pass

    def update_bom_cost(self, save=True):
        """Recalculate BOM cost for the referenced Part instance.

        Iterate through the Bill of Materials, and calculate cumulative pricing:

        cumulative_min: The sum of minimum costs for each line in the BOM
        cumulative_max: The sum of maximum costs for each line in the BOM

        Note: The cumulative costs are calculated based on the specified default currency
        """
        if not self.part.assembly:
            # Not an assembly - no BOM pricing
            self.bom_cost_min = None
            self.bom_cost_max = None

            if save:
                self.save()

            # Short circuit - no further operations required
            return

        currency_code = common.currency.currency_code_default()

        cumulative_min = Money(0, currency_code)
        cumulative_max = Money(0, currency_code)

        any_min_elements = False
        any_max_elements = False

        for bom_item in self.part.get_bom_items():
            # Loop through each BOM item which is used to assemble this part

            bom_item_min = None
            bom_item_max = None

            for sub_part in bom_item.get_valid_parts_for_allocation():
                # Check each part which *could* be used

                if sub_part != bom_item.sub_part and not sub_part.active:
                    continue

                sub_part_pricing = sub_part.pricing

                sub_part_min = self.convert(sub_part_pricing.overall_min)
                sub_part_max = self.convert(sub_part_pricing.overall_max)

                if sub_part_min is not None:
                    if bom_item_min is None or sub_part_min < bom_item_min:
                        bom_item_min = sub_part_min

                if sub_part_max is not None:
                    if bom_item_max is None or sub_part_max > bom_item_max:
                        bom_item_max = sub_part_max

            # Update cumulative totals
            if bom_item_min is not None:
                bom_item_min *= bom_item.quantity
                cumulative_min += self.convert(bom_item_min)

                any_min_elements = True

            if bom_item_max is not None:
                bom_item_max *= bom_item.quantity
                cumulative_max += self.convert(bom_item_max)

                any_max_elements = True

        if any_min_elements:
            self.bom_cost_min = cumulative_min
        else:
            self.bom_cost_min = None

        if any_max_elements:
            self.bom_cost_max = cumulative_max
        else:
            self.bom_cost_max = None

        if save:
            self.save()

    def update_purchase_cost(self, save=True):
        """Recalculate historical purchase cost for the referenced Part instance.

        Purchase history only takes into account "completed" purchase orders.
        """
        # Find all line items for completed orders which reference this part
        line_items = OrderModels.PurchaseOrderLineItem.objects.filter(
            order__status=PurchaseOrderStatus.COMPLETE.value,
            received__gt=0,
            part__part=self.part,
        )

        # Exclude line items which do not have an associated price
        line_items = line_items.exclude(purchase_price=None)

        purchase_min = None
        purchase_max = None

        for line in line_items:
            if line.purchase_price is None:
                continue

            # Take supplier part pack size into account
            purchase_cost = self.convert(
                line.purchase_price / line.part.pack_quantity_native
            )

            if purchase_cost is None:
                continue

            if purchase_min is None or purchase_cost < purchase_min:
                purchase_min = purchase_cost

            if purchase_max is None or purchase_cost > purchase_max:
                purchase_max = purchase_cost

        # Also check if manual stock item pricing is included
        if get_global_setting('PRICING_USE_STOCK_PRICING', True):
            items = self.part.stock_items.all()

            # Limit to stock items updated within a certain window
            days = int(get_global_setting('PRICING_STOCK_ITEM_AGE_DAYS', 0))

            if days > 0:
                date_threshold = InvenTree.helpers.current_date() - timedelta(days=days)
                items = items.filter(updated__gte=date_threshold)

            for item in items:
                cost = self.convert(item.purchase_price)

                # Skip if the cost could not be converted (for some reason)
                if cost is None:
                    continue

                if purchase_min is None or cost < purchase_min:
                    purchase_min = cost

                if purchase_max is None or cost > purchase_max:
                    purchase_max = cost

        self.purchase_cost_min = purchase_min
        self.purchase_cost_max = purchase_max

        if save:
            self.save()

    def update_internal_cost(self, save=True):
        """Recalculate internal cost for the referenced Part instance."""
        min_int_cost = None
        max_int_cost = None

        if get_global_setting('PART_INTERNAL_PRICE', False):
            # Only calculate internal pricing if internal pricing is enabled
            for pb in self.part.internalpricebreaks.all():
                cost = self.convert(pb.price)

                if cost is None:
                    # Ignore if cost could not be converted for some reason
                    continue

                if min_int_cost is None or cost < min_int_cost:
                    min_int_cost = cost

                if max_int_cost is None or cost > max_int_cost:
                    max_int_cost = cost

        self.internal_cost_min = min_int_cost
        self.internal_cost_max = max_int_cost

        if save:
            self.save()

    def update_supplier_cost(self, save=True):
        """Recalculate supplier cost for the referenced Part instance.

        - The limits are simply the lower and upper bounds of available SupplierPriceBreaks
        - We do not take "quantity" into account here
        """
        min_sup_cost = None
        max_sup_cost = None

        if self.part.purchaseable:
            # Iterate through each available SupplierPart instance
            for sp in self.part.supplier_parts.all():
                # Iterate through each available SupplierPriceBreak instance
                for pb in sp.pricebreaks.all():
                    if pb.price is None:
                        continue

                    # Ensure we take supplier part pack size into account
                    cost = self.convert(pb.price / sp.pack_quantity_native)

                    if cost is None:
                        continue

                    if min_sup_cost is None or cost < min_sup_cost:
                        min_sup_cost = cost

                    if max_sup_cost is None or cost > max_sup_cost:
                        max_sup_cost = cost

        self.supplier_price_min = min_sup_cost
        self.supplier_price_max = max_sup_cost

        if save:
            self.save()

    def update_variant_cost(self, save=True):
        """Update variant cost values.

        Here we track the min/max costs of any variant parts.
        """
        variant_min = None
        variant_max = None

        active_only = get_global_setting('PRICING_ACTIVE_VARIANTS', False)

        if self.part.is_template:
            variants = self.part.get_descendants(include_self=False)

            for v in variants:
                if active_only and not v.active:
                    # Ignore inactive variant parts
                    continue

                v_min = self.convert(v.pricing.overall_min)
                v_max = self.convert(v.pricing.overall_max)

                if v_min is not None:
                    if variant_min is None or v_min < variant_min:
                        variant_min = v_min

                if v_max is not None:
                    if variant_max is None or v_max > variant_max:
                        variant_max = v_max

        self.variant_cost_min = variant_min
        self.variant_cost_max = variant_max

        if save:
            self.save()

    def update_overall_cost(self):
        """Update overall cost values.

        Here we simply take the minimum / maximum values of the other calculated fields.
        """
        overall_min = None
        overall_max = None

        min_costs = [self.bom_cost_min, self.purchase_cost_min, self.internal_cost_min]

        max_costs = [self.bom_cost_max, self.purchase_cost_max, self.internal_cost_max]

        purchase_history_override = get_global_setting(
            'PRICING_PURCHASE_HISTORY_OVERRIDES_SUPPLIER', False
        )

        if get_global_setting('PRICING_USE_SUPPLIER_PRICING', True):
            # Add supplier pricing data, *unless* historical pricing information should override
            if self.purchase_cost_min is None or not purchase_history_override:
                min_costs.append(self.supplier_price_min)

            if self.purchase_cost_max is None or not purchase_history_override:
                max_costs.append(self.supplier_price_max)

        if get_global_setting('PRICING_USE_VARIANT_PRICING', True):
            # Include variant pricing in overall calculations
            min_costs.append(self.variant_cost_min)
            max_costs.append(self.variant_cost_max)

        # Calculate overall minimum cost
        for cost in min_costs:
            if cost is None:
                continue

            # Ensure we are working in a common currency
            cost = self.convert(cost)

            if overall_min is None or cost < overall_min:
                overall_min = cost

        # Calculate overall maximum cost
        for cost in max_costs:
            if cost is None:
                continue

            # Ensure we are working in a common currency
            cost = self.convert(cost)

            if overall_max is None or cost > overall_max:
                overall_max = cost

        if get_global_setting('PART_BOM_USE_INTERNAL_PRICE', False):
            # Check if internal pricing should override other pricing
            if self.internal_cost_min is not None:
                overall_min = self.internal_cost_min

            if self.internal_cost_max is not None:
                overall_max = self.internal_cost_max

        if self.override_min is not None:
            overall_min = self.convert(self.override_min)

        self.overall_min = overall_min

        if self.override_max is not None:
            overall_max = self.convert(self.override_max)

        self.overall_max = overall_max

    def update_sale_cost(self, save=True):
        """Recalculate sale cost data."""
        # Iterate through the sell price breaks
        min_sell_price = None
        max_sell_price = None

        for pb in self.part.salepricebreaks.all():
            cost = self.convert(pb.price)

            if cost is None:
                continue

            if min_sell_price is None or cost < min_sell_price:
                min_sell_price = cost

            if max_sell_price is None or cost > max_sell_price:
                max_sell_price = cost

        # Record min/max values
        self.sale_price_min = min_sell_price
        self.sale_price_max = max_sell_price

        min_sell_history = None
        max_sell_history = None

        # Calculate sale price history too
        parts = self.part.get_descendants(include_self=True)

        # Find all line items for shipped sales orders which reference this part
        line_items = OrderModels.SalesOrderLineItem.objects.filter(
            order__status__in=SalesOrderStatusGroups.COMPLETE, part__in=parts
        )

        # Exclude line items which do not have associated pricing data
        line_items = line_items.exclude(sale_price=None)

        for line in line_items:
            cost = self.convert(line.sale_price)

            if cost is None:
                continue

            if min_sell_history is None or cost < min_sell_history:
                min_sell_history = cost

            if max_sell_history is None or cost > max_sell_history:
                max_sell_history = cost

        self.sale_history_min = min_sell_history
        self.sale_history_max = max_sell_history

        if save:
            self.save()

    currency = models.CharField(
        default=currency_code_default,
        max_length=10,
        verbose_name=_('Currency'),
        help_text=_('Currency used to cache pricing calculations'),
        choices=common.currency.currency_code_mappings(),
    )

    scheduled_for_update = models.BooleanField(default=False)

    part = models.OneToOneField(
        Part,
        on_delete=models.CASCADE,
        related_name='pricing_data',
        verbose_name=_('Part'),
    )

    bom_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum BOM Cost'),
        help_text=_('Minimum cost of component parts'),
    )

    bom_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum BOM Cost'),
        help_text=_('Maximum cost of component parts'),
    )

    purchase_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Purchase Cost'),
        help_text=_('Minimum historical purchase cost'),
    )

    purchase_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Purchase Cost'),
        help_text=_('Maximum historical purchase cost'),
    )

    internal_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Internal Price'),
        help_text=_('Minimum cost based on internal price breaks'),
    )

    internal_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Internal Price'),
        help_text=_('Maximum cost based on internal price breaks'),
    )

    supplier_price_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Supplier Price'),
        help_text=_('Minimum price of part from external suppliers'),
    )

    supplier_price_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Supplier Price'),
        help_text=_('Maximum price of part from external suppliers'),
    )

    variant_cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Variant Cost'),
        help_text=_('Calculated minimum cost of variant parts'),
    )

    variant_cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Variant Cost'),
        help_text=_('Calculated maximum cost of variant parts'),
    )

    override_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Override minimum cost'),
    )

    override_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Override maximum cost'),
    )

    overall_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Cost'),
        help_text=_('Calculated overall minimum cost'),
    )

    overall_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Cost'),
        help_text=_('Calculated overall maximum cost'),
    )

    sale_price_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Sale Price'),
        help_text=_('Minimum sale price based on price breaks'),
    )

    sale_price_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Sale Price'),
        help_text=_('Maximum sale price based on price breaks'),
    )

    sale_history_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Sale Cost'),
        help_text=_('Minimum historical sale price'),
    )

    sale_history_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Sale Cost'),
        help_text=_('Maximum historical sale price'),
    )


class PartStocktake(models.Model):
    """Model representing a 'stock history' entry for a particular Part.

    A 'stocktake' is a representative count of available stock:
    - Performed on a given date
    - Records quantity of part in stock (across multiple stock items)
    - Records estimated value of "stock on hand"
    """

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='stocktakes',
        verbose_name=_('Part'),
        help_text=_('Part for stocktake'),
    )

    item_count = models.IntegerField(
        default=1,
        verbose_name=_('Item Count'),
        help_text=_('Number of individual stock entries at time of stocktake'),
    )

    quantity = models.DecimalField(
        max_digits=19,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        verbose_name=_('Quantity'),
        help_text=_('Total available stock at time of stocktake'),
    )

    date = models.DateField(
        verbose_name=_('Date'),
        help_text=_('Date stocktake was performed'),
        auto_now_add=True,
    )

    cost_min = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Minimum Stock Cost'),
        help_text=_('Estimated minimum cost of stock on hand'),
    )

    cost_max = InvenTree.fields.InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Stock Cost'),
        help_text=_('Estimated maximum cost of stock on hand'),
    )


class PartSellPriceBreak(common.models.PriceBreak):
    """Represents a price break for selling this part."""

    class Meta:
        """Metaclass providing extra model definition."""

        verbose_name = _('Part Sale Price Break')
        unique_together = ('part', 'quantity')

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartSellPriceBreak model."""
        return reverse('api-part-sale-price-list')

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='salepricebreaks',
        limit_choices_to={'salable': True},
        verbose_name=_('Part'),
    )


class PartInternalPriceBreak(common.models.PriceBreak):
    """Represents a price break for internally selling this part."""

    class Meta:
        """Metaclass providing extra model definition."""

        unique_together = ('part', 'quantity')

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartInternalPriceBreak model."""
        return reverse('api-part-internal-price-list')

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='internalpricebreaks',
        verbose_name=_('Part'),
    )


class PartStar(models.Model):
    """A PartStar object creates a subscription relationship between a User and a Part.

    It is used to designate a Part as 'subscribed' for a given User.

    Attributes:
        part: Link to a Part object
        user: Link to a User object
    """

    class Meta:
        """Metaclass providing extra model definition."""

        unique_together = ['part', 'user']

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        verbose_name=_('Part'),
        related_name='starred_users',
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='starred_parts',
    )


class PartCategoryStar(models.Model):
    """A PartCategoryStar creates a subscription relationship between a User and a PartCategory.

    Attributes:
        category: Link to a PartCategory object
        user: Link to a User object
    """

    class Meta:
        """Metaclass providing extra model definition."""

        unique_together = ['category', 'user']

    category = models.ForeignKey(
        PartCategory,
        on_delete=models.CASCADE,
        verbose_name=_('Category'),
        related_name='starred_users',
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='starred_categories',
    )


class PartTestTemplate(InvenTree.models.InvenTreeMetadataModel):
    """A PartTestTemplate defines a 'template' for a test which is required to be run against a StockItem (an instance of the Part).

    The test template applies "recursively" to part variants, allowing tests to be
    defined in a hierarchy.

    Test names are simply strings, rather than enforcing any sort of structure or pattern.
    It is up to the user to determine what tests are defined (and how they are run).

    To enable generation of unique lookup-keys for each test, there are some validation tests
    run on the model (refer to the validate_unique function).
    """

    class Meta:
        """Metaclass options for the PartTestTemplate model."""

        verbose_name = _('Part Test Template')

    def __str__(self):
        """Format a string representation of this PartTestTemplate."""
        return ' | '.join([self.part.name, self.test_name])

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartTestTemplate model."""
        return reverse('api-part-test-template-list')

    def save(self, *args, **kwargs):
        """Enforce 'clean' operation when saving a PartTestTemplate instance."""
        self.clean()

        super().save(*args, **kwargs)

    def clean(self):
        """Clean fields for the PartTestTemplate model."""
        self.test_name = self.test_name.strip()

        self.key = helpers.generateTestKey(self.test_name)

        if len(self.key) == 0:
            raise ValidationError({
                'test_name': _(
                    'Invalid template name - must include at least one alphanumeric character'
                )
            })

        # Check that 'choices' are in fact valid
        if self.choices is None:
            self.choices = ''
        else:
            self.choices = str(self.choices).strip()

        if self.choices:
            choice_set = set()

            for choice in self.choices.split(','):
                choice = choice.strip()

                # Ignore empty choices
                if not choice:
                    continue

                if choice in choice_set:
                    raise ValidationError({'choices': _('Choices must be unique')})

                choice_set.add(choice)

        self.validate_unique()
        super().clean()

    def validate_unique(self, exclude=None):
        """Test that this test template is 'unique' within this part tree."""
        if not self.part.testable:
            raise ValidationError({
                'part': _('Test templates can only be created for testable parts')
            })

        # Check that this test is unique for this part
        # (including template parts of which this part is a variant)
        parts = self.part.get_ancestors(include_self=True)

        tests = PartTestTemplate.objects.filter(key=self.key, part__in=parts).exclude(
            pk=self.pk
        )

        if tests.exists():
            raise ValidationError({
                'test_name': _(
                    'Test template with the same key already exists for part'
                )
            })

        super().validate_unique(exclude)

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='test_templates',
        limit_choices_to={'testable': True},
        verbose_name=_('Part'),
    )

    test_name = models.CharField(
        blank=False,
        max_length=100,
        verbose_name=_('Test Name'),
        help_text=_('Enter a name for the test'),
    )

    key = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Test Key'),
        help_text=_('Simplified key for the test'),
    )

    description = models.CharField(
        blank=False,
        null=True,
        max_length=100,
        verbose_name=_('Test Description'),
        help_text=_('Enter description for this test'),
    )

    enabled = models.BooleanField(
        default=True, verbose_name=_('Enabled'), help_text=_('Is this test enabled?')
    )

    required = models.BooleanField(
        default=True,
        verbose_name=_('Required'),
        help_text=_('Is this test required to pass?'),
    )

    requires_value = models.BooleanField(
        default=False,
        verbose_name=_('Requires Value'),
        help_text=_('Does this test require a value when adding a test result?'),
    )

    requires_attachment = models.BooleanField(
        default=False,
        verbose_name=_('Requires Attachment'),
        help_text=_(
            'Does this test require a file attachment when adding a test result?'
        ),
    )

    choices = models.CharField(
        max_length=5000,
        verbose_name=_('Choices'),
        help_text=_('Valid choices for this test (comma-separated)'),
        blank=True,
    )

    def get_choices(self):
        """Return a list of valid choices for this test template."""
        if not self.choices:
            return []

        return [x.strip() for x in self.choices.split(',') if x.strip()]


class BomItem(InvenTree.models.MetadataMixin, InvenTree.models.InvenTreeModel):
    """A BomItem links a part to its component items.

    A part can have a BOM (bill of materials) which defines
    which parts are required (and in what quantity) to make it.

    Attributes:
        part: Link to the parent part (the part that will be produced)
        sub_part: Link to the child part (the part that will be consumed)
        quantity: Number of 'sub_parts' consumed to produce one 'part'
        optional: Boolean field describing if this BomItem is optional
        consumable: Boolean field describing if this BomItem is considered a 'consumable'
        reference: BOM reference field (e.g. part designators)
        setup_quantity: Extra required quantity for a build, to account for setup losses
        attrition: Estimated losses for a Build, expressed as a percentage (e.g. '2%')
        rounding_multiple: Rounding quantity when calculating the required quantity for a build
        note: Note field for this BOM item
        checksum: Validation checksum for the particular BOM line item
        validated: Boolean field indicating if this BOM item is valid (checksum matches)
        inherited: This BomItem can be inherited by the BOMs of variant parts
        allow_variants: Stock for part variants can be substituted for this BomItem
    """

    class Meta:
        """Metaclass providing extra model definition."""

        verbose_name = _('BOM Item')

    def __str__(self):
        """Return a string representation of this BomItem instance."""
        return f'{decimal2string(self.quantity)} x {self.sub_part.full_name} to make {self.part.full_name}'

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the BomItem model."""
        return reverse('api-bom-list')

    def get_assemblies(self):
        """Return a list of assemblies which use this BomItem."""
        assemblies = [self.part]

        if self.inherited:
            assemblies += list(self.part.get_descendants(include_self=False))

        return assemblies

    def get_valid_parts_for_allocation(
        self, allow_variants=True, allow_substitutes=True
    ):
        """Return a list of valid parts which can be allocated against this BomItem.

        Includes:
        - The referenced sub_part
        - Any directly specified substitute parts
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

                # Account for variants of the substitute part (if allowed)
                if allow_variants and self.allow_variants:
                    for sub_variant in sub.part.get_descendants(include_self=False):
                        parts.add(sub_variant)

        valid_parts = []

        for p in parts:
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
        return Q(part__in=self.get_valid_parts_for_allocation())

    def delete(self):
        """Check if this item can be deleted."""
        import part.tasks as part_tasks

        self.check_part_lock(self.part)

        assemblies = self.get_assemblies()
        super().delete()

        for assembly in assemblies:
            # Offload task to update the checksum for this assembly
            InvenTree.tasks.offload_task(
                part_tasks.check_bom_valid, assembly.pk, group='part'
            )

    def save(self, *args, **kwargs):
        """Enforce 'clean' operation when saving a BomItem instance."""
        import part.tasks as part_tasks

        self.clean()

        check_lock = kwargs.pop('check_lock', True)

        if check_lock:
            self.check_part_lock(self.part)

        db_instance = self.get_db_instance()

        # Check if the part was changed
        deltas = self.get_field_deltas()

        if 'part' in deltas and (old_part := deltas['part'].get('old', None)):
            if check_lock:
                self.check_part_lock(old_part)

        # Update the 'validated' field based on checksum calculation
        self.validated = self.is_line_valid

        super().save(*args, **kwargs)

        # Do we need to recalculate the BOM hash for assemblies?
        if not db_instance or any(f in deltas for f in self.hash_fields()):
            # If this is a new BomItem, or if any of the fields used to calculate the hash have changed,
            # then we need to recalculate the BOM checksum for all assemblies which use this BomItem

            assemblies = set()

            if db_instance:
                # Find all assemblies which use this BomItem *after* we save
                assemblies.update(db_instance.get_assemblies())

            for assembly in assemblies:
                # Offload task to update the checksum for this assembly
                InvenTree.tasks.offload_task(
                    part_tasks.check_bom_valid, assembly.pk, group='part'
                )

    def check_part_lock(self, assembly):
        """When editing or deleting a BOM item, check if the assembly is locked.

        If locked, raise an exception.

        Arguments:
            assembly: The assembly part

        Raises:
            ValidationError: If the assembly is locked
        """
        # TODO: Perhaps control this with a global setting?

        if assembly.locked:
            raise ValidationError(_('BOM item cannot be modified - assembly is locked'))

        # If this BOM item is inherited, check all variants of the assembly
        if self.inherited:
            for part in assembly.get_descendants(include_self=False):
                if part.locked:
                    raise ValidationError(
                        _('BOM item cannot be modified - variant assembly is locked')
                    )

    # A link to the parent part
    # Each part will get a reverse lookup field 'bom_items'
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='bom_items',
        verbose_name=_('Part'),
        help_text=_('Select parent part'),
        limit_choices_to={'assembly': True},
    )

    # A link to the child item (sub-part)
    # Each part will get a reverse lookup field 'used_in'
    sub_part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='used_in',
        verbose_name=_('Sub part'),
        help_text=_('Select part to be used in BOM'),
        limit_choices_to={'component': True},
    )

    # Quantity required
    quantity = models.DecimalField(
        default=1.0,
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        verbose_name=_('Quantity'),
        help_text=_('BOM quantity for this BOM item'),
    )

    optional = models.BooleanField(
        default=False,
        verbose_name=_('Optional'),
        help_text=_('This BOM item is optional'),
    )

    consumable = models.BooleanField(
        default=False,
        verbose_name=_('Consumable'),
        help_text=_('This BOM item is consumable (it is not tracked in build orders)'),
    )

    setup_quantity = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        verbose_name=_('Setup Quantity'),
        help_text=_('Extra required quantity for a build, to account for setup losses'),
    )

    attrition = models.DecimalField(
        default=0,
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Attrition'),
        help_text=_(
            'Estimated attrition for a build, expressed as a percentage (0-100)'
        ),
    )

    rounding_multiple = models.DecimalField(
        null=True,
        blank=True,
        default=None,
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        verbose_name=_('Rounding Multiple'),
        help_text=_(
            'Round up required production quantity to nearest multiple of this value'
        ),
    )

    reference = models.CharField(
        max_length=5000,
        blank=True,
        verbose_name=_('Reference'),
        help_text=_('BOM item reference'),
    )

    # Note attached to this BOM line item
    note = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Note'),
        help_text=_('BOM item notes'),
    )

    checksum = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_('Checksum'),
        help_text=_('BOM line checksum'),
    )

    validated = models.BooleanField(
        default=False,
        verbose_name=_('Validated'),
        help_text=_('This BOM item has been validated'),
    )

    inherited = models.BooleanField(
        default=False,
        verbose_name=_('Gets inherited'),
        help_text=_('This BOM item is inherited by BOMs for variant parts'),
    )

    allow_variants = models.BooleanField(
        default=False,
        verbose_name=_('Allow Variants'),
        help_text=_('Stock items for variant parts can be used for this BOM item'),
    )

    def hash_fields(self) -> list[str]:
        """Return a list of fields to be used for hashing this BOM item.

        These fields are used to calculate the checksum hash of this BOM item.
        """
        return [
            'part_id',
            'sub_part_id',
            'quantity',
            'setup_quantity',
            'attrition',
            'rounding_multiple',
            'reference',
            'optional',
            'inherited',
            'consumable',
            'allow_variants',
        ]

    def get_item_hash(self) -> str:
        """Calculate the checksum hash of this BOM line item."""
        # Seed the hash with the ID of this BOM item
        result_hash = hashlib.md5(b'')

        for field in self.hash_fields():
            # Get the value of the field
            value = getattr(self, field, None)

            # If the value is None, use an empty string
            if value is None:
                value = ''

            # Normalize decimal values to ensure consistent representation
            # These values are only included if they are non-zero
            # This is to provide some backwards compatibility from before these fields were addede
            if value is not None and field in [
                'quantity',
                'attrition',
                'setup_quantity',
                'rounding_multiple',
            ]:
                try:
                    value = normalize(value)

                    if not value or value <= 0:
                        continue
                except Exception:
                    pass

            # Update the hash with the string representation of the value
            result_hash.update(str(value).encode())

        return str(result_hash.digest())

    def validate_hash(self, valid=True):
        """Mark this item as 'valid' (store the checksum hash).

        Args:
            valid: If true, validate the hash, otherwise invalidate it (default = True)
        """
        if valid:
            self.checksum = self.get_item_hash()
        else:
            self.checksum = ''

        # Save the BOM item (bypass lock check)
        self.save(check_lock=False)

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
            raise ValidationError({'quantity': _('Must be a valid number')})

        try:
            # Check for circular BOM references
            if self.sub_part:
                self.sub_part.check_add_to_bom(self.part, raise_error=True)

                # If the sub_part is 'trackable' then the 'quantity' field must be an integer
                if self.sub_part.trackable:
                    if self.quantity != int(self.quantity):
                        raise ValidationError({
                            'quantity': _(
                                'Quantity must be integer value for trackable parts'
                            )
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

    def can_build_quantity(self, available_stock: float) -> int:
        """Calculate the number of assemblies that can be built with the available stock.

        Arguments:
            available_stock: The amount of stock available for this BOM item

        Returns:
            The number of assemblies that can be built with the available stock.
            Returns 0 if the available stock is insufficient.
        """
        # Account for setup quantity
        available_stock = Decimal(max(0, available_stock - self.setup_quantity))
        quantity_decimal = Decimal(self.quantity)
        attrition_decimal = Decimal(self.attrition) / 100
        n = quantity_decimal * (1 + attrition_decimal)

        if n <= 0:
            return 0.0

        return int(available_stock / n)

    def get_required_quantity(self, build_quantity: float) -> float:
        """Calculate the required part quantity, based on the supplied build_quantity.

        Arguments:
            build_quantity: Number of assemblies to build

        Returns:
            Production quantity required for this component
        """
        # Base quantity requirement
        required = self.quantity * build_quantity

        # Account for attrition
        if self.attrition > 0:
            try:
                # Convert attrition percentage to decimal
                attrition = Decimal(self.attrition) / Decimal(100)
                required *= 1 + attrition
            except Exception:
                log_error('bom_item.get_required_quantity')

        # Account for setup quantity
        if self.setup_quantity > 0:
            try:
                setup_quantity = Decimal(self.setup_quantity)
                required += setup_quantity
            except Exception:
                log_error('bom_item.get_required_quantity')

        # We now have the total requirement
        # If a "rounding_multiple" is specified, then round up to the nearest multiple
        if self.rounding_multiple and self.rounding_multiple > 0:
            try:
                round_up = Decimal(self.rounding_multiple)
                value = Decimal(required)
                value = math.ceil(value / round_up) * round_up
                required = float(value)
            except InvalidOperation:
                log_error('bom_item.get_required_quantity')

        return required

    @property
    def price_range(self, internal=False):
        """Return the price-range for this BOM item."""
        # get internal price setting
        use_internal = get_global_setting('PART_BOM_USE_INTERNAL_PRICE', False)
        p_range = self.sub_part.get_price_range(
            self.quantity, internal=use_internal and internal
        )

        if p_range is None:
            return p_range

        p_min, p_max = p_range

        if p_min == p_max:
            return decimal2money(p_min)

        # Convert to better string representation
        p_min = decimal2money(p_min)
        p_max = decimal2money(p_max)

        return f'{p_min} to {p_max}'


@receiver(post_save, sender=BomItem, dispatch_uid='update_bom_build_lines')
def update_bom_build_lines(sender, instance, created, **kwargs):
    """Update existing build orders when a BomItem is created or edited."""
    if InvenTree.ready.canAppAccessDatabase() and not InvenTree.ready.isImportingData():
        import build.tasks

        InvenTree.tasks.offload_task(
            build.tasks.update_build_order_lines, instance.pk, group='build'
        )


@receiver(post_save, sender=BomItem, dispatch_uid='post_save_bom_item')
@receiver(
    post_save, sender=PartSellPriceBreak, dispatch_uid='post_save_sale_price_break'
)
@receiver(
    post_save,
    sender=PartInternalPriceBreak,
    dispatch_uid='post_save_internal_price_break',
)
def update_pricing_after_edit(sender, instance, created, **kwargs):
    """Callback function when a part price break is created or updated."""
    # Update part pricing *unless* we are importing data
    if (
        InvenTree.ready.canAppAccessDatabase(allow_test=settings.TESTING_PRICING)
        and not InvenTree.ready.isImportingData()
    ):
        if instance.part:
            instance.part.schedule_pricing_update(create=True)


@receiver(post_delete, sender=BomItem, dispatch_uid='post_delete_bom_item')
@receiver(
    post_delete, sender=PartSellPriceBreak, dispatch_uid='post_delete_sale_price_break'
)
@receiver(
    post_delete,
    sender=PartInternalPriceBreak,
    dispatch_uid='post_delete_internal_price_break',
)
def update_pricing_after_delete(sender, instance, **kwargs):
    """Callback function when a part price break is deleted."""
    # Update part pricing *unless* we are importing data
    if (
        InvenTree.ready.canAppAccessDatabase(allow_test=settings.TESTING_PRICING)
        and not InvenTree.ready.isImportingData()
    ):
        if instance.part:
            instance.part.schedule_pricing_update(create=False)


class BomItemSubstitute(InvenTree.models.InvenTreeMetadataModel):
    """A BomItemSubstitute provides a specification for alternative parts, which can be used in a bill of materials.

    Attributes:
        bom_item: Link to the parent BomItem instance
        part: The part which can be used as a substitute
    """

    class Meta:
        """Metaclass providing extra model definition."""

        verbose_name = _('BOM Item Substitute')

        # Prevent duplication of substitute parts
        unique_together = ('part', 'bom_item')

    def save(self, *args, **kwargs):
        """Enforce a full_clean when saving the BomItemSubstitute model."""
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
                'part': _('Substitute part cannot be the same as the master part')
            })

    @staticmethod
    def get_api_url():
        """Returns the list API endpoint URL associated with this model."""
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
        limit_choices_to={'component': True},
    )


class PartRelated(InvenTree.models.InvenTreeMetadataModel):
    """Store and handle related parts (eg. mating connector, crimps, etc.)."""

    class Meta:
        """Metaclass defines extra model properties."""

        unique_together = ('part_1', 'part_2')

    part_1 = models.ForeignKey(
        Part,
        related_name='related_parts_1',
        verbose_name=_('Part 1'),
        on_delete=models.CASCADE,
    )

    part_2 = models.ForeignKey(
        Part,
        related_name='related_parts_2',
        on_delete=models.CASCADE,
        verbose_name=_('Part 2'),
        help_text=_('Select Related Part'),
    )

    note = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Note'),
        help_text=_('Note for this relationship'),
    )

    def __str__(self):
        """Return a string representation of this Part-Part relationship."""
        return f'{self.part_1} <--> {self.part_2}'

    def save(self, *args, **kwargs):
        """Enforce a 'clean' operation when saving a PartRelated instance."""
        self.clean()
        self.validate_unique()
        super().save(*args, **kwargs)

    def clean(self):
        """Overwrite clean method to check that relation is unique."""
        super().clean()

        if self.part_1 == self.part_2:
            raise ValidationError(
                _('Part relationship cannot be created between a part and itself')
            )

        # Check for inverse relationship
        if PartRelated.objects.filter(part_1=self.part_2, part_2=self.part_1).exists():
            raise ValidationError(_('Duplicate relationship already exists'))
