"""Plugin mixin for integrating suppliers."""

import logging
from dataclasses import dataclass
from typing import Dict, OrderedDict

from common.models import WebConnectionData
from part.models import PartCategory
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

    @classmethod
    def _activate_mixin(cls, registry, plugins, force_reload=False, full_reload: bool = False):
        """Activate SupplierMixin plugins.

        Args:
            registry (PluginRegistry): The registry that should be used
            plugins (dict): List of IntegrationPlugins that should be installed
            force_reload (bool, optional): Only reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        logger.info('Activating supplier plugins')

        # Define registry for supplier plugins
        registry.mixins_suppliers = {}

        # Collect connections
        for slug, plugin in plugins:
            if plugin.mixin_enabled('supplier'):
                registry.mixins_suppliers[slug] = plugin.connections

    @classmethod
    def _deactivate_mixin(cls, registry, force_reload: bool = False):
        """Deactivate SupplierMixin plugins.

        Args:
            registry (PluginRegistry): The registry that should be used
            force_reload (bool, optional): Also reload base apps. Defaults to False.
        """
        logger.info('Deactivating supplier plugins')

        # Clear settings cache
        registry.mixins_suppliers = {}

    def setup_connections(self):
        """Setup web connections for this plugin."""
        return getattr(self, 'CONNECTIONS', None)

    # TODO @matmair clean up this mess
    def get_con(self, key: str, ref: str = None, default=None):
        """Get webconnection setting data."""
        def ret_default(val):
            if not val and default:
                return default
            return val

        ref = ref if ref else self.STD_CONNECTION
        qs = self.db.webconnections.filter(connection_key=ref)
        ret = [a.settings.get(key=key).value for a in qs]
        if len(ret) == 1:
            return ret_default(ret[0])
        return ret_default(ret)

    # TODO @matmair clean up this mess
    def set_con(self, key: str, val, ref: str = None):
        """Set webconnection setting data."""
        ref = ref if ref else self.STD_CONNECTION
        qs = self.db.webconnections.filter(connection_key=ref)
        if len(qs) > 1:
            raise NotImplementedError('This function is not implemented!')
        setting = qs[0].settings.get(key=key)
        setting.value = val
        setting.save()

    def search_action(self, term: str, exact: bool = False, safe_results: bool = True) -> SearchRunResult:
        """Run search against supplier and return results."""
        raise MixinNotImplementedError('The `search_action` function must be enabled for search integration.')

    def import_part(self, term: str, category: PartCategory) -> bool:
        """Tries to import a part by term. Returns bool if import was successfull."""
        raise MixinNotImplementedError('The `import_part` function must be enabled for search integration.')
