"""Generic models which provide extra functionality over base Django model types."""

import logging
import os
import re
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from error_report.models import Error
from mptt.exceptions import InvalidMove
from mptt.models import MPTTModel, TreeForeignKey

import InvenTree.format
import InvenTree.helpers
from common.models import InvenTreeSetting
from InvenTree.fields import InvenTreeURLField

logger = logging.getLogger('inventree')


def rename_attachment(instance, filename):
    """Function for renaming an attachment file. The subdirectory for the uploaded file is determined by the implementing class.

    Args:
        instance: Instance of a PartAttachment object
        filename: name of uploaded file

    Returns:
        path to store file, format: '<subdir>/<id>/filename'
    """
    # Construct a path to store a file attachment for a given model type
    return os.path.join(instance.getSubdir(), filename)


class DataImportMixin(object):
    """Model mixin class which provides support for 'data import' functionality.

    Models which implement this mixin should provide information on the fields available for import
    """

    # Define a map of fields avaialble for import
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

    @classmethod
    def get_reference_pattern(cls):
        """Returns the reference pattern associated with this model.

        This is defined by a global setting object, specified by the REFERENCE_PATTERN_SETTING attribute
        """

        # By default, we return an empty string
        if cls.REFERENCE_PATTERN_SETTING is None:
            return ''

        return InvenTreeSetting.get_setting(cls.REFERENCE_PATTERN_SETTING, create=False).strip()

    @classmethod
    def get_reference_context(cls):
        """Generate context data for generating the 'reference' field for this class.

        - Returns a python dict object which contains the context data for formatting the reference string.
        - The default implementation provides some default context information
        """

        return {
            'ref': cls.get_next_reference(),
            'date': datetime.now(),
        }

    @classmethod
    def get_most_recent_item(cls):
        """Return the item which is 'most recent'

        In practice, this means the item with the highest reference value
        """

        query = cls.objects.all().order_by('-reference_int', '-pk')

        if query.exists():
            return query.first()
        else:
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
            reference = InvenTree.format.extract_named_group('ref', reference, cls.get_reference_pattern())
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
        """Generate the next 'reference' field based on specified pattern"""

        fmt = cls.get_reference_pattern()
        ctx = cls.get_reference_context()

        reference = None

        attempts = set()

        while reference is None:
            try:
                ref = fmt.format(**ctx)

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
                if recent:
                    reference = recent.reference
                else:
                    reference = ""

        return reference

    @classmethod
    def validate_reference_pattern(cls, pattern):
        """Ensure that the provided pattern is valid"""

        ctx = cls.get_reference_context()

        try:
            info = InvenTree.format.parse_format_string(pattern)
        except Exception:
            raise ValidationError({
                "value": _("Improperly formatted pattern"),
            })

        # Check that only 'allowed' keys are provided
        for key in info.keys():
            if key not in ctx.keys():
                raise ValidationError({
                    "value": _("Unknown format key specified") + f": '{key}'"
                })

        # Check that the 'ref' variable is specified
        if 'ref' not in info.keys():
            raise ValidationError({
                'value': _("Missing required format key") + ": 'ref'"
            })

    @classmethod
    def validate_reference_field(cls, value):
        """Check that the provided 'reference' value matches the requisite pattern"""

        pattern = cls.get_reference_pattern()

        value = str(value).strip()

        if len(value) == 0:
            raise ValidationError(_("Reference field cannot be empty"))

        # An 'empty' pattern means no further validation is required
        if not pattern:
            return

        if not InvenTree.format.validate_string(value, pattern):
            raise ValidationError(_("Reference must match required pattern") + ": " + pattern)

        # Check that the reference field can be rebuild
        cls.rebuild_reference_field(value, validate=True)

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

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
            reference = InvenTree.format.extract_named_group('ref', reference, cls.get_reference_pattern())
        except Exception:
            pass

        reference_int = extract_int(reference)

        if validate:
            if reference_int > models.BigIntegerField.MAX_BIGINT:
                raise ValidationError({
                    "reference": _("Reference number is too large")
                })

        return reference_int

    reference_int = models.BigIntegerField(default=0)


def extract_int(reference, clip=0x7fffffff, allow_negative=False):
    """Extract an integer out of reference."""

    # Default value if we cannot convert to an integer
    ref_int = 0

    reference = str(reference).strip()

    # Ignore empty string
    if len(reference) == 0:
        return 0

    # Look at the start of the string - can it be "integerized"?
    result = re.match(r"^(\d+)", reference)

    if result and len(result.groups()) == 1:
        ref = result.groups()[0]
        try:
            ref_int = int(ref)
        except Exception:
            ref_int = 0
    else:
        # Look at the "end" of the string
        result = re.search(r'(\d+)$', reference)

        if result and len(result.groups()) == 1:
            ref = result.groups()[0]
            try:
                ref_int = int(ref)
            except Exception:
                ref_int = 0

    # Ensure that the returned values are within the range that can be stored in an IntegerField
    # Note: This will result in large values being "clipped"
    if clip is not None:
        if ref_int > clip:
            ref_int = clip
        elif ref_int < -clip:
            ref_int = -clip

    if not allow_negative and ref_int < 0:
        ref_int = abs(ref_int)

    return ref_int


class InvenTreeAttachment(models.Model):
    """Provides an abstracted class for managing file attachments.

    An attachment can be either an uploaded file, or an external URL

    Attributes:
        attachment: File
        comment: String descriptor for the attachment
        user: User associated with file upload
        upload_date: Date the file was uploaded
    """

    def getSubdir(self):
        """Return the subdirectory under which attachments should be stored.

        Note: Re-implement this for each subclass of InvenTreeAttachment
        """
        return "attachments"

    def save(self, *args, **kwargs):
        """Provide better validation error."""
        # Either 'attachment' or 'link' must be specified!
        if not self.attachment and not self.link:
            raise ValidationError({
                'attachment': _('Missing file'),
                'link': _('Missing external link'),
            })

        super().save(*args, **kwargs)

    def __str__(self):
        """Human name for attachment."""
        if self.attachment is not None:
            return os.path.basename(self.attachment.name)
        else:
            return str(self.link)

    attachment = models.FileField(upload_to=rename_attachment, verbose_name=_('Attachment'),
                                  help_text=_('Select file to attach'),
                                  blank=True, null=True
                                  )

    link = InvenTreeURLField(
        blank=True, null=True,
        verbose_name=_('Link'),
        help_text=_('Link to external URL')
    )

    comment = models.CharField(blank=True, max_length=100, verbose_name=_('Comment'), help_text=_('File comment'))

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    upload_date = models.DateField(auto_now_add=True, null=True, blank=True, verbose_name=_('upload date'))

    @property
    def basename(self):
        """Base name/path for attachment."""
        if self.attachment:
            return os.path.basename(self.attachment.name)
        else:
            return None

    @basename.setter
    def basename(self, fn):
        """Function to rename the attachment file.

        - Filename cannot be empty
        - Filename cannot contain illegal characters
        - Filename must specify an extension
        - Filename cannot match an existing file
        """
        fn = fn.strip()

        if len(fn) == 0:
            raise ValidationError(_('Filename must not be empty'))

        attachment_dir = settings.MEDIA_ROOT.joinpath(self.getSubdir())
        old_file = settings.MEDIA_ROOT.joinpath(self.attachment.name)
        new_file = settings.MEDIA_ROOT.joinpath(self.getSubdir(), fn).resolve()

        # Check that there are no directory tricks going on...
        if new_file.parent != attachment_dir:
            logger.error(f"Attempted to rename attachment outside valid directory: '{new_file}'")
            raise ValidationError(_("Invalid attachment directory"))

        # Ignore further checks if the filename is not actually being renamed
        if new_file == old_file:
            return

        forbidden = ["'", '"', "#", "@", "!", "&", "^", "<", ">", ":", ";", "/", "\\", "|", "?", "*", "%", "~", "`"]

        for c in forbidden:
            if c in fn:
                raise ValidationError(_(f"Filename contains illegal character '{c}'"))

        if len(fn.split('.')) < 2:
            raise ValidationError(_("Filename missing extension"))

        if not old_file.exists():
            logger.error(f"Trying to rename attachment '{old_file}' which does not exist")
            return

        if new_file.exists():
            raise ValidationError(_("Attachment with this filename already exists"))

        try:
            os.rename(old_file, new_file)
            self.attachment.name = os.path.join(self.getSubdir(), fn)
            self.save()
        except Exception:
            raise ValidationError(_("Error renaming file"))

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True


class InvenTreeTree(MPTTModel):
    """Provides an abstracted self-referencing tree model for data categories.

    - Each Category has one parent Category, which can be blank (for a top-level Category).
    - Each Category can have zero-or-more child Categor(y/ies)

    Attributes:
        name: brief name
        description: longer form description
        parent: The item immediately above this one. An item with a null parent is a top-level item
    """

    def api_instance_filters(self):
        """Instance filters for InvenTreeTree models."""
        return {
            'parent': {
                'exclude_tree': self.pk,
            }
        }

    def save(self, *args, **kwargs):
        """Custom save method for InvenTreeTree abstract model"""

        try:
            super().save(*args, **kwargs)
        except InvalidMove:
            # Provide better error for parent selection
            raise ValidationError({
                'parent': _("Invalid choice"),
            })

        # Re-calculate the 'pathstring' field
        pathstring = InvenTree.helpers.constructPathString(
            [item.name for item in self.path]
        )

        if pathstring != self.pathstring:
            self.pathstring = pathstring
            super().save(force_update=True)

    class Meta:
        """Metaclass defines extra model properties."""

        abstract = True

        # Names must be unique at any given level in the tree
        unique_together = ('name', 'parent')

    class MPTTMeta:
        """Set insert order."""
        order_insertion_by = ['name']

    name = models.CharField(
        blank=False,
        max_length=100,
        verbose_name=_("Name"),
        help_text=_("Name"),
    )

    description = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_("Description"),
        help_text=_("Description (optional)")
    )

    # When a category is deleted, graft the children onto its parent
    parent = TreeForeignKey('self',
                            on_delete=models.DO_NOTHING,
                            blank=True,
                            null=True,
                            verbose_name=_("parent"),
                            related_name='children')

    # The 'pathstring' field is calculated each time the model is saved
    pathstring = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Path'),
        help_text=_('Path')
    )

    @property
    def item_count(self):
        """Return the number of items which exist *under* this node in the tree.

        Here an 'item' is considered to be the 'leaf' at the end of each branch,
        and the exact nature here will depend on the class implementation.

        The default implementation returns zero
        """
        return 0

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
        childs = self.getUniqueChildren()

        acceptable = [None]

        for a in available:
            if a.id not in childs:
                acceptable.append(a)

        return acceptable

    @property
    def parentpath(self):
        """Get the parent path of this category.

        Returns:
            List of category names from the top level to the parent of this category
        """
        return [a for a in self.get_ancestors()]

    @property
    def path(self):
        """Get the complete part of this category.

        e.g. ["Top", "Second", "Third", "This"]

        Returns:
            List of category names from the top level to this category
        """
        return self.parentpath + [self]

    def __str__(self):
        """String representation of a category is the full path to that category."""
        return "{path} - {desc}".format(path=self.pathstring, desc=self.description)


class InvenTreeBarcodeMixin(models.Model):
    """A mixin class for adding barcode functionality to a model class.

    Two types of barcodes are supported:

    - Internal barcodes (QR codes using a strictly defined format)
    - External barcodes (assign third party barcode data to a model instance)

    The following fields are added to any model which implements this mixin:

    - barcode_data : Raw data associated with an assigned barcode
    - barcode_hash : A 'hash' of the assigned barcode data used to improve matching
    """

    class Meta:
        """Metaclass options for this mixin.

        Note: abstract must be true, as this is only a mixin, not a separate table
        """
        abstract = True

    barcode_data = models.CharField(
        blank=True, max_length=500,
        verbose_name=_('Barcode Data'),
        help_text=_('Third party barcode data'),
    )

    barcode_hash = models.CharField(
        blank=True, max_length=128,
        verbose_name=_('Barcode Hash'),
        help_text=_('Unique hash of barcode data')
    )

    @classmethod
    def barcode_model_type(cls):
        """Return the model 'type' for creating a custom QR code."""

        # By default, use the name of the class
        return cls.__name__.lower()

    def format_barcode(self, **kwargs):
        """Return a JSON string for formatting a QR code for this model instance."""

        return InvenTree.helpers.MakeBarcode(
            self.__class__.barcode_model_type(),
            self.pk,
            **kwargs
        )

    @property
    def barcode(self):
        """Format a minimal barcode string (e.g. for label printing)"""

        return self.format_barcode(brief=True)

    @classmethod
    def lookup_barcode(cls, barcode_hash):
        """Check if a model instance exists with the specified third-party barcode hash."""

        return cls.objects.filter(barcode_hash=barcode_hash).first()

    def assign_barcode(self, barcode_hash, barcode_data=None, raise_error=True):
        """Assign an external (third-party) barcode to this object."""

        # Check for existing item
        if self.__class__.lookup_barcode(barcode_hash) is not None:
            if raise_error:
                raise ValidationError(_("Existing barcode found"))
            else:
                return False

        if barcode_data is not None:
            self.barcode_data = barcode_data

        self.barcode_hash = barcode_hash

        self.save()

        return True


@receiver(pre_delete, sender=InvenTreeTree, dispatch_uid='tree_pre_delete_log')
def before_delete_tree_item(sender, instance, using, **kwargs):
    """Receives pre_delete signal from InvenTreeTree object.

    Before an item is deleted, update each child object to point to the parent of the object being deleted.
    """
    # Update each tree item below this one
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()


@receiver(post_save, sender=Error, dispatch_uid='error_post_save_notification')
def after_error_logged(sender, instance: Error, created: bool, **kwargs):
    """Callback when a server error is logged.

    - Send a UI notification to all users with staff status
    """

    if created:
        try:
            import common.notifications

            users = get_user_model().objects.filter(is_staff=True)

            link = InvenTree.helpers.construct_absolute_url(
                reverse('admin:error_report_error_change', kwargs={'object_id': instance.pk})
            )

            context = {
                'error': instance,
                'name': _('Server Error'),
                'message': _('An error has been logged by the server.'),
                'link': link
            }

            common.notifications.trigger_notification(
                instance,
                'inventree.error_log',
                context=context,
                targets=users,
                delivery_methods=set([common.notifications.UIMessageNotification]),
            )

        except Exception as exc:
            """We do not want to throw an exception while reporting an exception"""
            logger.error(exc)
