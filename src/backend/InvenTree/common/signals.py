"""Signals for InvenTree actions.

These should be used slectevily, mostly to avoid circular imports and tight coupeling with modular/extensible parts of the codebase.
"""

from django.dispatch import Signal

post_currency_change = Signal()
"""Send after the default currency was changed."""
