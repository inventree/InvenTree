"""Models for parameters."""

import math

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

import common.models
import InvenTree.conversion
import InvenTree.models
import part.models as part_models
from common.settings import get_global_setting
from InvenTree import validators
from InvenTree.exceptions import log_error
from InvenTree.helpers import str2bool
from part.models import Part


class PartParameterTemplate(InvenTree.models.InvenTreeMetadataModel):
    """A PartParameterTemplate provides a template for key:value pairs for extra parameters fields/values to be added to a Part.

    This allows users to arbitrarily assign data fields to a Part beyond the built-in attributes.

    Attributes:
        name: The name (key) of the Parameter [string]
        units: The units of the Parameter [string]
        description: Description of the parameter [string]
        checkbox: Boolean flag to indicate whether the parameter is a checkbox [bool]
        choices: List of valid choices for the parameter [string]
        selectionlist: SelectionList that should be used for choices [selectionlist]
    """

    class Meta:
        """Metaclass options for the PartParameterTemplate model."""

        verbose_name = _('Part Parameter Template')

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartParameterTemplate model."""
        return reverse('api-part-parameter-template-list')

    def __str__(self):
        """Return a string representation of a PartParameterTemplate instance."""
        s = str(self.name)
        if self.units:
            s += f' ({self.units})'
        return s

    def clean(self):
        """Custom cleaning step for this model.

        Checks:
        - A 'checkbox' field cannot have 'choices' set
        - A 'checkbox' field cannot have 'units' set
        """
        super().clean()

        # Check that checkbox parameters do not have units or choices
        if self.checkbox:
            if self.units:
                raise ValidationError({
                    'units': _('Checkbox parameters cannot have units')
                })

            if self.choices:
                raise ValidationError({
                    'choices': _('Checkbox parameters cannot have choices')
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

    def validate_unique(self, exclude=None):
        """Ensure that PartParameterTemplates cannot be created with the same name.

        This test should be case-insensitive (which the unique caveat does not cover).
        """
        super().validate_unique(exclude)

        try:
            others = PartParameterTemplate.objects.filter(
                name__iexact=self.name
            ).exclude(pk=self.pk)

            if others.exists():
                msg = _('Parameter template name must be unique')
                raise ValidationError({'name': msg})
        except PartParameterTemplate.DoesNotExist:
            pass

    def get_choices(self):
        """Return a list of choices for this parameter template."""
        if self.selectionlist:
            return self.selectionlist.get_choices()

        if not self.choices:
            return []

        return [x.strip() for x in self.choices.split(',') if x.strip()]

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Parameter Name'),
        unique=True,
    )

    units = models.CharField(
        max_length=25,
        verbose_name=_('Units'),
        help_text=_('Physical units for this parameter'),
        blank=True,
        validators=[validators.validate_physical_units],
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Parameter description'),
        blank=True,
    )

    checkbox = models.BooleanField(
        default=False,
        verbose_name=_('Checkbox'),
        help_text=_('Is this parameter a checkbox?'),
    )

    choices = models.CharField(
        max_length=5000,
        verbose_name=_('Choices'),
        help_text=_('Valid choices for this parameter (comma-separated)'),
        blank=True,
    )

    selectionlist = models.ForeignKey(
        common.models.SelectionList,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='parameter_templates',
        verbose_name=_('Selection List'),
        help_text=_('Selection list for this parameter'),
    )


class PartParameter(InvenTree.models.InvenTreeMetadataModel):
    """A PartParameter is a specific instance of a PartParameterTemplate. It assigns a particular parameter <key:value> pair to a part.

    Attributes:
        part: Reference to a single Part object
        template: Reference to a single PartParameterTemplate object
        data: The data (value) of the Parameter [string]
    """

    class Meta:
        """Metaclass providing extra model definition."""

        verbose_name = _('Part Parameter')
        # Prevent multiple instances of a parameter for a single part
        unique_together = ('part', 'template')

    @staticmethod
    def get_api_url():
        """Return the list API endpoint URL associated with the PartParameter model."""
        return reverse('api-part-parameter-list')

    def __str__(self):
        """String representation of a PartParameter (used in the admin interface)."""
        return f'{self.part.full_name} : {self.template.name} = {self.data} ({self.template.units})'

    def delete(self):
        """Custom delete handler for the PartParameter model.

        - Check if the parameter can be deleted
        """
        self.check_part_lock()
        super().delete()

    def check_part_lock(self):
        """Check if the referenced part is locked."""
        # TODO: Potentially control this behaviour via a global setting

        if self.part.locked:
            raise ValidationError(_('Parameter cannot be modified - part is locked'))

    def save(self, *args, **kwargs):
        """Custom save method for the PartParameter model."""
        # Validate the PartParameter before saving
        self.calculate_numeric_value()

        # Check if the part is locked
        self.check_part_lock()

        # Convert 'boolean' values to 'True' / 'False'
        if self.template.checkbox:
            self.data = str2bool(self.data)
            self.data_numeric = 1 if self.data else 0

        super().save(*args, **kwargs)

    def clean(self):
        """Validate the PartParameter before saving to the database."""
        super().clean()

        # Validate the parameter data against the template units
        if (
            get_global_setting(
                'PART_PARAMETER_ENFORCE_UNITS', True, cache=False, create=False
            )
            and self.template.units
        ):
            try:
                InvenTree.conversion.convert_physical_value(
                    self.data, self.template.units
                )
            except ValidationError as e:
                raise ValidationError({'data': e.message})

        # Validate the parameter data against the template choices
        if choices := self.template.get_choices():
            if self.data not in choices:
                raise ValidationError({'data': _('Invalid choice for parameter value')})

        self.calculate_numeric_value()

        # Run custom validation checks (via plugins)
        from plugin.registry import registry

        for plugin in registry.with_mixin('validation'):
            # Note: The validate_part_parameter function may raise a ValidationError
            try:
                result = plugin.validate_part_parameter(self, self.data)
                if result:
                    break
            except ValidationError as exc:
                # Re-throw the ValidationError against the 'data' field
                raise ValidationError({'data': exc.message})
            except Exception:
                log_error(f'{plugin.slug}.validate_part_parameter')

    def calculate_numeric_value(self):
        """Calculate a numeric value for the parameter data.

        - If a 'units' field is provided, then the data will be converted to the base SI unit.
        - Otherwise, we'll try to do a simple float cast
        """
        if self.template.units:
            try:
                self.data_numeric = InvenTree.conversion.convert_physical_value(
                    self.data, self.template.units
                )
            except (ValidationError, ValueError):
                self.data_numeric = None

        # No units provided, so try to cast to a float
        else:
            try:
                self.data_numeric = float(self.data)
            except ValueError:
                self.data_numeric = None

        if self.data_numeric is not None and type(self.data_numeric) is float:
            # Prevent out of range numbers, etc
            # Ref: https://github.com/inventree/InvenTree/issues/7593
            if math.isnan(self.data_numeric) or math.isinf(self.data_numeric):
                self.data_numeric = None

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='parameters',
        verbose_name=_('Part'),
        help_text=_('Parent Part'),
    )

    template = models.ForeignKey(
        PartParameterTemplate,
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name=_('Template'),
        help_text=_('Parameter Template'),
    )

    data = models.CharField(
        max_length=500,
        verbose_name=_('Data'),
        help_text=_('Parameter Value'),
        validators=[MinLengthValidator(1)],
    )

    data_numeric = models.FloatField(default=None, null=True, blank=True)

    @property
    def units(self):
        """Return the units associated with the template."""
        return self.template.units

    @property
    def name(self):
        """Return the name of the template."""
        return self.template.name

    @property
    def description(self):
        """Return the description of the template."""
        return self.template.description

    @classmethod
    def create(cls, part, template, data, save=False):
        """Custom save method for the PartParameter class."""
        part_parameter = cls(part=part, template=template, data=data)
        if save:
            part_parameter.save()
        return part_parameter


class PartParameterTemplateFilter(rest_filters.FilterSet):
    """FilterSet for PartParameterTemplate objects."""

    class Meta:
        """Metaclass options."""

        model = PartParameterTemplate

        # Simple filter fields
        fields = ['name', 'units', 'checkbox']

    has_choices = rest_filters.BooleanFilter(
        method='filter_has_choices', label='Has Choice'
    )

    def filter_has_choices(self, queryset, name, value):
        """Filter queryset to include only PartParameterTemplates with choices."""
        if str2bool(value):
            return queryset.exclude(Q(choices=None) | Q(choices=''))

        return queryset.filter(Q(choices=None) | Q(choices='')).distinct()

    has_units = rest_filters.BooleanFilter(method='filter_has_units', label='Has Units')

    def filter_has_units(self, queryset, name, value):
        """Filter queryset to include only PartParameterTemplates with units."""
        if str2bool(value):
            return queryset.exclude(Q(units=None) | Q(units=''))

        return queryset.filter(Q(units=None) | Q(units='')).distinct()

    part = rest_filters.ModelChoiceFilter(
        queryset=part_models.Part.objects.all(), method='filter_part', label=_('Part')
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_part(self, queryset, name, part):
        """Filter queryset to include only PartParameterTemplates which are referenced by a part."""
        parameters = PartParameter.objects.filter(part=part)
        template_ids = parameters.values_list('template').distinct()
        return queryset.filter(pk__in=[el[0] for el in template_ids])

    # Filter against a "PartCategory" - return only parameter templates which are referenced by parts in this category
    category = rest_filters.ModelChoiceFilter(
        queryset=part_models.PartCategory.objects.all(),
        method='filter_category',
        label=_('Category'),
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_category(self, queryset, name, category):
        """Filter queryset to include only PartParameterTemplates which are referenced by parts in this category."""
        cats = category.get_descendants(include_self=True)
        parameters = PartParameter.objects.filter(part__category__in=cats)
        template_ids = parameters.values_list('template').distinct()
        return queryset.filter(pk__in=[el[0] for el in template_ids])


@receiver(
    post_save,
    sender=PartParameterTemplate,
    dispatch_uid='post_save_part_parameter_template',
)
def post_save_part_parameter_template(sender, instance, created, **kwargs):
    """Callback function when a PartParameterTemplate is created or saved."""
    import part.tasks as part_tasks

    if InvenTree.ready.canAppAccessDatabase() and not InvenTree.ready.isImportingData():
        if not created:
            # Schedule a background task to rebuild the parameters against this template
            InvenTree.tasks.offload_task(
                part_tasks.rebuild_parameters,
                instance.pk,
                force_async=True,
                group='part',
            )


class PartCategoryParameterTemplate(InvenTree.models.InvenTreeMetadataModel):
    """A PartCategoryParameterTemplate creates a unique relationship between a PartCategory and a PartParameterTemplate.

    Multiple PartParameterTemplate instances can be associated to a PartCategory to drive a default list of parameter templates attached to a Part instance upon creation.

    Attributes:
        category: Reference to a single PartCategory object
        parameter_template: Reference to a single PartParameterTemplate object
        default_value: The default value for the parameter in the context of the selected
                       category
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
                fields=['category', 'parameter_template'],
                name='unique_category_parameter_template_pair',
            )
        ]

    def __str__(self):
        """String representation of a PartCategoryParameterTemplate (admin interface)."""
        if self.default_value:
            return f'{self.category.name} | {self.parameter_template.name} | {self.default_value}'
        return f'{self.category.name} | {self.parameter_template.name}'

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
                'PART_PARAMETER_ENFORCE_UNITS', True, cache=False, create=False
            )
            and self.parameter_template.units
        ):
            try:
                InvenTree.conversion.convert_physical_value(
                    self.default_value, self.parameter_template.units
                )
            except ValidationError as e:
                raise ValidationError({'default_value': e.message})

    category = models.ForeignKey(
        part_models.PartCategory,
        on_delete=models.CASCADE,
        related_name='parameter_templates',
        verbose_name=_('Category'),
        help_text=_('Part Category'),
    )

    parameter_template = models.ForeignKey(
        PartParameterTemplate,
        on_delete=models.CASCADE,
        related_name='part_categories',
        verbose_name=_('Parameter Template'),
        help_text=_('Parameter Template'),
    )

    default_value = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Default Value'),
        help_text=_('Default Parameter Value'),
    )
