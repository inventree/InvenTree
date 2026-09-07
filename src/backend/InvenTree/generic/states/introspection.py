"""FSM transition introspection for UI rendering (T-0709)."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from django_fsm import FSMFieldMixin


@dataclass
class TransitionInfo:
    """Information about a transition reachable from an instance's current state."""

    name: str
    target: str
    label: str
    blocked: bool = False
    blocking_reason: str | None = None


def state_fields(model: type):
    """Return the names of the FSM state fields on model."""
    return tuple(
        field.name for field in model._meta.fields if isinstance(field, FSMFieldMixin)
    )


def transition_methods(model: type, field_name: str | None = None):
    """Return every transition method on model.

    Args:
        model: The model class to scan
        field_name: Restrict insights on specific name

    Returns:
        Mapping of transition method name to its django-fsm metadata.
    """
    found: dict[str, Any] = {}

    for name, func in inspect.getmembers(model):
        meta = getattr(func, '_django_fsm', None)
        if meta is None:
            continue

        field = meta.field
        declared = field if isinstance(field, str) else getattr(field, 'name', None)
        if field_name is None or declared == field_name:
            found[name] = meta

    return found


def available_transitions(instance):
    """List the transitions reachable from an instance's current state."""
    found: list[TransitionInfo] = []

    for field_name in state_fields(type(instance)):
        current_state = getattr(instance, field_name, None)
        if current_state is None:
            continue

        for name, meta in transition_methods(type(instance), field_name).items():
            if not meta.has_transition(current_state):
                continue

            transition = meta.get_transition(current_state)
            blocked, reason = _evaluate_conditions(transition, instance)

            found.append(
                TransitionInfo(
                    name=name,
                    target=str(transition.target)
                    if transition.target is not None
                    else '',
                    label=_label(transition, name),
                    blocked=blocked,
                    blocking_reason=reason,
                )
            )
    return found


def _evaluate_conditions(transition, instance):
    """Check a transition's conditions without running it."""
    for condition in transition.conditions or ():
        try:
            passed = condition(instance)
        except Exception:
            return True, 'Cannot evaluate transition conditions'
        if not passed:
            reason = getattr(condition, 'blocking_reason', None)
            return True, str(reason) if reason is not None else None

    return False, None


def _label(transition, name: str):
    """Return the human-readable label for a transition."""
    label = (transition.custom or {}).get('label')
    if label:
        return str(label)
    return name.replace('_', ' ').title()
