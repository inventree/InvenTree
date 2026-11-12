"""Support for generic search functionality."""

from collections.abc import Callable

SEARCH_PROVIDERS = {}
SEARCH_FILTERS = {}


def search_provider(
    ref_names: list[str] | None = None, default_filters: dict | None = None
):
    """Register a view class as a provider for one or more search result types."""

    def decorator(func):
        """Register the view class for each configured search result type."""
        filters = default_filters or {}
        for name in ref_names or [func.__name__.lower()]:
            SEARCH_PROVIDERS[name] = func
            SEARCH_FILTERS[name] = filters.get(name, {})
        return func

    return decorator


def get_search_providers() -> dict[str, Callable]:
    """Return the registered search provider classes."""
    return dict(SEARCH_PROVIDERS)


def get_search_filters() -> dict[str, dict]:
    """Return default filters keyed by search result type."""
    return dict(SEARCH_FILTERS)
