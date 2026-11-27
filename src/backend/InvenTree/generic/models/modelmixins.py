"""Generic models which provide extra functionality over base Django model types."""

from collections.abc import Callable
from datetime import datetime
from string import Formatter
from typing import Any, Optional

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import QuerySet
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

import structlog
from mptt.models import TreeForeignKey
from rest_framework.exceptions import PermissionDenied
from stdimage.models import StdImageField
from taggit.managers import TaggableManager

import common.settings
import common.validators
import InvenTree.format
import InvenTree.helpers
import report.mixins
from generic.modelfeatures import ModelFeatureMixin

from .internal import DiffMixin, InvenTreePermissionCheckMixin

logger = structlog.get_logger('inventree')


class InvenTreePluginValidationMixin(DiffMixin):
    """Mixin class which exposes the model instance to plugin validation.

    Any model class which inherits from this mixin will be exposed to the plugin validation system.
    """

    def should_plugin_validate(self):
        """Return True if this model instance should be validated by plugins.

        The default implementation returns True, but this can be overridden in the implementing class if required.
        """
        from InvenTree.ready import isReadOnlyCommand

        # Prevent plugin validation when importing or exporting data
        return not isReadOnlyCommand()

    def run_plugin_validation(self):
        """Throw this model against the plugin validation interface."""
        from plugin import PluginMixinEnum, registry

        if not self.should_plugin_validate():
            return

        deltas = self.get_field_deltas()

        for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
            try:
                if plugin.validate_model_instance(self, deltas=deltas) is True:
                    return
            except ValidationError as exc:
                raise exc
            except Exception:
                # Log the exception to the database
                import InvenTree.exceptions

                InvenTree.exceptions.log_error(
                    'validate_model_instance', plugin=plugin.slug
                )
                raise ValidationError(_('Error running plugin validation'))

    def full_clean(self, *args, **kwargs):
        """Run plugin validation on full model clean.

        Note that plugin validation is performed *after* super.full_clean()
        """
        super().full_clean(*args, **kwargs)
        self.run_plugin_validation()

    def save(self, *args, **kwargs):
        """Run plugin validation on model save.

        Note that plugin validation is performed *before* super.save()
        """
        self.run_plugin_validation()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Run plugin validation on model delete.

        Allows plugins to prevent model instances from being deleted.

        Note: Each plugin may raise a ValidationError to prevent deletion.
        """
        from InvenTree.exceptions import log_error
        from plugin import PluginMixinEnum, registry

        if self.should_plugin_validate():
            for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
                try:
                    plugin.validate_model_deletion(self)
                except ValidationError as e:
                    # Plugin might raise a ValidationError to prevent deletion
                    raise e
                except Exception:
                    log_error('validate_model_deletion', plugin=plugin.slug)
                    continue

        super().delete(*args, **kwargs)


class InvenTreeMetadataMixin(models.Model):
    """Model mixin class which adds a JSON metadata field to a model, for use by any (and all) plugins.

    The intent of this mixin is to provide a metadata field on a model instance,
    for plugins to read / modify as required, to store any extra information.

    The assumptions for models implementing this mixin are:

    - The internal InvenTree business logic will make no use of this field
    - Multiple plugins may read / write to this metadata field, and not assume they have sole rights
    """

    class Meta:
        """Meta for MetadataMixin."""

        abstract = True

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        """Save the model instance, and perform validation on the metadata field."""
        self.validate_metadata()
        if len(args) > 0:
            raise TypeError(
                'save() takes no positional arguments anymore'
            )  # pragma: no cover
        super().save(force_insert=force_insert, force_update=force_update, **kwargs)

    def clean(self, *args, **kwargs):
        """Perform model validation on the metadata field."""
        super().clean()

        self.validate_metadata()

    def validate_metadata(self):
        """Validate the metadata field."""
        # Ensure that the 'metadata' field is a valid dict object
        if self.metadata is None:
            self.metadata = {}

        if type(self.metadata) is not dict:
            raise ValidationError({
                'metadata': _('Metadata must be a python dict object')
            })

    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Plugin Metadata'),
        help_text=_('JSON metadata field, for use by external plugins'),
    )

    def get_metadata(self, key: str, backup_value=None):
        """Finds metadata for this model instance, using the provided key for lookup.

        Args:
            key: String key for requesting metadata. e.g. if a plugin is accessing the metadata, the plugin slug should be used
            backup_value: Value that should be used if no value is found

        Returns:
            Python dict object containing requested metadata. If no matching metadata is found, returns None
        """
        if self.metadata is None:
            return backup_value

        return self.metadata.get(key, backup_value)

    def set_metadata(
        self, key: str, data, commit: bool = True, overwrite: bool = False
    ):
        """Save the provided metadata under the provided key.

        Args:
            key (str): Key for saving metadata
            data (Any): Data object to save - must be able to be rendered as a JSON string
            commit (bool, optional): If true, existing metadata with the provided key will be overwritten. If false, a merge will be attempted. Defaults to True.
            overwrite (bool): If true, delete existing metadata before adding new value
        """
        if overwrite or self.metadata is None:
            self.metadata = {}

        self.metadata[key] = data

        if commit:
            self.save()


class InvenTreeReferenceIndexingMixin(models.Model):
    """A mixin for keeping track of numerical copies of the "reference" field.

    Here, we attempt to convert a "reference" field value (char) to an integer,
    for performing fast natural sorting.

    This requires extra database space (due to the extra table column),
    but is required as not all supported database backends provide equivalent casting.

    This mixin adds a field named 'reference_int'.

    - If the 'reference' field can be cast to an integer, it is stored here
    - If the 'reference' field *starts* with an integer, it is stored here
    - Otherwise, we store zero
    """

    # Name of the global setting which defines the required reference pattern for this model
    REFERENCE_PATTERN_SETTING = None

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    @classmethod
    def get_reference_pattern(cls):
        """Returns the reference pattern associated with this model.

        This is defined by a global setting object, specified by the REFERENCE_PATTERN_SETTING attribute
        """
        # By default, we return an empty string
        if cls.REFERENCE_PATTERN_SETTING is None:
            return ''

        return common.settings.get_global_setting(
            cls.REFERENCE_PATTERN_SETTING, create=False
        ).strip()

    @classmethod
    def get_reference_context(cls):
        """Generate context data for generating the 'reference' field for this class.

        - Returns a python dict object which contains the context data for formatting the reference string.
        - The default implementation provides some default context information
        - The '?' key is required to accept our wildcard-with-default syntax {?:default}
        """
        return {'ref': cls.get_next_reference(), 'date': datetime.now(), '?': '?'}

    @classmethod
    def get_most_recent_item(cls):
        """Return the item which is 'most recent'.

        In practice, this means the item with the highest reference value
        """
        query = cls.objects.all().order_by('-reference_int', '-pk')

        if query.exists():
            return query.first()
        return None

    @classmethod
    def get_next_reference(cls):
        """Return the next available reference value for this particular class."""
        # Find the "most recent" item
        latest = cls.get_most_recent_item()

        if not latest:
            # No existing items
            return 1

        reference = latest.reference.strip()

        try:
            reference = InvenTree.format.extract_named_group(
                'ref', reference, cls.get_reference_pattern()
            )
        except Exception:
            # If reference cannot be extracted using the pattern, try just the integer value
            reference = str(latest.reference_int)

        # Attempt to perform 'intelligent' incrementing of the reference field
        incremented = InvenTree.helpers.increment(reference)

        try:
            incremented = int(incremented)
        except ValueError:
            pass

        return incremented

    @classmethod
    def generate_reference(cls):
        """Generate the next 'reference' field based on specified pattern."""

        # Based on https://stackoverflow.com/a/57570269/14488558
        class ReferenceFormatter(Formatter):
            def format_field(self, value, format_spec):
                if isinstance(value, str) and value == '?':
                    value = format_spec
                    format_spec = ''
                return super().format_field(value, format_spec)

        ref_ptn = cls.get_reference_pattern()
        ctx = cls.get_reference_context()
        fmt = ReferenceFormatter()

        reference = None

        attempts = set()

        while reference is None:
            try:
                ref = fmt.format(ref_ptn, **ctx)

                if ref in attempts:
                    # We are stuck in a loop!
                    reference = ref
                    break
                else:
                    attempts.add(ref)

                    if cls.objects.filter(reference=ref).exists():
                        # Handle case where we have duplicated an existing reference
                        ctx['ref'] = InvenTree.helpers.increment(ctx['ref'])
                    else:
                        # We have found an 'unused' reference
                        reference = ref
                        break

            except Exception:
                # If anything goes wrong, return the most recent reference
                recent = cls.get_most_recent_item()
                reference = recent.reference if recent else ''

        return reference

    @classmethod
    def validate_reference_pattern(cls, pattern):
        """Ensure that the provided pattern is valid."""
        ctx = cls.get_reference_context()

        try:
            info = InvenTree.format.parse_format_string(pattern)
        except Exception as exc:
            raise ValidationError({
                'value': _('Improperly formatted pattern') + ': ' + str(exc)
            })

        # Check that only 'allowed' keys are provided
        for key in info:
            if key not in ctx:
                raise ValidationError({
                    'value': _('Unknown format key specified') + f": '{key}'"
                })

        # Check that the 'ref' variable is specified
        if 'ref' not in info:
            raise ValidationError({
                'value': _('Missing required format key') + ": 'ref'"
            })

    @classmethod
    def validate_reference_field(cls, value):
        """Check that the provided 'reference' value matches the requisite pattern."""
        pattern = cls.get_reference_pattern()

        value = str(value).strip()

        if len(value) == 0:
            raise ValidationError(_('Reference field cannot be empty'))

        # An 'empty' pattern means no further validation is required
        if not pattern:
            return

        if not InvenTree.format.validate_string(value, pattern):
            raise ValidationError(
                _('Reference must match required pattern') + ': ' + pattern
            )

        # Check that the reference field can be rebuild
        return cls.rebuild_reference_field(value, validate=True)

    @classmethod
    def rebuild_reference_field(cls, reference, validate=False):
        """Extract integer out of reference for sorting.

        If the 'integer' portion is buried somewhere 'within' the reference,
        we can first try to extract it using the pattern.

        Example:
        reference - BO-123-ABC
        pattern - BO-{ref}-???
        extracted - 123

        If we cannot extract using the pattern for some reason, fallback to the entire reference
        """
        try:
            # Extract named group based on provided pattern
            reference = InvenTree.format.extract_named_group(
                'ref', reference, cls.get_reference_pattern()
            )
        except Exception:
            pass

        reference_int = InvenTree.helpers.extract_int(reference)

        if validate and reference_int > models.BigIntegerField.MAX_BIGINT:
            raise ValidationError({'reference': _('Reference number is too large')})

        return reference_int

    reference_int = models.BigIntegerField(default=0)


class InvenTreeAuditMixin(ModelFeatureMixin):
    """Opt a model in to the audit log (field-level change history).

    Any concrete model which inherits from this mixin is registered with django-auditlog
    when the 'audit' app is loaded (see audit.registry).

    Attributes:
        AUDIT_INCLUDE_FIELDS: If specified, *only* these fields are recorded (e.g. user-editable fields of a cache model)
        AUDIT_EXCLUDE_FIELDS: Fields which are never recorded (merged with a base set, see audit.registry)
        AUDIT_MASK_FIELDS: Fields whose values are masked (the change is recorded, the value is not)
        AUDIT_M2M_FIELDS: Many-to-many fields which are tracked
        AUDIT_PARENT_FIELD: Name of the field which links to the "parent" object (e.g. 'order' for a line item)
        AUDIT_VIEW_RESTRICTION: Restrict reading audit history to 'staff' or 'superuser' users (or None)
        AUDIT_REQUIRE_PARENT_PERMISSION: Entries are only visible to users who can view the *parent* model
            (for models whose access is determined by the linked object, e.g. attachments)
        AUDIT_EVENT_TYPES: Enumeration of named event types which can be recorded against this model
            (e.g. StockHistoryCode) - see audit.helpers.audit_event
    """

    MODEL_FEATURE = 'org.inventree.i.modelfeatures.history'

    AUDIT_INCLUDE_FIELDS: tuple[str, ...] = ()
    AUDIT_EXCLUDE_FIELDS: tuple[str, ...] = ()
    AUDIT_MASK_FIELDS: tuple[str, ...] = ()
    AUDIT_M2M_FIELDS: tuple[str, ...] = ()
    AUDIT_PARENT_FIELD: Optional[str] = None
    AUDIT_VIEW_RESTRICTION: Optional[str] = None
    AUDIT_REQUIRE_PARENT_PERMISSION: bool = False
    AUDIT_EVENT_TYPES: Optional[type] = None

    def get_audit_parent(self):
        """Return the "parent" object for audit log entries against this instance.

        Audit entries linked to a parent are included in the history of that parent
        (e.g. changes to line items are shown against the order).
        """
        if self.AUDIT_PARENT_FIELD:
            return getattr(self, self.AUDIT_PARENT_FIELD, None)

        return None

    def get_audit_parent_reference(self) -> Optional[tuple[Any, str]]:
        """Return a (ContentType, pk) reference to the "parent" object (or None).

        Override this (rather than get_audit_parent) where the parent can be identified
        without fetching it from the database (e.g. generic model_type / model_id links).
        """
        from django.contrib.contenttypes.models import ContentType

        # Resolve a foreign key parent from its ID, without fetching the related object
        if self.AUDIT_PARENT_FIELD:
            field = self._meta.get_field(self.AUDIT_PARENT_FIELD)

            if field.many_to_one or field.one_to_one:
                parent_id = getattr(self, field.attname)

                if parent_id is None:
                    return None

                return ContentType.objects.get_for_model(field.related_model), str(
                    parent_id
                )

        if parent := self.get_audit_parent():
            return ContentType.objects.get_for_model(parent), str(parent.pk)

        return None

    def should_audit(self) -> bool:
        """Return False to skip recording audit entries for this instance.

        Used where only some rows of a model are of interest
        (e.g. settings which are written automatically by the system).
        """
        return True

    def audit_always(self) -> bool:
        """Return True to record audit entries for this instance, even if the audit log is disabled.

        Used for changes which must always be recorded (e.g. disabling the audit log itself).
        """
        return False

    def is_audit_masked(self) -> bool:
        """Return True if *all* values recorded against this instance must be masked.

        Used where sensitivity depends on the row rather than the field
        (e.g. a 'protected' setting value).
        """
        return False


class InvenTreeParameterMixin(
    ModelFeatureMixin, InvenTreePermissionCheckMixin, models.Model
):
    """Provides an abstracted class for managing parameters.

    Links the implementing model to the common.models.Parameter table,
    and provides the following methods:
    """

    MODEL_FEATURE = 'org.inventree.i.modelfeatures.parameters'

    class Meta:
        """Metaclass options for InvenTreeParameterMixin."""

        abstract = True

    # Define a reverse relation to the Parameter model
    parameters_list = GenericRelation(
        'common.Parameter', content_type_field='model_type', object_id_field='model_id'
    )

    @staticmethod
    def annotate_parameters(queryset: QuerySet) -> QuerySet:
        """Annotate a queryset with pre-fetched parameters.

        Args:
            queryset: Queryset to annotate

        Returns:
            Annotated queryset
        """
        return queryset.prefetch_related(
            'parameters_list',
            'parameters_list__model_type',
            'parameters_list__updated_by',
            'parameters_list__template',
            'parameters_list__template__model_type',
        )

    @property
    @report.mixins.report_attribute()
    def parameters(self) -> report.mixins.QuerySet:
        """Return a QuerySet containing all the Parameter instances for this model.

        This will return pre-fetched data if available (i.e. in a serializer context).
        """
        # Check the query cache for pre-fetched parameters
        if cache := getattr(self, '_prefetched_objects_cache', None):
            if 'parameters_list' in cache:
                return cache['parameters_list']

        return self.parameters_list.all().prefetch_related('template')

    def delete(self, *args, **kwargs):
        """Handle the deletion of a model instance.

        Before deleting the model instance, delete any associated parameters.
        """
        self.parameters_list.all().delete()
        super().delete(*args, **kwargs)

    @transaction.atomic
    def copy_parameters_from(self, other, clear=True, **kwargs):
        """Copy all parameters from another model instance.

        Arguments:
            other: The other model instance to copy parameters from
            clear: If True, clear existing parameters before copying
            **kwargs: Additional keyword arguments to pass to the Parameter constructor
        """
        import common.models

        if clear:
            self.parameters_list.all().delete()

        parameters = []

        content_type = ContentType.objects.get_for_model(self.__class__)

        # Skip any parameters which are linked to a template with a uniqueness requirement,
        # as copying these values would create conflicting (duplicate) values
        copyable_parameters = [
            parameter
            for parameter in other.parameters.all().select_related('template')
            if parameter.template.unique
            == common.models.ParameterTemplate.UniqueOptions.NONE
        ]

        template_ids = [parameter.template.pk for parameter in copyable_parameters]

        # Remove all conflicting parameters first
        self.parameters_list.filter(template__pk__in=template_ids).delete()

        for parameter in copyable_parameters:
            parameter.pk = None
            parameter.model_id = self.pk
            parameter.model_type = content_type

            parameters.append(parameter)

        if len(parameters) > 0:
            from audit.helpers import audited_bulk_create

            audited_bulk_create(common.models.Parameter, parameters)

    def get_parameter(self, name: str):
        """Return a Parameter instance for the given parameter name.

        Args:
            name: Name of the parameter template

        Returns:
            Parameter instance if found, else None
        """
        return self.parameters_list.filter(template__name=name).first()

    def get_parameters(self) -> QuerySet:
        """Return all Parameter instances for this model."""
        return (
            self.parameters_list
            .all()
            .prefetch_related('template', 'model_type')
            .order_by('template__name')
        )

    def parameters_map(self) -> dict:
        """Return a map (dict) of parameter values associated with this Part instance, of the form.

        Example:
        {
            "name_1": "value_1",
            "name_2": "value_2",
        }
        """
        params = {}

        for parameter in self.parameters.all().prefetch_related('template'):
            params[parameter.template.name] = parameter.data

        return params

    def check_parameter_delete(self, parameter) -> bool:
        """Run a check to determine if the provided parameter can be deleted.

        The default implementation always returns True, but this can be overridden in the implementing class.
        """
        return True

    def check_parameter_save(self, parameter) -> bool:
        """Run a check to determine if the provided parameter can be saved.

        The default implementation always returns True, but this can be overridden in the implementing class.
        """
        return True


class InvenTreeNoteMixin(
    ModelFeatureMixin, InvenTreePermissionCheckMixin, models.Model
):
    """Provides an abstracted class for managing notes.

    Links the implementing model to the common.models.Note table,
    and provides multiple accessor / helper methods.
    """

    MODEL_FEATURE = 'org.inventree.i.modelfeatures.notes'

    class Meta:
        """Metaclass options for InvenTreeNoteMixin."""

        abstract = True

    # Define a reverse relation to the Note model
    notes_list = GenericRelation(
        'common.Note', content_type_field='model_type', object_id_field='model_id'
    )

    @property
    def notes(self) -> QuerySet:
        """Return a queryset containing all notes for this model."""
        # Check the query cache for pre-fetched parameters
        if cache := getattr(self, '_prefetched_objects_cache', None):
            if 'notes_list' in cache:
                return cache['notes_list']

        return self.notes_list.all()

    def delete(self, *args, **kwargs):
        """Handle the deletion of a model instance.

        Before deleting the model instance, delete any associated notes.
        """
        self.notes_list.all().delete()
        super().delete(*args, **kwargs)

    @transaction.atomic
    def copy_notes_from(self, other, **kwargs):
        """Copy all notes from another model instance.

        Arguments:
            other: The other model instance to copy notes from
        """
        import os

        from django.core.files.base import ContentFile

        import common.models

        content_type = ContentType.objects.get_for_model(self.__class__)

        # Prefetch each note's images in a single extra query, rather than
        # one 'images.all()' query per note.
        #
        # Sort so primary note is saved last — Note.save() promotes the last
        # note saved with primary=True, which correctly mirrors the source.
        # This (and the resulting demotion of sibling notes) is real business
        # logic in Note.save(), so notes must still be saved one at a time,
        # in this order - unlike common.migrations.0051's data migration,
        # which bulk_create()s notes directly, this can't do the same: that
        # migration operates on a historical model with no custom
        # save()/clean() methods at all, so there's no primary-flag logic to
        # preserve there in the first place.
        source_notes = sorted(
            other.notes.all().prefetch_related('images'), key=lambda n: n.primary
        )

        for source_note in source_notes:
            new_note = common.models.Note(
                model_type=content_type,
                model_id=self.pk,
                primary=source_note.primary,
                title=source_note.title,
                description=source_note.description,
                content=source_note.content,
            )
            new_note.save()

            # Read each source image's file data and write it to storage up front,
            # then bulk_create() all of this note's NotesImage rows in one INSERT
            # instead of one save() per image - unlike Note, NotesImage has no
            # save()-time business logic, so this is safe to batch.
            new_images = []

            for img in source_note.images.all():
                if not img.image:
                    continue

                old_url = img.image.url
                filename = os.path.basename(img.image.name)

                try:
                    img.image.open('rb')
                    data = img.image.read()
                finally:
                    img.image.close()

                new_img = common.models.NotesImage(note=new_note, user=img.user)
                # save=False: still writes the file to storage (and assigns the
                # resulting name/url), but defers the NotesImage row itself to
                # the bulk_create() below
                new_img.image.save(filename, ContentFile(data), save=False)
                new_images.append((old_url, new_img))

            if new_images:
                common.models.NotesImage.objects.bulk_create([
                    new_img for _, new_img in new_images
                ])

                content_updated = False

                for old_url, new_img in new_images:
                    if old_url in new_note.content:
                        new_note.content = new_note.content.replace(
                            old_url, new_img.image.url
                        )
                        content_updated = True

                if content_updated:
                    new_note.save()

    @property
    def primary_note(self):
        """Return the primary note for this model instance, if it exists."""
        return self.notes_list.all().order_by('-primary').first()

    def get_note(self, title: Optional[str] = None):
        """Return a Note instance for the given note title.

        Arguments:
            title: Title of the note to retrieve. If None, returns the primary note (if it exists)
        """
        notes = self.notes_list.all().order_by('-primary')

        if title:
            notes = notes.filter(title=title)

        return notes.first()

    def check_note_delete(self, note) -> bool:
        """Run a check to determine if the provided note can be deleted.

        The default implementation always returns True, but this can be overridden in the implementing class.
        """
        return True

    def check_note_save(self, note) -> bool:
        """Run a check to determine if the provided note can be saved.

        The default implementation always returns True, but this can be overridden in the implementing class.
        """
        return True


class InvenTreeAttachmentMixin(ModelFeatureMixin, InvenTreePermissionCheckMixin):
    """Provides an abstracted class for managing file attachments.

    Links the implementing model to the common.models.Attachment table,
    and provides the following methods:

    - attachments: Return a queryset containing all attachments for this model
    """

    MODEL_FEATURE = 'org.inventree.i.modelfeatures.attachments'

    def delete(self, *args, **kwargs):
        """Handle the deletion of a model instance.

        Before deleting the model instance, delete any associated attachments.
        """
        for attachment in list(self.attachments.all()):
            attachment.delete()

        super().delete(*args, **kwargs)

    @property
    @report.mixins.report_attribute()
    def attachments(self) -> report.mixins.QuerySet:
        """Return a queryset containing all attachments for this model."""
        return self.attachments_for_model().filter(model_id=self.pk)

    def attachments_for_model(self) -> QuerySet:
        """Return all attachments for this model class."""
        from common.models import Attachment

        model_type = self.__class__.__name__.lower()
        return Attachment.objects.filter(model_type=model_type)

    def create_attachment(self, attachment=None, link=None, comment='', **kwargs):
        """Create an attachment / link for this model."""
        from common.models import Attachment

        kwargs['attachment'] = attachment
        kwargs['link'] = link
        kwargs['comment'] = comment
        kwargs['model_type'] = self.__class__.__name__.lower()
        kwargs['model_id'] = self.pk

        Attachment.objects.create(**kwargs)


class InvenTreeImageMixin(ModelFeatureMixin, models.Model):
    """A mixin class for adding image functionality to a model class.

    The following fields are added to any model which implements this mixin:

    - image : An image field for storing an image
    """

    MODEL_FEATURE = 'org.inventree.i.modelfeatures.image'

    IMAGE_RENAME: Callable | None = None

    class Meta:
        """Metaclass options for this mixin.

        Note: abstract must be true, as this is only a mixin, not a separate table
        """

        abstract = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Custom init method for InvenTreeImageMixin to ensure IMAGE_RENAME is implemented."""
        if self.IMAGE_RENAME is None:
            raise NotImplementedError(
                'IMAGE_RENAME must be implemented in the model class'
            )
        super().__init__(*args, **kwargs)

    def rename_image(self, filename):
        """Rename the uploaded image file using the IMAGE_RENAME function."""
        return self.IMAGE_RENAME(filename)

    image = StdImageField(
        upload_to=rename_image,
        null=True,
        blank=True,
        variations={'thumbnail': (128, 128), 'preview': (256, 256)},
        delete_orphans=False,
        verbose_name=_('Image'),
        validators=[common.validators.validate_uploaded_file],
    )

    def get_image_url(self) -> str:
        """Return the URL of the image for this object."""
        if self.image:
            return InvenTree.helpers.getMediaUrl(self.image)
        return InvenTree.helpers.getBlankImage()

    @property
    @report.mixins.report_attribute()
    def image_url(self) -> str:
        """Return the URL of the image for this object."""
        return self.get_image_url()

    def get_thumbnail_url(self) -> str:
        """Return the URL of the image thumbnail for this object."""
        if self.image:
            return InvenTree.helpers.getMediaUrl(self.image, 'thumbnail')
        return InvenTree.helpers.getBlankThumbnail()

    @property
    @report.mixins.report_attribute()
    def thumbnail_url(self) -> str:
        """Return the URL of the image thumbnail for this object."""
        return self.get_thumbnail_url()


class InvenTreePathStringMixin(models.Model):
    """Mixin class for adding a 'pathstring' field to a model class.

    The pathstring is a string representation of the path to this model instance,
    which can be used for display purposes.

    The pathstring is automatically generated when the model instance is saved.
    """

    # Field to use for constructing a "pathstring" for the tree
    PATH_FIELD = 'name'

    # Extra fields to include in the get_path result. E.g. icon
    EXTRA_PATH_FIELDS = []

    class Meta:
        """Metaclass options for this mixin.

        Note: abstract must be true, as this is only a mixin, not a separate table
        """

        abstract = True

    name = models.CharField(
        blank=False, max_length=100, verbose_name=_('Name'), help_text=_('Name')
    )

    description = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Description (optional)'),
    )

    # When a category is deleted, graft the children onto its parent
    parent = TreeForeignKey(
        'self',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name='parent',
        related_name='children',
    )

    # The 'pathstring' field is calculated each time the model is saved
    pathstring = models.CharField(
        blank=True, max_length=250, verbose_name=_('Path'), help_text=_('Path')
    )

    def save(self, *args, **kwargs):
        """Update the pathstring field when saving the model instance."""
        old_pathstring = self.pathstring

        # Rebuild upper first, to ensure the lower nodes are updated correctly
        super().save(*args, **kwargs)

        # Determine if a tree rebuild task was already triggered by this save
        # (e.g. if the node was re-parented) - if so, the pathstring values
        # for any lower nodes are updated by that task
        rebuild_offloaded = getattr(self, '_tree_rebuild_offloaded', False)

        # Ensure that the pathstring is correctly constructed
        pathstring = self.construct_pathstring(refresh=True)

        if pathstring != old_pathstring:
            kwargs.pop('force_insert', None)
            kwargs['force_update'] = True

            self.pathstring = pathstring
            super().save(*args, **kwargs)

            # Update the pathstring values for any lower nodes,
            # by offloading the update to the background worker
            if not rebuild_offloaded and self.get_descendant_count() > 0:
                self.__class__.offload_tree_rebuild([self.tree_id])  # ty: ignore[invalid-attribute-access]

    def delete(self, *args, **kwargs):
        """Custom delete method for PathStringMixin.

        - Before deleting the object, update the pathstring for any child nodes.
        - Then, delete the object.
        """
        # Ensure that we have the latest version of the database object
        try:
            self.refresh_from_db()
        except self.__class__.DoesNotExist:
            # If the object no longer exists, raise a ValidationError
            raise ValidationError(
                'Object %s of type %s no longer exists', str(self), str(self.__class__)
            )

        # Store the node ID values for lower nodes, before we delete this one
        lower_nodes = self.get_lower_nodes()

        # Delete this node - after which we expect the tree structure will be updated
        super().delete(*args, **kwargs)

        # Rebuild the pathstring for lower nodes
        self.rebuild_lower_nodes(lower_nodes)

    def __str__(self):
        """String representation of a category is the full path to that category."""
        return f'{self.pathstring} - {self.description}'

    def get_lower_nodes(self) -> list[int]:
        """Return a list of all lower nodes in the tree."""
        return list(
            self.get_descendants(include_self=False).values_list('pk', flat=True)
        )

    def rebuild_lower_nodes(self, lower_nodes: list[int]):
        """Rebuild the pathstring for lower nodes in the tree.

        - This is used when the pathstring for this node is updated, and we need to update all lower nodes.
        - We use a bulk-update to update the pathstring for all lower nodes in the tree.
        """
        nodes = self.__class__.objects.filter(pk__in=lower_nodes)

        nodes_to_update = []

        for node in nodes:
            new_path = node.construct_pathstring()

            if new_path != node.pathstring:
                node.pathstring = new_path
                nodes_to_update.append(node)

        if len(nodes_to_update) > 0:
            self.__class__.objects.bulk_update(nodes_to_update, ['pathstring'])

    @classmethod
    def rebuild_tree_pathstring_values(cls, tree_ids) -> None:
        """Rebuild the 'pathstring' values for all nodes in the specified trees.

        Each tree is processed in a single pass:
        the pathstring for each node is constructed from its parent node,
        and any changed values are written back in a single bulk update.
        """
        tree_nodes = list(cls.objects.filter(tree_id__in=tree_ids))
        node_map = {node.pk: node for node in tree_nodes}

        # Cache of node ID -> list of path elements (from the top level down)
        path_cache: dict[int, list[str]] = {}

        def path_names(node) -> list[str]:
            """Construct the path (list of names) for a node, via its parent chain."""
            if node.pk in path_cache:
                return path_cache[node.pk]

            names = [str(getattr(node, cls.PATH_FIELD, node.pk))]

            if node.parent_id:
                parent = node_map.get(node.parent_id)

                if parent is None:
                    # Parent node exists outside the selected trees
                    parent = cls.objects.get(pk=node.parent_id)
                    node_map[node.parent_id] = parent

                names = [*path_names(parent), *names]

            path_cache[node.pk] = names
            return names

        nodes_to_update = []

        for node in tree_nodes:
            pathstring = InvenTree.helpers.constructPathString(path_names(node))

            if pathstring != node.pathstring:
                node.pathstring = pathstring
                nodes_to_update.append(node)

        if len(nodes_to_update) > 0:
            cls.objects.bulk_update(nodes_to_update, ['pathstring'], batch_size=250)

    def construct_pathstring(self, refresh: bool = False) -> str:
        """Construct the pathstring for this tree node.

        Arguments:
            refresh: If True, force a refresh of the model instance
        """
        if refresh:
            # Refresh the model instance from the database
            self.refresh_from_db()

        return InvenTree.helpers.constructPathString([
            getattr(item, self.PATH_FIELD, item.pk) for item in self.path
        ])

    def validate_unique(self, exclude=None):
        """Validate that this tree instance satisfies our uniqueness requirements.

        Note that a 'unique_together' requirement for ('name', 'parent') is insufficient,
        as it ignores cases where parent=None (i.e. top-level items)
        """
        super().validate_unique(exclude)

        results = self.__class__.objects.filter(
            name=self.name, parent=self.parent
        ).exclude(pk=self.pk)

        if results.exists():
            raise ValidationError(
                _('Duplicate names cannot exist under the same parent')
            )

    @property
    @report.mixins.report_attribute()
    def parentpath(self) -> list:
        """Construct the parent path of this tree node.

        Returns:
            List of category names from the top level to the parent of this category
        """
        return list(self.get_ancestors())

    @property
    @report.mixins.report_attribute()
    def path(self) -> list:
        """Construct the complete part of this tree node.

        e.g. ["Top", "Second", "Third", "This"]

        Returns:
            List of category names from the top level to this category
        """
        return [*self.parentpath, self]

    def get_path(self) -> list:
        """Return a list of element in the item tree.

        Contains the full path to this item, with each entry containing the following data:

        {
            pk: <pk>,
            name: <name>,
        }
        """
        return [
            {
                'pk': item.pk,
                'name': getattr(item, self.PATH_FIELD, item.pk),
                **{k: getattr(item, k, None) for k in self.EXTRA_PATH_FIELDS},
            }
            for item in self.path
        ]


class InvenTreeTagsMixin(ModelFeatureMixin, models.Model):
    """A mixin class for adding tag functionality to a model class.

    The following fields are added to any model which implements this mixin:

    - tags : A text field for storing comma-separated tags
    """

    MODEL_FEATURE = 'org.inventree.i.modelfeatures.tags'

    class Meta:
        """Metaclass options for this mixin.

        Note: abstract must be true, as this is only a mixin, not a separate table
        """

        abstract = True

    tags = TaggableManager(blank=True)


class InvenTreeBarcodeMixin(ModelFeatureMixin, models.Model):
    """A mixin class for adding barcode functionality to a model class.

    Two types of barcodes are supported:

    - Internal barcodes (QR codes using a strictly defined format)
    - External barcodes (assign third party barcode data to a model instance)

    The following fields are added to any model which implements this mixin:

    - barcode_data : Raw data associated with an assigned barcode
    - barcode_hash : A 'hash' of the assigned barcode data used to improve matching

    The barcode_model_type_code() classmethod must be implemented in the model class.
    """

    MODEL_FEATURE = 'org.inventree.i.modelfeatures.barcode'

    class Meta:
        """Metaclass options for this mixin.

        Note: abstract must be true, as this is only a mixin, not a separate table
        """

        abstract = True

    barcode_data = models.CharField(
        blank=True,
        max_length=500,
        verbose_name=_('Barcode Data'),
        help_text=_('Third party barcode data'),
    )

    barcode_hash = models.CharField(
        blank=True,
        max_length=128,
        verbose_name=_('Barcode Hash'),
        help_text=_('Unique hash of barcode data'),
    )

    @classmethod
    def barcode_model_type(cls):
        """Return the model 'type' for creating a custom QR code."""
        # By default, use the name of the class
        return cls.__name__.lower()

    @classmethod
    def barcode_model_type_code(cls):
        r"""Return a 'short' code for the model type.

        This is used to generate a efficient QR code for the model type.
        It is expected to match this pattern: [0-9A-Z $%*+-.\/:]{2}

        Note: Due to the shape constraints (45**2=2025 different allowed codes)
        this needs to be explicitly implemented in the model class to avoid collisions.
        """
        raise NotImplementedError(
            'barcode_model_type_code() must be implemented in the model class'
        )

    def format_barcode(self, **kwargs):
        """Return a string for formatting a QR code for this model instance."""
        from plugin.base.barcodes.helper import generate_barcode

        return generate_barcode(self)

    def format_matched_response(self, user, **kwargs):
        """Format a standard response for a matched barcode."""
        # Check permission for this object
        from users.permissions import check_user_permission

        if not check_user_permission(user, self, 'view'):
            raise PermissionDenied(
                _('User does not have permission to view this model')
            )

        data = {'pk': self.pk}

        if hasattr(self, 'get_api_url'):
            api_url = self.get_api_url()
            data['api_url'] = api_url = f'{api_url}{self.pk}/'

            # Attempt to serialize the object too
            try:
                match = resolve(api_url)
                view_class = match.func.view_class
                serializer_class = view_class.serializer_class

                kwargs = {}

                # Pass the requesting user through, so that field-level permission
                # checks (e.g. role-gated or nested OptionalFields) are applied
                from InvenTree.serializers import FilterableSerializerMixin

                if issubclass(serializer_class, FilterableSerializerMixin):
                    kwargs[serializer_class.PERMISSION_USER_KWARG] = user

                serializer = serializer_class(self, **kwargs)
                data['instance'] = serializer.data
            except Exception:
                pass

        if hasattr(self, 'get_absolute_url'):
            data['web_url'] = self.get_absolute_url()

        return data

    @property
    @report.mixins.report_attribute()
    def barcode(self) -> str:
        """Format a minimal barcode string (e.g. for label printing)."""
        return self.format_barcode()

    @classmethod
    def lookup_barcode(cls, barcode_hash: str) -> models.Model:
        """Check if a model instance exists with the specified third-party barcode hash."""
        return cls.objects.filter(barcode_hash=barcode_hash).first()

    def assign_barcode(
        self,
        barcode_hash: Optional[str] = None,
        barcode_data: Optional[str] = None,
        raise_error: bool = True,
        save: bool = True,
    ):
        """Assign an external (third-party) barcode to this object."""
        # Must provide either barcode_hash or barcode_data
        if barcode_hash is None and barcode_data is None:
            raise ValueError("Provide either 'barcode_hash' or 'barcode_data'")

        # If barcode_hash is not provided, create from supplier barcode_data
        if barcode_hash is None and barcode_data is not None:
            barcode_hash = InvenTree.helpers.hash_barcode(barcode_data)

        # Check for existing item
        if self.__class__.lookup_barcode(barcode_hash) is not None:
            if raise_error:
                raise ValidationError(_('Existing barcode found'))
            else:
                return False

        if barcode_data is not None:
            self.barcode_data = barcode_data

        self.barcode_hash = barcode_hash

        if save:
            self.save()

        return True

    def unassign_barcode(self):
        """Unassign custom barcode from this model."""
        self.barcode_data = ''
        self.barcode_hash = ''

        self.save()
