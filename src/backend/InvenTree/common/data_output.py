"""Access a DataOutput instance and collect warnings in the current context."""

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from common.models import DataOutput


logger = logging.getLogger('inventree')

_current_data_output: ContextVar[Optional['DataOutput']] = ContextVar(
    'current_data_output', default=None
)


@contextmanager
def data_output_context(output: 'DataOutput'):
    """Bind a result for this scope, restoring the previous binding on exit."""
    token = _current_data_output.set(output)
    try:
        yield
    finally:
        _current_data_output.reset(token)


def get_current_data_output() -> Optional['DataOutput']:
    """Return the result bound to this context, or None outside a scope."""
    return _current_data_output.get()


def add_output_warning(message: str):
    """Add a warning without saving, or log it when no result is bound."""
    if (output := get_current_data_output()) is not None:
        output.add_warning(message)
    else:
        logger.warning('%s', message)
