"""Generic models which provide extra functionality over base Django model types."""

from datetime import datetime
from string import Formatter

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext_lazy as _

import structlog
from django_q.models import Task
from django_q.signals import post_execute
from error_report.models import Error

import common.settings
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

            if field.is_relation:
                # Compare the raw FK id first (no query) - only dereference to the
                # full related object (one query each side) if it actually differs.
                # In the common case (unchanged FK) this avoids two full-object
                # fetches per relational field for every single save() call.
                if getattr(self, field.attname) == getattr(db_instance, field.attname):
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


def _notify_task_failure(func: str, task_id: str, attempt_count: int, result) -> None:
    """Create a new Error object for a permanently-failed background task.

    This will, in turn, trigger a notification to staff users via the Error post_save signal.
    """
    from InvenTree.exceptions import log_error

    message = f"Task '{func} ({task_id})' failed after {attempt_count} attempt{'s' if attempt_count != 1 else ''}"

    logger.error(message)

    log_error(
        'task_failure',
        scope='worker',
        error_name='Task Failure',
        error_info=message,
        error_data=str(result) if result else '',
    )


@receiver(post_save, sender=Task, dispatch_uid='failure_post_save_notification')
def after_failed_task(sender, instance: Task, created: bool, **kwargs):
    """Callback when a new task failure log is generated."""
    from django.conf import settings

    max_attempts = int(settings.Q_CLUSTER.get('max_attempts', 5))
    n = instance.attempt_count

    # Only notify once the maximum number of attempts has been reached
    if not instance.success and n >= max_attempts:
        _notify_task_failure(instance.func, instance.pk, n, instance.result)


@receiver(post_execute, dispatch_uid='failure_post_execute_notification')
def after_single_shot_task_failure(sender, task: dict, **kwargs):
    """Callback when a background task finishes executing.

    A task offloaded with offload_task(..., retry=False) is marked with the
    'ack_failure' option, which causes the broker to drop it after a single failed
    attempt (see InvenTree.tasks.offload_task) - its attempt_count will never reach
    Q_CLUSTER['max_attempts'], so after_failed_task()'s post_save-based check would
    otherwise never fire a notification for it. This uses django-q2's post_execute
    signal instead, which (unlike the saved Task record) still carries the
    'ack_failure' flag, to notify immediately on that task's one and only attempt.
    """
    from django.conf import settings

    if task.get('success') or not task.get('ack_failure'):
        return

    max_attempts = int(settings.Q_CLUSTER.get('max_attempts', 5))

    if max_attempts <= 1:
        # after_failed_task() already handles this case via its own post_save signal -
        # avoid notifying twice
        return

    from django_q.utils import get_func_repr

    _notify_task_failure(
        get_func_repr(task.get('func')), task.get('id'), 1, task.get('result')
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
