"""DRF viewset helpers to add transition endpoints."""

from __future__ import annotations

import inspect
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from InvenTree.serializers import EmptySerializer

from .introspection import available_transitions, state_fields, transition_methods

# from .serializers import AvailableTransitionSerializer

#: URL segment every transition endpoint sits under, keeping them clear of model field routes.
TRANSITION_URL_PREFIX = '_transition'


def current_state(instance: Any, field_name: str | None = None) -> str | None:
    """Return the value of an instance's FSM state field.

    Args:
        instance: Any model instance, whether or not it carries an FSM field.
        field_name: Which state field to read. Defaults to the model's first FSM field.

    Returns:
        The current state value, or None when the instance has no such field.
    """
    if field_name is None:
        names = state_fields(type(instance))
        if not names:
            return None
        field_name = names[0]

    return getattr(instance, field_name, None)


def transition_error(
    instance: Any, transition_name: str, exc: Exception
) -> dict[str, Any]:
    """Build the error body for a refused transition.

    Args:
        instance: The instance the transition was attempted on, still in its source state.
        transition_name: Name of the transition function that refused.
        exc: The ``ValidationError`` the FSM raised.

    Returns:
        A JSON-safe body with ``detail``, ``transition``, ``state`` and ``blocking_reason``.
    """
    meta = transition_methods(type(instance)).get(transition_name)
    field = getattr(meta, 'field', None) if meta is not None else None
    field_name = field if isinstance(field, str) else getattr(field, 'name', None)

    state = current_state(instance, field_name)
    info = next(
        (
            entry
            for entry in available_transitions(instance)
            if entry.name == transition_name
        ),
        None,
    )

    messages = getattr(exc, 'messages', None) or [str(exc)]
    detail = '; '.join(str(message) for message in messages)
    reason: str | None = None

    if info is None:
        detail = (
            f"Transition '{transition_name}' is not available from state '{state}'."
        )
    elif info.blocked:
        reason = info.blocking_reason
        detail = reason or detail

    return {
        'detail': detail,
        'transition': transition_name,
        'state': state,
        'blocking_reason': reason,
    }


def transition_action(
    method_name: str,
    *,
    name: str | None = None,
    url_path: str | None = None,
    arg_serializer: type[serializers.Serializer] | None = None,
    return_code: int = status.HTTP_200_OK,
    pass_user: bool = False,
    serializer_class: type[serializers.Serializer] | None = None,
) -> Any:
    """Build a ``POST`` detail endpoint running one FSM transition method.

    ``inventree_transition`` runs the transition in ``transaction.atomic`` and saves the instance,
    so nothing here saves. A refused transition raises ``ValidationError``, returned as ``400``.

    Args:
        method_name: Name of the transition method on the model.
        name: Attribute name on the viewset. Defaults to ``method_name``.
        url_path: Path segment under ``_transition/``. Defaults to ``name``, hyphenated.
        arg_serializer: Serializer validating the request body. Its ``transition_kwargs()``, else
            its ``validated_data``, is passed to the transition as keyword arguments.
        return_code: HTTP status code to return on success. Defaults to `200`.
        pass_user: Pass the requesting user to the transition as ``user=``.
        serializer_class: Serializer to use for the response body. Defaults to an empty serializer

    Returns:
        A DRF ``@action``-decorated method, ready to assign as a viewset class attribute.
    """
    attr_name = name or method_name
    segment = url_path or attr_name.replace('_', '-')
    # TODO @matmair move all transition actions under the common prefix
    # path = f'{TRANSITION_URL_PREFIX}/{segment}'
    path = f'{segment}'

    def endpoint(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        kwargs: dict[str, Any] = {}

        if arg_serializer is not None:
            payload = arg_serializer(data=request.data)
            payload.is_valid(raise_exception=True)
            extract = getattr(payload, 'transition_kwargs', None)
            kwargs.update(extract() if extract else dict(payload.validated_data))

        if pass_user:
            user = getattr(request, 'user', None)
            kwargs['user'] = (
                user if user is not None and user.is_authenticated else None
            )

        try:
            getattr(instance, method_name)(**kwargs)
        except DjangoValidationError as exc:
            return Response(
                transition_error(instance, method_name, exc),
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.refresh_from_db()

        serial = (
            self.get_serializer(instance)
            if not arg_serializer
            else arg_serializer(instance)
        )
        return Response(serial.data, status=return_code)

    model_name = 'object'
    endpoint.__name__ = attr_name
    endpoint.__qualname__ = attr_name
    endpoint.__doc__ = f"API endpoint to '{method_name}' a {model_name}."
    # Read back by FSMTransitionMixin.transition_url_paths().
    endpoint.transition_name = method_name

    optional_kwargs = {}
    if serializer_class is not None:
        optional_kwargs['serializer_class'] = serializer_class
    else:
        optional_kwargs['serializer_class'] = EmptySerializer

    ret = action(
        detail=True,
        methods=['post'],
        url_path=path,
        # TODO @matmair add option to rename the urlname
        url_name=segment,
        output_options=None,
        **optional_kwargs,
    )(endpoint)

    # add decorator if custom return_code is required
    if return_code != status.HTTP_200_OK:
        ret = extend_schema(
            responses={return_code: optional_kwargs['serializer_class']}
        )(ret)

    return ret


def transition_call_plan(func: Any) -> tuple[bool, tuple[str, ...]]:
    """Report how a transition method must be called, from its signature.

    ``inventree_transition`` wraps the method with ``functools.wraps``, so the decorated method's
    own parameters are still visible.

    Args:
        func: The transition method, as read off the model class.

    Returns:
        ``(pass_user, required)`` — whether the method takes ``user``, and the names of any other
        parameters it requires.
    """
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):  # pragma: no cover
        return False, ()

    pass_user = False
    required: list[str] = []

    for index, (param_name, param) in enumerate(signature.parameters.items()):
        if index == 0 and param_name in ('self', 'cls'):
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if param_name == 'user':
            pass_user = True
            continue
        if param.default is param.empty:
            required.append(param_name)

    return pass_user, tuple(required)


class FSMTransitionMixin:
    """Viewset mixin for exposing all FSM transitions on a model."""

    #: Per-transition overrides keyed by model method name
    transition_options: dict[str, dict[str, Any]] = {}

    #: Model method names to leave unexposed, including ones inherited from a base viewset.
    transition_exclude: tuple[str, ...] = ()

    #: Set False to stop this class generating endpoints; inherited ones remain.
    autodiscover_transitions: bool = True

    #: Model method name -> viewset attribute, filled in by :meth:`register_transition_actions`.
    generated_transition_actions: dict[str, str] = {}

    #: Model method name -> why no endpoint was generated for it.
    skipped_transitions: dict[str, str] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Generate the transition endpoints when a viewset class is defined.

        Args:
            **kwargs: Class keyword arguments, forwarded up the MRO.
        """
        super().__init_subclass__(**kwargs)
        cls.register_transition_actions()

    @classmethod
    def get_transition_model(cls) -> type | None:
        """Return the model whose transitions this viewset exposes.

        Returns:
            The model from ``queryset``, else from ``serializer_class.Meta.model``, else None.
        """
        queryset = getattr(cls, 'queryset', None)
        if queryset is not None:
            return queryset.model

        meta = getattr(getattr(cls, 'serializer_class', None), 'Meta', None)
        return getattr(meta, 'model', None)

    @classmethod
    def register_transition_actions(cls) -> dict[str, str]:
        """Attach one endpoint to this class per transition on its model.

        Idempotent: endpoints generated earlier are regenerated, other attributes are untouched.

        Returns:
            Mapping of model method name to the viewset attribute holding its endpoint.
        """
        generated: dict[str, str] = {}
        skipped: dict[str, str] = {}
        cls.generated_transition_actions = generated
        cls.skipped_transitions = skipped

        model = cls.get_transition_model()
        if model is None or not cls.autodiscover_transitions:
            return generated

        for method_name in sorted(transition_methods(model)):
            options = dict(cls.transition_options.get(method_name) or {})
            attr_name = options.get('name') or method_name
            existing = getattr(cls, attr_name, None)
            inherited = getattr(existing, 'transition_name', None) == method_name

            if method_name in cls.transition_exclude:
                skipped[method_name] = 'excluded by transition_exclude'
                cls._suppress_transition_action(attr_name, inherited)
                continue

            if existing is not None and not inherited:
                # A hand-written action or a viewset method of the same name wins.
                skipped[method_name] = (
                    f"'{attr_name}' is already defined on {cls.__name__}"
                )
                continue

            pass_user, required = transition_call_plan(getattr(model, method_name))
            options.setdefault('pass_user', pass_user)

            if required and 'arg_serializer' not in options:
                skipped[method_name] = (
                    'takes arguments ({}) with no arg_serializer'.format(
                        ', '.join(required)
                    )
                )
                cls._suppress_transition_action(attr_name, inherited)
                continue

            setattr(cls, attr_name, transition_action(method_name, **options))
            generated[method_name] = attr_name

        return generated

    @classmethod
    def _suppress_transition_action(cls, attr_name: str, inherited: bool) -> None:
        """Hide an endpoint generated by a base class.

        Shadowing the attribute with None removes it from DRF's extra-action discovery without
        touching the base class.

        Args:
            attr_name: The viewset attribute the inherited endpoint occupies.
            inherited: Whether that attribute holds a generated transition endpoint.
        """
        if inherited:
            setattr(cls, attr_name, None)

    @classmethod
    def transition_url_paths(cls) -> dict[str, str]:
        """Map transition method name to the URL path of the endpoint running it.

        Returns:
            Mapping of transition name to detail-relative URL path, generated or hand-written.
        """
        return {
            handler.transition_name: handler.url_path
            for handler in cls.get_extra_actions()
            if getattr(handler, 'transition_name', None)
        }

    # @action(
    #     detail=True,
    #     methods=['get'],
    #     url_path=TRANSITION_URL_PREFIX,
    #     url_name='transitions',
    #     serializer_class=AvailableTransitionSerializer,
    # )
    # def transitions(self, request: Request, pk: str | None = None) -> Response:
    #     """List the FSM transitions reachable from this object's current state.

    #     Blocked transitions are included and flagged with their reason.

    #     Only transitions this viewset exposes as an endpoint are reported: ``available_transitions``
    #     matches by state field name, so restricting the answer to this viewset's own endpoints keeps
    #     every entry something the client can POST to.
    #     """
    #     instance = self.get_object()
    #     paths = self.transition_url_paths()

    #     available: list[TransitionInfo] = [
    #         entry for entry in available_transitions(instance) if entry.name in paths
    #     ]
    #     data = [
    #         {
    #             'name': entry.name,
    #             'url_path': paths[entry.name],
    #             'target': entry.target,
    #             'label': entry.label,
    #             'blocked': entry.blocked,
    #             'blocking_reason': entry.blocking_reason,
    #         }
    #         for entry in available
    #     ]
    #     return Response(AvailableTransitionSerializer(data, many=True).data)


__all__ = [
    'TRANSITION_URL_PREFIX',
    'FSMTransitionMixin',
    'current_state',
    'transition_action',
    'transition_call_plan',
    'transition_error',
]
