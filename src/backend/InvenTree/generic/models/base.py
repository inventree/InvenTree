"""Base classes for building models."""

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import QuerySet
from django.db.transaction import TransactionManagementError
from django.utils.translation import gettext_lazy as _

import structlog
from mptt.exceptions import InvalidMove
from mptt.models import MPTTModel

import InvenTree.exceptions
import InvenTree.sentry
from generic.models.internal import ContentTypeMixin
from generic.models.modelmixins import (
    InvenTreeMetadataMixin,
    InvenTreePluginValidationMixin,
)

logger = structlog.get_logger('inventree')


class InvenTreeModel(ContentTypeMixin, InvenTreePluginValidationMixin, models.Model):
    """Base class for InvenTree models, which provides some common functionality.

    Includes the following mixins by default:

    - PluginValidationMixin: Provides a hook for plugins to validate model instances
    """

    class Meta:
        """Metaclass options."""

        abstract = True


class InvenTreeMetadataModel(InvenTreeMetadataMixin, InvenTreeModel):
    """Base class for an InvenTree model which includes a metadata field."""

    class Meta:
        """Metaclass options."""

        abstract = True


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

    @transaction.atomic
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

        # If items are to be deleted, ensure that *all* of them can be deleted,
        # before any changes are made to the database
        if delete_items:
            self.validate_delete_items(cascade=delete_children)

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
        self.__class__.rebuild_trees(trees)

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

        Note: re-parenting uses audited_update(), so that the change is recorded
        for audited models (it falls back to a plain update() otherwise).
        """
        from audit.helpers import audited_update

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
                audited_update(items, **{self.ITEM_PARENT_KEY: parent})
            self.delete_nodes(child_nodes)

        # Case C: Delete all child items, but keep all child nodes
        # - Remove all items directly associated with this node
        # - Move any direct child nodes up one level
        elif not delete_children and delete_items:
            self.delete_items(cascade=False)
            parent = getattr(self, self.NODE_PARENT_KEY, None)
            audited_update(self.get_children(), **{self.NODE_PARENT_KEY: parent})

        # Case D: Keep all child items, and keep all child nodes
        # - Move all items directly associated with this node up one level
        # - Move any direct child nodes up one level
        elif not delete_children and not delete_items:
            parent = getattr(self, self.NODE_PARENT_KEY, None)
            if items := self.get_items(cascade=False):
                audited_update(items, **{self.ITEM_PARENT_KEY: parent})
            audited_update(self.get_children(), **{self.NODE_PARENT_KEY: parent})

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

        # Flag to indicate that a tree rebuild task was triggered by this save
        self._tree_rebuild_offloaded = False

        if len(trees) > 0:
            # Offload the tree rebuild(s) to the background worker.
            # Note that repeated calls are de-duplicated (per tree),
            # so a bulk operation results in a single rebuild per affected tree.
            ran_sync = self.__class__.offload_tree_rebuild(trees)
            self._tree_rebuild_offloaded = True

            if ran_sync:
                # The tree was rebuilt synchronously, so refresh the instance
                try:
                    self.refresh_from_db()
                except TransactionManagementError:
                    # If we are inside a transaction block, we cannot refresh from db
                    pass
                except Exception as e:
                    # Any other error is unexpected
                    InvenTree.sentry.report_exception(e)
                    InvenTree.exceptions.log_error(f'{self.__class__.__name__}.save')

    @classmethod
    def offload_tree_rebuild(cls, tree_ids) -> bool:
        """Offload a rebuild of the specified trees to the background worker.

        - The tree structure (and pathstring values, where applicable) are rebuilt for each tree
        - If the background worker is not running, the rebuild is performed synchronously
        - Identical pending tasks are skipped, so repeated calls (e.g. during a bulk
          operation) result in (at most) a single queued rebuild per affected tree

        Returns:
            bool: True if any rebuild was performed synchronously (in the calling thread)
        """
        from InvenTree.tasks import offload_task

        ran_sync = False

        for tree_id in tree_ids:
            if tree_id:
                result = offload_task(
                    'InvenTree.tasks.rebuild_model_tree', cls._meta.label_lower, tree_id
                )

                if result is True:
                    # offload_task returns True if the task ran synchronously
                    ran_sync = True

        return ran_sync

    @classmethod
    def rebuild_trees(cls, tree_ids) -> None:
        """Rebuild the specified trees, with fallback to a full rebuild.

        - Perform a partial rebuild for each provided tree_id
        - If any partial rebuild fails, rebuild the entire tree (expensive!!!)
        """
        result = True

        for tree_id in tree_ids:
            if tree_id and not cls.partial_rebuild(tree_id):
                result = False

        if not result:
            # Rebuild the entire tree (expensive!!!)
            cls.objects.rebuild()

    @classmethod
    def partial_rebuild(cls, tree_id: int) -> bool:
        """Perform a partial rebuild of the tree structure.

        If a failure occurs, log the error and return False.
        """
        try:
            cls.objects.partial_rebuild(tree_id)
            return True
        except Exception as e:
            # This is a critical error, explicitly report to sentry
            InvenTree.sentry.report_exception(e)

            InvenTree.exceptions.log_error(f'{cls.__name__}.partial_rebuild')
            logger.exception(
                'Failed to rebuild tree <%s> for %s: %s', tree_id, cls.__name__, e
            )
            return False

    # Maximum number of blocking items to list in a validation error message
    MAX_DELETE_ERRORS = 10

    def validate_delete_items(self, cascade: bool = False):
        """Ensure that all 'items' under this node can be deleted.

        Each item is checked using its own 'check_delete' method (if it has one),
        which applies the same rules as deleting that item individually.

        Arguments:
            cascade: If True, also check items under all child nodes

        Raises:
            ValidationError: If any item cannot be deleted. No changes are made.
        """
        items = self.get_items(cascade=cascade)

        if not items:
            return

        errors = []
        n_blocked = 0

        for item in items:
            check_delete = getattr(item, 'check_delete', None)

            if not check_delete:
                continue

            try:
                check_delete()
            except ValidationError as exc:
                n_blocked += 1

                if len(errors) < self.MAX_DELETE_ERRORS:
                    errors.append(f'{item}: {"; ".join(exc.messages)}')

        if n_blocked > 0:
            msg = _('{n} item(s) cannot be deleted').format(n=n_blocked)

            if n_blocked > len(errors):
                errors.append('...')

            raise ValidationError([msg, *errors])

    def delete_items(self, cascade: bool = False):
        """Delete any 'items' which exist under this node in the tree.

        - Note that an 'item' is an instance of a different model class.
        - Not all tree structures will have items associated with them.
        - Items are deleted in bulk (for performance). The items must first be
          checked with validate_delete_items, which is performed by delete().
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
