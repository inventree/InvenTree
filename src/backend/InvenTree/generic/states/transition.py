"""Classes and functions for plugin controlled object state transitions."""

from collections.abc import Callable
from enum import Enum
from functools import wraps

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model

import structlog
from django_fsm import TransitionNotAllowed, transition

from plugin.events import trigger_event

from .deprecations import deprecated

logger = structlog.get_logger('inventree')


def inventree_transition(
    field, source, target, event=None, refresh_field: bool = True, **extra
):
    """Decorator that combines ``@django_fsm.transition`` with plugin transitions.

    Wraps a model method so that:
    * Source/target state validation is enforced via ``django_fsm.transition``.
    * Plugin transitions are called automatically before the FSM transition executes.
    * The model instance is saved after a successful transition.
    * The whole operation is wrapped in a database transaction.

    Usage::

        class MyOrder(StateTransitionMixin, models.Model):
            status = InvenTreeCustomStatusModelField(
                status_class=MyOrderStatus, ...
            )

            @inventree_transition(
                field=status,
                source=[MyOrderStatus.PENDING, MyOrderStatus.ON_HOLD],
                target=MyOrderStatus.PLACED,
                event=MyOrderEvents.PLACED,
                refresh_field=False,
            )
            def place_order(self):
                notify_responsible(...)

    The ``can_<method>`` guard pattern can be preserved using ``can_proceed``::

        @property
        def can_issue(self) -> bool:
            return can_proceed(self.place_order)

    Args:
        field: The ``InvenTreeCustomStatusModelField`` (or its string name) that holds the state.
        source: Allowed source state(s) for the transition.
        target: Target state after the transition.
        event: Optional event (name) to trigger after the transition.  If not provided no event is triggered.
        refresh_field: (default True) If True, the field is updated from the database before the transition.
        **extra: Additional keyword arguments forwarded to `django_fsm.transition` (e.g. `conditions`, `on_error`, `permission`).
    """

    def decorator(func):
        # Apply the django-fsm @transition decorator first.
        fsm_func = transition(field=field, source=source, target=target, **extra)(func)

        @transaction.atomic
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            """Ensure that transitions are handled correctly."""
            if refresh_field:
                try:
                    # Update the field from the database to avoid race conditions
                    current_obj = type(self).objects.select_for_update().get(pk=self.pk)
                    new_value = getattr(current_obj, field.name)
                    setattr(self, field.name, new_value)
                except type(self).DoesNotExist:  # pragma: no cover
                    raise ValidationError(
                        f'{self._meta.verbose_name} with pk={self.pk} does not exist in the database'
                    )

            # Run plugin transition handlers - if no step is taken the decorated method is called
            if result := _run_plugin_transition_handlers(
                self,
                getattr(self, field.name),
                target,
                default_action=_noop_default_action,
            ):
                return result

            # Execute the FSM-wrapped function.  This validates the source state,
            # runs the method body, and updates the field to the target state.
            try:
                fsm_func(self, *args, **kwargs)
            except TransitionNotAllowed as exc:
                # Preserve backward-compatible behaviour: an invalid transition
                # (wrong source state, failed condition, or explicit raise inside
                # the method body) returns False rather than raising.
                if getattr(self, field.name) == target:
                    target_val = (
                        target.label
                        if isinstance(target, Enum) and hasattr(target, 'label')
                        else target
                    )
                    raise ValidationError(
                        f'{self._meta.verbose_name} is already {target_val}'
                    ) from exc
                raise ValidationError(
                    f'Invalid transition on {self._meta.verbose_name}.{field.name} (source value should be {source}, is {getattr(self, field.name)})'
                ) from exc
            # Persist all changes (including the updated status field) to the DB.
            self.save()

            # trigger event for the transition
            if event:
                trigger_event(event, id=self.pk)

            return True

        # Propagate the django-fsm metadata so that can_proceed() works correctly
        # on the public wrapper method.
        if hasattr(fsm_func, '_django_fsm'):
            wrapper._django_fsm = fsm_func._django_fsm
        return wrapper

    return decorator


class TransitionMethod:
    """Base class for all plugin-defined transition handler classes.

    A plugin transition handler is called for every state transition on a
    ``StateTransitionMixin`` model.  Subclasses must implement a ``transition``
    method.
    """

    def __init__(self) -> None:
        """Check that the method is defined correctly.

        This checks that:
        - The needed functions are implemented
        """
        # Check if a sending fnc is defined
        if not hasattr(self, 'transition'):  # pragma: no cover
            raise NotImplementedError(
                'A TransitionMethod must define a `transition` method'
            )

    def transition(
        self,
        current_state: int,
        target_state: int,
        instance: Model,
        default_action: Callable,
        **kwargs,
    ) -> bool:
        """Perform a state transition.

        When used with ``@inventree_transition``-decorated methods, plugin
        handlers are invoked before the decorated method body executes.
        The semantics are:

        * **Ignore** - return ``False``.  Further handlers are attempted;
          the decorated method body executes as normal.
        * **Veto** - raise ``ValidationError``.  The transition is cancelled;
          no further handlers are called; the method body does *not* execute.
        * **Handle** (deprecated) - return ``True``.  This historically meant
          "I handled the transition; skip the default action."  Under
          ``@inventree_transition``, the decorated method body *always* runs, so
          returning ``True`` now only triggers a ``DeprecationWarning``.  Plugin
          authors should raise ``ValidationError`` to cancel a transition, or
          return ``False`` to allow it to proceed.

        Arguments:
            current_state: int - Current state of the instance.
            target_state: int - Target state to transition to.
            instance: Model - The object instance to transition.
            default_action: callable - No-op when called from the
                ``inventree_transition`` wrapper; present for backward
                compatibility.
            **kwargs: Additional keyword arguments for custom logic.

        Returns:
            result: bool - ``True`` triggers a deprecation warning (see above).
                ``False`` allows the transition to proceed normally.

        Raises:
            ValidationError: Cancels the transition.
        """
        raise NotImplementedError(
            'TransitionMethod.transition must be implemented'
        )  # pragma: no cover


class StateTransitionMixin:
    """Mixin class to enable plugin-controlled state transitions.

    Add this mixin to a Django model to gain:

    * Plugin hook support for all ``@inventree_transition``-decorated methods
      (via the ``inventree_transition`` decorator).
    * A legacy ``handle_transition`` method for backward compatibility with
      code that calls it directly.

    Example::

        class MyOrder(StateTransitionMixin, models.Model):
            status = InvenTreeCustomStatusModelField(
                status_class=MyOrderStatus, ...
            )

            @inventree_transition(
                field=status,
                source=[MyOrderStatus.PENDING],
                target=MyOrderStatus.PLACED,
            )
            def place_order(self):
                pass
    """

    @deprecated('Use the @inventree_transition decorator instead', version='1.5.0')
    def handle_transition(
        self, current_state, target_state, instance, default_action, **kwargs
    ):  # pragma: no cover
        """Handle a state transition for an object.

        .. deprecated::
            Use the ``@inventree_transition`` decorator instead.  This method
            is kept for backward compatibility only and calls the ``default_action``
            directly without invoking the django-fsm machinery or signals.

        Args:
            current_state: Current state of instance
            target_state: Target state of instance
            instance: Object instance
            default_action: Default action to be taken if none of the
                transitions returns a boolean true value
        """
        if result := _run_plugin_transition_handlers(
            instance, current_state, target_state, default_action=default_action
        ):
            return result
        return default_action(current_state, target_state, instance, **kwargs)


def _run_plugin_transition_handlers(instance, source, target, default_action):
    """Run plugin transition handlers before a state transition.

    A plugin handler may veto the transition by raising a ``ValidationError``.
    """
    if not isinstance(instance, StateTransitionMixin) or not isinstance(
        instance, Model
    ):
        return  # pragma: no cover

    from InvenTree.exceptions import log_error
    from plugin import PluginMixinEnum, registry

    transition_plugins = registry.with_mixin(PluginMixinEnum.STATE_TRANSITION)

    for plugin in transition_plugins:
        try:
            handlers = plugin.get_transition_handlers()
        except Exception:
            log_error('get_transition_handlers', plugin=plugin)
            continue

        if type(handlers) is not list:
            logger.error(
                'INVE-E9: Plugin %s returned invalid type for transition handlers',
                plugin.slug,
            )
            continue

        for handler in handlers:
            if not isinstance(handler, TransitionMethod):
                logger.error('INVE-E9: Invalid transition handler type: %s', handler)
                continue

            # Call the transition method.
            # ValidationError raised here will propagate and cancel the transition.
            if result := handler.transition(source, target, instance, default_action):
                return result


def _noop_default_action(current_state, target_state, instance, **kwargs):
    """No-op default action for compatibility with transition handlers."""
    return None  # pragma: no cover
