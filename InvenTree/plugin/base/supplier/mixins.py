"""Plugin mixin for integrating suppliers."""

import logging
from dataclasses import dataclass
from typing import Dict, OrderedDict

from common.models import WebConnectionData
from plugin import MixinNotImplementedError

logger = logging.getLogger('inventree')


@dataclass
class SearchResult:
    """Contains a single search result."""
    term: str
    title: str
    link: str
    description: str = None
    pricture_url: str = None
    id: str = None


@dataclass()
class SearchRunResult:
    """Contains the results for a search run."""
    term: str
    exact: bool
    safe_results: bool
    results: OrderedDict[str, SearchResult]


class SupplierMixin:
    """Mixin to enable supplier integration."""

    CONNECTIONS: Dict[str, WebConnectionData]
    LIMIT_API_CALLS: bool = True

    class MixinMeta:
        """Meta for mixin."""
        MIXIN_NAME = "Supplier"

    def __init__(self):
        """Register the mixin."""
        super().__init__()
        self.add_mixin('supplier', True, __class__)
        self.connections = self.setup_connections()

    def setup_connections(self):
        """Setup web connections for this plugin."""
        return getattr(self, 'CONNECTIONS', None)

    def search_action(self, term: str, exact: bool = False, safe_results: bool = True) -> SearchRunResult:
        """Run search against supplier and return results."""
        raise MixinNotImplementedError('The `search_action` function must be enabled for search integration.')
