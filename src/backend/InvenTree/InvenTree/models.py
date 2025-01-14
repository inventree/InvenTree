"""Generic models which provide extra functionality over base Django model types."""

from datetime import datetime
from string import Formatter

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext_lazy as _

import structlog
from django_q.models import Task
from error_report.models import Error
from mptt.exceptions import InvalidMove
from mptt.models import MPTTModel, TreeForeignKey

import common.settings
import InvenTree.fields
import InvenTree.format
import InvenTree.helpers
import InvenTree.helpers_model

logger = structlog.get_logger('inventree')


class DiffMixin:
    """Mixin which can be used to determine which fields have changed, compared to the instance saved to the database."""

    def get_db_instance(self):
        """Return the instance of the object saved in the database.

        Returns:
            object: Instance of the object saved in the database
        """
        if self.pk:
            try:
                return self.__class__.objects.get(pk=self.pk)
            except self.__class__.DoesNotExist:
                pass

        return None

    def get_field_deltas(self):
        """Return a dict of field deltas.

        Compares the current instance with the instance saved in the database,
        and returns a dict of fields which have changed.

        Returns:
            dict: Dict of field deltas
        """
        db_instance = self.get_db_instance()

        if db_instance is None:
            return {}

        deltas = {}

        for field in self._meta.fields:
            if field.name == 'id':
                continue

            if getattr(self, field.name) != getattr(db_instance, field.name):
                deltas[field.name] = {
                    'old': getattr(db_instance, field.name),
                    'new': getattr(self, field.name),
                }

        return deltas

    def has_field_changed(self, field_name):
        """Determine if a particular field has changed."""
        return field_name in self.get_field_deltas()


class PluginValidationMixin(DiffMixin):
    """Mixin class which exposes the model instance to plugin validation.

    Any model class which inherits from this mixin will be exposed to the plugin validation system.
    """

    def run_plugin_validation(self):
        """Throw this model against the plugin validation interface."""
        from plugin.registry import registry

        deltas = self.get_field_deltas()

        for plugin in registry.with_mixin('validation'):
            try:
                if plugin.validate_model_instance(self, deltas=deltas) is True:
                    return
            except ValidationError as exc:
                raise exc
            except Exception:
                # Log the exception to the database
                import InvenTree.exceptions

                InvenTree.exceptions.log_error(
                    f'plugins.{plugin.slug}.validate_model_instance'
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

    def delete(self):
        """Run plugin validation on model delete.

        Allows plugins to prevent model instances from being deleted.

        Note: Each plugin may raise a ValidationError to prevent deletion.
        """
        from InvenTree.exceptions import log_error
        from plugin.registry import registry

        for plugin in registry.with_mixin('validation'):
            try:
                plugin.validate_model_deletion(self)
            except ValidationError as e:
                # Plugin might raise a ValidationError to prevent deletion
                raise e
            except Exception:
                log_error('plugin.validate_model_deletion')
                continue

        super().delete()


class MetadataMixin(models.Model):
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

    def save(self, *args, **kwargs):
        """Save the model instance, and perform validation on the metadata field."""
        self.validate_metadata()
        super().save(*args, **kwargs)

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


class DataImportMixin:
    """Model mixin class which provides support for 'data import' functionality.

    Models which implement this mixin should provide information on the fields available for import
    """

    # TODO: This mixin should be removed after https://github.com/inventree/InvenTree/pull/6911 is implemented
    # TODO: This approach to data import functionality is *outdated*

    # Define a map of fields available for import
    IMPORT_FIELDS = {}

    @classmethod
    def get_import_fields(cls):
        """Return all available import fields.

        Where information on a particular field is not explicitly provided,
        introspect the base model to (attempt to) find that information.
        """
        fields = cls.IMPORT_FIELDS

        for name, field in fields.items():
            # Attempt to extract base field information from the model
            base_field = None

            for f in cls._meta.fields:
                if f.name == name:
                    base_field = f
                    break

            if base_field:
                if 'label' not in field:
                    field['label'] = base_field.verbose_name

                if 'help_text' not in field:
                    field['help_text'] = base_field.help_text

            fields[name] = field

        return fields

    @classmethod
    def get_required_import_fields(cls):
        """Return all *required* import fields."""
        fields = {}

        for name, field in cls.get_import_fields().items():
            required = field.get('required', False)

            if required:
                fields[name] = field

        return fields


class ReferenceIndexingMixin(models.Model):
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

        reference = latest.reference.strip

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


class InvenTreeModel(PluginValidationMixin, models.Model):
    """Base class for InvenTree models, which provides some common functionality.

    Includes the following mixins by default:

    - PluginValidationMixin: Provides a hook for plugins to validate model instances
    """

    class Meta:
        """Metaclass options."""

        abstract = True


class InvenTreeMetadataModel(MetadataMixin, InvenTreeModel):
    """Base class for an InvenTree model which includes a metadata field."""

    class Meta:
        """Metaclass options."""

        abstract = True


class InvenTreeAttachmentMixin:
    """Provides an abstracted class for managing file attachments.

    Links the implementing model to the common.models.Attachment table,
    and provides the following methods:

    - attachments: Return a queryset containing all attachments for this model
    """

    def delete(self):
        """Handle the deletion of a model instance.

        Before deleting the model instance, delete any associated attachments.
        """
        self.attachments.all().delete()
        super().delete()

    @property
    def attachments(self):
        """Return a queryset containing all attachments for this model."""
        return self.attachments_for_model().filter(model_id=self.pk)

    @classmethod
    def check_attachment_permission(cls, permission, user) -> bool:
        """Check if the user has permission to perform the specified action on the attachment.

        The default implementation runs a permission check against *this* model class,
        but this can be overridden in the implementing class if required.

        Arguments:
            permission: The permission to check (add / change / view / delete)
            user: The user to check against

        Returns:
            bool: True if the user has permission, False otherwise
        """
        perm = f'{cls._meta.app_label}.{permission}_{cls._meta.model_name}'
        return user.has_perm(perm)

    def attachments_for_model(self):
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


class InvenTreeTree(MetadataMixin, PluginValidationMixin, MPTTModel):
    """Provides an abstracted self-referencing tree model for data categories.

    - Each Category has one parent Category, which can be blank (for a top-level Category).
    - Each Category can have zero-or-more child Category(y/ies)

    Attributes:
        name: brief name
        description: longer form description
        parent: The item immediately above this one. An item with a null parent is a top-level item
    """

    # How items (not nodes) are hooked into the tree
    # e.g. for StockLocation, this value is 'location'
    ITEM_PARENT_KEY = None

    # Extra fields to include in the get_path result. E.g. icon
    EXTRA_PATH_FIELDS = []

    class Meta:
        """Metaclass defines extra model properties."""

        abstract = True

    class MPTTMeta:
        """Set insert order."""

        order_insertion_by = ['name']

    def delete(self, delete_children=False, delete_items=False):
        """Handle the deletion of a tree node.

        1. Update nodes and items under the current node
        2. Delete this node
        3. Rebuild the model tree
        4. Rebuild the path for any remaining lower nodes
        """
        tree_id = self.tree_id if self.parent else None

        # Ensure that we have the latest version of the database object
        try:
            self.refresh_from_db()
        except self.__class__.DoesNotExist:
            # If the object no longer exists, raise a ValidationError
            raise ValidationError(
                'Object %s of type %s no longer exists', str(self), str(self.__class__)
            )

        # Cache node ID values for lower nodes, before we delete this one
        lower_nodes = list(
            self.get_descendants(include_self=False).values_list('pk', flat=True)
        )

        # 1. Update nodes and items under the current node
        self.handle_tree_delete(
            delete_children=delete_children, delete_items=delete_items
        )

        # 2. Delete *this* node
        super().delete()

        # 3. Update the tree structure
        if tree_id:
            self.__class__.objects.partial_rebuild(tree_id)
        else:
            self.__class__.objects.rebuild()

        # 4. Rebuild the path for any remaining lower nodes
        nodes = self.__class__.objects.filter(pk__in=lower_nodes)

        nodes_to_update = []

        for node in nodes:
            new_path = node.construct_pathstring()

            if new_path != node.pathstring:
                node.pathstring = new_path
                nodes_to_update.append(node)

        if len(nodes_to_update) > 0:
            self.__class__.objects.bulk_update(nodes_to_update, ['pathstring'])

    def handle_tree_delete(self, delete_children=False, delete_items=False):
        """Delete a single instance of the tree, based on provided kwargs.

        Removing a tree "node" from the database must be considered carefully,
        based on what the user intends for any items which exist *under* that node.

        - "children" are any nodes which exist *under* this node (e.g. PartCategory)
        - "items" are any items which exist *under* this node (e.g. Part)

        Arguments:
            delete_children: If True, delete all child items
            delete_items: If True, delete all items associated with this node

        There are multiple scenarios we can consider here:

        A) delete_children = True and delete_items = True
        B) delete_children = True and delete_items = False
        C) delete_children = False and delete_items = True
        D) delete_children = False and delete_items = False
        """
        child_nodes = self.get_descendants(include_self=False)

        # Case A: Delete all child items, and all child nodes.
        # - Delete all items at any lower level
        # - Delete all descendant nodes
        if delete_children and delete_items:
            self.get_items(cascade=True).delete()
            self.delete_nodes(child_nodes)

        # Case B: Delete all child nodes, but move all child items up to the parent
        # - Move all items at any lower level to the parent of this item
        # - Delete all descendant nodes
        elif delete_children and not delete_items:
            self.get_items(cascade=True).update(**{self.ITEM_PARENT_KEY: self.parent})

            self.delete_nodes(child_nodes)

        # Case C: Delete all child items, but keep all child nodes
        # - Remove all items directly associated with this node
        # - Move any direct child nodes up one level
        elif not delete_children and delete_items:
            self.get_items(cascade=False).delete()
            self.get_children().update(parent=self.parent)

        # Case D: Keep all child items, and keep all child nodes
        # - Move all items directly associated with this node up one level
        # - Move any direct child nodes up one level
        elif not delete_children and not delete_items:
            self.get_items(cascade=False).update(**{self.ITEM_PARENT_KEY: self.parent})
            self.get_children().update(parent=self.parent)

    def delete_nodes(self, nodes):
        """Delete  a set of nodes from the tree.

        1. First, set the "parent" value for selected nodes to None
        2. Then, perform bulk deletion of selected nodes

        Step 1. is required because we cannot guarantee the order-of-operations in the db backend

        Arguments:
            nodes: A queryset of nodes to delete
        """
        nodes.update(parent=None)
        nodes.delete()

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
            raise ValidationError({
                'name': _('Duplicate names cannot exist under the same parent')
            })

    def api_instance_filters(self):
        """Instance filters for InvenTreeTree models."""
        return {'parent': {'exclude_tree': self.pk}}

    def construct_pathstring(self):
        """Construct the pathstring for this tree node."""
        return InvenTree.helpers.constructPathString([item.name for item in self.path])

    def save(self, *args, **kwargs):
        """Custom save method for InvenTreeTree abstract model."""
        try:
            super().save(*args, **kwargs)
        except InvalidMove:
            # Provide better error for parent selection
            raise ValidationError({'parent': _('Invalid choice')})

        # Re-calculate the 'pathstring' field
        pathstring = self.construct_pathstring()

        if pathstring != self.pathstring:
            if 'force_insert' in kwargs:
                del kwargs['force_insert']

            kwargs['force_update'] = True

            self.pathstring = pathstring
            super().save(*args, **kwargs)

            # Update the pathstring for any child nodes
            lower_nodes = self.get_descendants(include_self=False)

            nodes_to_update = []

            for node in lower_nodes:
                new_path = node.construct_pathstring()

                if new_path != node.pathstring:
                    node.pathstring = new_path
                    nodes_to_update.append(node)

            if len(nodes_to_update) > 0:
                self.__class__.objects.bulk_update(nodes_to_update, ['pathstring'])

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

    def get_items(self, cascade=False):
        """Return a queryset of items which exist *under* this node in the tree.

        - For a StockLocation instance, this would be a queryset of StockItem objects
        - For a PartCategory instance, this would be a queryset of Part objects

        The default implementation returns an empty list
        """
        raise NotImplementedError(f'items() method not implemented for {type(self)}')

    def getUniqueParents(self):
        """Return a flat set of all parent items that exist above this node.

        If any parents are repeated (which would be very bad!), the process is halted
        """
        return self.get_ancestors()

    def getUniqueChildren(self, include_self=True):
        """Return a flat set of all child items that exist under this node.

        If any child items are repeated, the repetitions are omitted.
        """
        return self.get_descendants(include_self=include_self)

    @property
    def has_children(self):
        """True if there are any children under this item."""
        return self.getUniqueChildren(include_self=False).count() > 0

    def getAcceptableParents(self):
        """Returns a list of acceptable parent items within this model Acceptable parents are ones which are not underneath this item.

        Setting the parent of an item to its own child results in recursion.
        """
        contents = ContentType.objects.get_for_model(type(self))

        available = contents.get_all_objects_for_this_type()

        # List of child IDs
        children = self.getUniqueChildren()

        acceptable = [None]

        for a in available:
            if a.id not in children:
                acceptable.append(a)

        return acceptable

    @property
    def parentpath(self):
        """Get the parent path of this category.

        Returns:
            List of category names from the top level to the parent of this category
        """
        return list(self.get_ancestors())

    @property
    def path(self):
        """Get the complete part of this category.

        e.g. ["Top", "Second", "Third", "This"]

        Returns:
            List of category names from the top level to this category
        """
        return [*self.parentpath, self]

    def get_path(self):
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
                'name': item.name,
                **{k: getattr(item, k, None) for k in self.EXTRA_PATH_FIELDS},
            }
            for item in self.path
        ]

    def __str__(self):
        """String representation of a category is the full path to that category."""
        return f'{self.pathstring} - {self.description}'


class InvenTreeNotesMixin(models.Model):
    """A mixin class for adding notes functionality to a model class.

    The following fields are added to any model which implements this mixin:

    - notes : A text field for storing notes
    """

    class Meta:
        """Metaclass options for this mixin.

        Note: abstract must be true, as this is only a mixin, not a separate table
        """

        abstract = True

    def delete(self):
        """Custom delete method for InvenTreeNotesMixin.

        - Before deleting the object, check if there are any uploaded images associated with it.
        - If so, delete the notes first
        """
        from common.models import NotesImage

        images = NotesImage.objects.filter(
            model_type=self.__class__.__name__.lower(), model_id=self.pk
        )

        if images.exists():
            logger.info(
                'Deleting %s uploaded images associated with %s <%s>',
                images.count(),
                self.__class__.__name__,
                self.pk,
            )

            images.delete()

        super().delete()

    notes = InvenTree.fields.InvenTreeNotesField(
        verbose_name=_('Notes'), help_text=_('Markdown notes (optional)')
    )


class InvenTreeBarcodeMixin(models.Model):
    """A mixin class for adding barcode functionality to a model class.

    Two types of barcodes are supported:

    - Internal barcodes (QR codes using a strictly defined format)
    - External barcodes (assign third party barcode data to a model instance)

    The following fields are added to any model which implements this mixin:

    - barcode_data : Raw data associated with an assigned barcode
    - barcode_hash : A 'hash' of the assigned barcode data used to improve matching

    The barcode_model_type_code() classmethod must be implemented in the model class.
    """

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

        Note: Due to the shape constrains (45**2=2025 different allowed codes)
        this needs to be explicitly implemented in the model class to avoid collisions.
        """
        raise NotImplementedError(
            'barcode_model_type_code() must be implemented in the model class'
        )

    def format_barcode(self, **kwargs):
        """Return a JSON string for formatting a QR code for this model instance."""
        from plugin.base.barcodes.helper import generate_barcode

        return generate_barcode(self)

    def format_matched_response(self):
        """Format a standard response for a matched barcode."""
        data = {'pk': self.pk}

        if hasattr(self, 'get_api_url'):
            api_url = self.get_api_url()
            data['api_url'] = f'{api_url}{self.pk}/'

        if hasattr(self, 'get_absolute_url'):
            data['web_url'] = self.get_absolute_url()

        return data

    @property
    def barcode(self):
        """Format a minimal barcode string (e.g. for label printing)."""
        return self.format_barcode()

    @classmethod
    def lookup_barcode(cls, barcode_hash):
        """Check if a model instance exists with the specified third-party barcode hash."""
        return cls.objects.filter(barcode_hash=barcode_hash).first()

    def assign_barcode(
        self, barcode_hash=None, barcode_data=None, raise_error=True, save=True
    ):
        """Assign an external (third-party) barcode to this object."""
        # Must provide either barcode_hash or barcode_data
        if barcode_hash is None and barcode_data is None:
            raise ValueError("Provide either 'barcode_hash' or 'barcode_data'")

        # If barcode_hash is not provided, create from supplier barcode_data
        if barcode_hash is None:
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


def notify_staff_users_of_error(instance, label: str, context: dict):
    """Helper function to notify staff users of an error."""
    import common.models
    import common.notifications

    try:
        # Get all staff users
        staff_users = get_user_model().objects.filter(is_staff=True)

        target_users = []

        # Send a notification to each staff user (unless they have disabled error notifications)
        for user in staff_users:
            if common.models.InvenTreeUserSetting.get_setting(
                'NOTIFICATION_ERROR_REPORT', True, user=user
            ):
                target_users.append(user)

        if len(target_users) > 0:
            common.notifications.trigger_notification(
                instance,
                label,
                context=context,
                targets=target_users,
                delivery_methods={common.notifications.UIMessageNotification},
            )

    except Exception as exc:
        # We do not want to throw an exception while reporting an exception!
        logger.error(exc)


@receiver(post_save, sender=Task, dispatch_uid='failure_post_save_notification')
def after_failed_task(sender, instance: Task, created: bool, **kwargs):
    """Callback when a new task failure log is generated."""
    from django.conf import settings

    max_attempts = int(settings.Q_CLUSTER.get('max_attempts', 5))
    n = instance.attempt_count

    # Only notify once the maximum number of attempts has been reached
    if not instance.success and n >= max_attempts:
        try:
            url = InvenTree.helpers_model.construct_absolute_url(
                reverse(
                    'admin:django_q_failure_change', kwargs={'object_id': instance.pk}
                )
            )
        except (ValueError, NoReverseMatch):
            url = ''

        # Function name
        f = instance.func

        notify_staff_users_of_error(
            instance,
            'inventree.task_failure',
            {
                'failure': instance,
                'name': _('Task Failure'),
                'message': _(f"Background worker task '{f}' failed after {n} attempts"),
                'link': url,
            },
        )


@receiver(post_save, sender=Error, dispatch_uid='error_post_save_notification')
def after_error_logged(sender, instance: Error, created: bool, **kwargs):
    """Callback when a server error is logged.

    - Send a UI notification to all users with staff status
    """
    if created:
        try:
            url = InvenTree.helpers_model.construct_absolute_url(
                reverse(
                    'admin:error_report_error_change', kwargs={'object_id': instance.pk}
                )
            )
        except NoReverseMatch:
            url = ''

        notify_staff_users_of_error(
            instance,
            'inventree.error_log',
            {
                'error': instance,
                'name': _('Server Error'),
                'message': _('An error has been logged by the server.'),
                'link': url,
            },
        )
