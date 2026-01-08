"""Generic models which provide extra functionality over base Django model types."""

from collections.abc import Callable
from datetime import datetime
from string import Formatter
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.db.transaction import TransactionManagementError
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext_lazy as _

import structlog
from django_q.models import Task
from error_report.models import Error
from mptt.exceptions import InvalidMove
from mptt.models import MPTTModel, TreeForeignKey
from stdimage.models import StdImageField

import common.settings
import InvenTree.exceptions
import InvenTree.fields
import InvenTree.format
import InvenTree.helpers
import InvenTree.helpers_model
import InvenTree.sentry

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
        from plugin import PluginMixinEnum, registry

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


class ContentTypeMixin:
    """Mixin class which supports retrieval of the ContentType for a model instance."""

    @classmethod
    def get_content_type(cls):
        """Return the ContentType object associated with this model."""
        from django.contrib.contenttypes.models import ContentType

        return ContentType.objects.get_for_model(cls)


class InvenTreeModel(ContentTypeMixin, PluginValidationMixin, models.Model):
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


class InvenTreePermissionCheckMixin:
    """Provides an abstracted class for managing permissions against related fields."""

    @classmethod
    def check_related_permission(cls, permission, user) -> bool:
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


class InvenTreeParameterMixin(InvenTreePermissionCheckMixin, models.Model):
    """Provides an abstracted class for managing parameters.

    Links the implementing model to the common.models.Parameter table,
    and provides the following methods:
    """

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
    def parameters(self) -> QuerySet:
        """Return a QuerySet containing all the Parameter instances for this model.

        This will return pre-fetched data if available (i.e. in a serializer context).
        """
        # Check the query cache for pre-fetched parameters
        if cache := getattr(self, '_prefetched_objects_cache', None):
            if 'parameters_list' in cache:
                return cache['parameters_list']

        return self.parameters_list.all()

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

        template_ids = [parameter.template.pk for parameter in other.parameters.all()]

        # Remove all conflicting parameters first
        self.parameters_list.filter(template__pk__in=template_ids).delete()

        for parameter in other.parameters.all():
            parameter.pk = None
            parameter.model_id = self.pk
            parameter.model_type = content_type

            parameters.append(parameter)

        if len(parameters) > 0:
            common.models.Parameter.objects.bulk_create(parameters)

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

    def check_parameter_delete(self, parameter):
        """Run a check to determine if the provided parameter can be deleted.

        The default implementation always returns True, but this can be overridden in the implementing class.
        """
        return True

    def check_parameter_save(self, parameter):
        """Run a check to determine if the provided parameter can be saved.

        The default implementation always returns True, but this can be overridden in the implementing class.
        """
        return True


class InvenTreeAttachmentMixin(InvenTreePermissionCheckMixin):
    """Provides an abstracted class for managing file attachments.

    Links the implementing model to the common.models.Attachment table,
    and provides the following methods:

    - attachments: Return a queryset containing all attachments for this model
    """

    def delete(self, *args, **kwargs):
        """Handle the deletion of a model instance.

        Before deleting the model instance, delete any associated attachments.
        """
        self.attachments.all().delete()
        super().delete(*args, **kwargs)

    @property
    def attachments(self) -> QuerySet:
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


class InvenTreeTree(ContentTypeMixin, MPTTModel):
    """Provides an abstracted self-referencing tree model, based on the MPTTModel class.

    Our implementation provides the following key improvements:

    - Allow tracking of separate concepts of "nodes" and "items"
    - Better handling of deletion of nodes and items
    - Ensure tree is correctly rebuilt after deletion and other operations
    - Improved protection against recursive tree structures
    """

    # How each node reference its parent object
    NODE_PARENT_KEY = 'parent'

    # How items (not nodes) are hooked into the tree
    # e.g. for StockLocation, this value is 'location'
    ITEM_PARENT_KEY = None

    class Meta:
        """Metaclass defines extra model properties."""

        abstract = True

    class MPTTMeta:
        """MPTT metaclass options."""

        order_insertion_by = ['name']

    def delete(self, *args, **kwargs):
        """Handle the deletion of a tree node.

        kwargs:
            delete_children: If True, delete all child nodes (otherwise, point to the parent of this node)
            delete_items: If True, delete all items associated with this node (otherwise, point to the parent of this node)

        Order of operations:
            1. Update nodes and items under the current node
            2. Delete this node
            3. Rebuild the model tree
        """
        delete_children = kwargs.pop('delete_children', False)
        delete_items = kwargs.pop('delete_items', False)

        # Ensure that we have the latest version of the database object
        try:
            self.refresh_from_db()
        except self.__class__.DoesNotExist:
            # If the object no longer exists, raise a ValidationError
            raise ValidationError(
                'Object %s of type %s no longer exists', str(self), str(self.__class__)
            )

        tree_id = self.tree_id
        parent = getattr(self, self.NODE_PARENT_KEY, None)

        # When deleting a top level node with multiple children,
        # we need to assign a new tree_id to each child node
        # otherwise they will all have the same tree_id (which is not allowed)
        lower_trees = []

        if not parent:  # No parent, which means this is a top-level node
            for child in self.get_children():
                # Store a flattened list of node IDs for each of the lower trees
                nodes = list(
                    child
                    .get_descendants(include_self=True)
                    .values_list('pk', flat=True)
                    .distinct()
                )
                lower_trees.append(nodes)

        # 1. Update nodes and items under the current node
        self.handle_tree_delete(
            delete_children=delete_children, delete_items=delete_items
        )

        # 2. Delete *this* node
        super().delete(*args, **kwargs)

        # A set of tree_id values which need to be rebuilt
        trees = set()

        if tree_id:
            # If this node had a tree_id, we need to rebuild that tree
            trees.add(tree_id)

        # Did we delete a top-level node?
        next_tree_id = self.getNextTreeID()

        # If there is only one sub-tree, it can retain the same tree_id value
        for tree in lower_trees[1:]:
            # Bulk update the tree_id for all lower nodes
            lower_nodes = self.__class__.objects.filter(pk__in=tree)
            lower_nodes.update(tree_id=next_tree_id)
            trees.add(next_tree_id)
            next_tree_id += 1

        # 3. Rebuild the model tree(s) as required
        #  - If any partial rebuilds fail, we will rebuild the entire tree

        result = True

        for tree_id in trees:
            if tree_id:
                if not self.partial_rebuild(tree_id):
                    result = False

        if not result:
            # Rebuild the entire tree (expensive!!!)
            self.__class__.objects.rebuild()

    def handle_tree_delete(self, delete_children=False, delete_items=False):
        """Delete a single instance of the tree, based on provided kwargs.

        Removing a tree "node" from the database must be considered carefully,
        based on what the user intends for any items which exist *under* that node.

        - "children" are any nodes (of the same type) which exist *under* this node (e.g. PartCategory)
        - "items" are any items (of a different type) which exist *under* this node (e.g. Part)

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
            self.delete_items(cascade=True)
            self.delete_nodes(child_nodes)

        # Case B: Delete all child nodes, but move all child items up to the parent
        # - Move all items at any lower level to the parent of this item
        # - Delete all descendant nodes
        elif delete_children and not delete_items:
            if items := self.get_items(cascade=True):
                parent = getattr(self, self.NODE_PARENT_KEY, None)
                items.update(**{self.ITEM_PARENT_KEY: parent})
            self.delete_nodes(child_nodes)

        # Case C: Delete all child items, but keep all child nodes
        # - Remove all items directly associated with this node
        # - Move any direct child nodes up one level
        elif not delete_children and delete_items:
            self.delete_items(cascade=False)
            parent = getattr(self, self.NODE_PARENT_KEY, None)
            self.get_children().update(**{self.NODE_PARENT_KEY: parent})

        # Case D: Keep all child items, and keep all child nodes
        # - Move all items directly associated with this node up one level
        # - Move any direct child nodes up one level
        elif not delete_children and not delete_items:
            parent = getattr(self, self.NODE_PARENT_KEY, None)
            if items := self.get_items(cascade=False):
                items.update(**{self.ITEM_PARENT_KEY: parent})
            self.get_children().update(**{self.NODE_PARENT_KEY: parent})

    def delete_nodes(self, nodes):
        """Delete  a set of nodes from the tree.

        1. First, set the "parent" value for selected nodes to None
        2. Then, perform bulk deletion of selected nodes

        Step 1. is required because we cannot guarantee the order-of-operations in the db backend

        Arguments:
            nodes: A queryset of nodes to delete
        """
        nodes.update(**{self.NODE_PARENT_KEY: None})
        nodes.delete()

    def api_instance_filters(self):
        """Instance filters for InvenTreeTree models."""
        return {self.NODE_PARENT_KEY: {'exclude_tree': self.pk}}

    def save(self, *args, **kwargs):
        """Custom save method for InvenTreeTree abstract model."""
        db_instance = None

        parent = getattr(self, self.NODE_PARENT_KEY, None)

        if not self.tree_id:
            if parent:
                # If we have a parent, use the parent's tree_id
                self.tree_id = parent.tree_id
                self.level = parent.level + 1
            else:
                # Otherwise, we need to generate a new tree_id
                self.tree_id = self.getNextTreeID()

        if self.pk:
            try:
                db_instance = self.get_db_instance()
            except self.__class__.DoesNotExist:
                # If the instance does not exist, we cannot get the db instance
                db_instance = None
        try:
            super().save(*args, **kwargs)
        except InvalidMove:
            # Provide better error for parent selection
            raise ValidationError({self.NODE_PARENT_KEY: _('Invalid choice')})

        trees = set()

        parent = getattr(self, self.NODE_PARENT_KEY, None)

        if db_instance:
            # If the tree_id or parent has changed, we need to rebuild the tree
            if getattr(db_instance, self.NODE_PARENT_KEY) != parent:
                trees.add(db_instance.tree_id)
            if db_instance.tree_id != self.tree_id:
                trees.add(self.tree_id)
                trees.add(db_instance.tree_id)
        elif parent:
            # New instance, so we need to rebuild the tree (if it has a parent)
            trees.add(self.tree_id)

        for tree_id in trees:
            if tree_id:
                self.partial_rebuild(tree_id)

        if len(trees) > 0:
            # A tree update was performed, so we need to refresh the instance
            try:
                self.refresh_from_db()
            except TransactionManagementError:
                # If we are inside a transaction block, we cannot refresh from db
                pass
            except Exception as e:
                # Any other error is unexpected
                InvenTree.sentry.report_exception(e)
                InvenTree.exceptions.log_error(f'{self.__class__.__name__}.save')

    def partial_rebuild(self, tree_id: int) -> bool:
        """Perform a partial rebuild of the tree structure.

        If a failure occurs, log the error and return False.
        """
        try:
            self.__class__.objects.partial_rebuild(tree_id)
            return True
        except Exception as e:
            # This is a critical error, explicitly report to sentry
            InvenTree.sentry.report_exception(e)

            InvenTree.exceptions.log_error(f'{self.__class__.__name__}.partial_rebuild')
            logger.exception(
                'Failed to rebuild tree for %s <%s>: %s',
                self.__class__.__name__,
                self.pk,
                e,
            )
            return False

    def delete_items(self, cascade: bool = False):
        """Delete any 'items' which exist under this node in the tree.

        - Note that an 'item' is an instance of a different model class.
        - Not all tree structures will have items associated with them.
        """
        if items := self.get_items(cascade=cascade):
            items.delete()

    def get_items(self, cascade: bool = False):
        """Return a queryset of items which exist *under* this node in the tree.

        - For a StockLocation instance, this would be a queryset of StockItem objects
        - For a PartCategory instance, this would be a queryset of Part objects

        The default implementation returns None, indicating that no items exist under this node.
        """
        return None

    def getUniqueParents(self) -> QuerySet:
        """Return a flat set of all parent items that exist above this node."""
        return self.get_ancestors()

    def getUniqueChildren(self, include_self=True) -> QuerySet:
        """Return a flat set of all child items that exist under this node."""
        return self.get_descendants(include_self=include_self)

    @property
    def has_children(self) -> bool:
        """True if there are any children under this item."""
        return self.getUniqueChildren(include_self=False).count() > 0

    @classmethod
    def getNextTreeID(cls) -> int:
        """Return the next available tree_id for this model class."""
        instance = cls.objects.order_by('-tree_id').first()

        if instance:
            return instance.tree_id + 1
        else:
            return 1


class PathStringMixin(models.Model):
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

        # Ensure that the pathstring is correctly constructed
        pathstring = self.construct_pathstring(refresh=True)

        if pathstring != old_pathstring:
            kwargs.pop('force_insert', None)
            kwargs['force_update'] = True

            self.pathstring = pathstring
            super().save(*args, **kwargs)

            # Bulk-update any child nodes, if applicable
            lower_nodes = list(
                self.get_descendants(include_self=False).values_list('pk', flat=True)
            )

            self.rebuild_lower_nodes(lower_nodes)

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
        lower_nodes = list(
            self.get_descendants(include_self=False).values_list('pk', flat=True)
        )

        # Delete this node - after which we expect the tree structure will be updated
        super().delete(*args, **kwargs)

        # Rebuild the pathstring for lower nodes
        self.rebuild_lower_nodes(lower_nodes)

    def __str__(self):
        """String representation of a category is the full path to that category."""
        return f'{self.pathstring} - {self.description}'

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
    def parentpath(self) -> list:
        """Get the parent path of this category.

        Returns:
            List of category names from the top level to the parent of this category
        """
        return list(self.get_ancestors())

    @property
    def path(self) -> list:
        """Get the complete part of this category.

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

    def delete(self, *args, **kwargs):
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

        super().delete(*args, **kwargs)

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

    def format_matched_response(self):
        """Format a standard response for a matched barcode."""
        data = {'pk': self.pk}

        if hasattr(self, 'get_api_url'):
            api_url = self.get_api_url()
            data['api_url'] = api_url = f'{api_url}{self.pk}/'

            # Attempt to serialize the object too
            try:
                match = resolve(api_url)
                view_class = match.func.view_class
                serializer_class = view_class.serializer_class
                serializer = serializer_class(self)
                data['instance'] = serializer.data
            except Exception:
                pass

        if hasattr(self, 'get_absolute_url'):
            data['web_url'] = self.get_absolute_url()

        return data

    @property
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


def notify_staff_users_of_error(instance, label: str, context: dict):
    """Helper function to notify staff users of an error."""
    import common.models
    import common.notifications
    from plugin.builtin.integration.core_notifications import InvenTreeUINotifications

    try:
        # Get all staff users
        staff_users = get_user_model().objects.filter(is_active=True, is_staff=True)

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
                delivery_methods={InvenTreeUINotifications},
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


class InvenTreeImageMixin(models.Model):
    """A mixin class for adding image functionality to a model class.

    The following fields are added to any model which implements this mixin:

    - image : An image field for storing an image
    """

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
        return self.IMAGE_RENAME(filename)  # type: ignore

    image = StdImageField(
        upload_to=rename_image,
        null=True,
        blank=True,
        variations={'thumbnail': (128, 128), 'preview': (256, 256)},
        delete_orphans=False,
        verbose_name=_('Image'),
    )

    def get_image_url(self):
        """Return the URL of the image for this object."""
        if self.image:
            return InvenTree.helpers.getMediaUrl(self.image)
        return InvenTree.helpers.getBlankImage()

    def get_thumbnail_url(self) -> str:
        """Return the URL of the image thumbnail for this object."""
        if self.image:
            return InvenTree.helpers.getMediaUrl(self.image, 'thumbnail')
        return InvenTree.helpers.getBlankThumbnail()
