"""Helper functions for barcode generation."""

from typing import cast

import structlog

import InvenTree.helpers_model
from InvenTree.models import InvenTreeBarcodeMixin

logger = structlog.get_logger('inventree')


def cache(func):
    """Cache the result of a function, but do not cache falsy results."""
    cache = {}

    def wrapper():
        """Wrapper function for caching."""
        if 'default' not in cache:
            res = func()

            if res:
                cache['default'] = res

            return res

        return cache['default']

    return wrapper


def generate_barcode(model_instance: InvenTreeBarcodeMixin):
    """Generate a barcode for a given model instance."""
    from common.settings import get_global_setting
    from plugin import registry
    from plugin.mixins import BarcodeMixin

    # Find the selected barcode generation plugin
    slug = get_global_setting('BARCODE_GENERATION_PLUGIN', create=False)

    plugin = cast(BarcodeMixin, registry.get_plugin(slug))

    return plugin.generate(model_instance)


@cache
def get_supported_barcode_models() -> list[type[InvenTreeBarcodeMixin]]:
    """Returns a list of database models which support barcode functionality."""
    return InvenTree.helpers_model.getModelsWithMixin(InvenTreeBarcodeMixin)


@cache
def get_supported_barcode_models_map():
    """Return a mapping of barcode model types to the model class."""
    return {
        model.barcode_model_type(): model for model in get_supported_barcode_models()
    }


@cache
def get_supported_barcode_model_codes_map():
    """Return a mapping of barcode model type codes to the model class."""
    return {
        model.barcode_model_type_code(): model
        for model in get_supported_barcode_models()
    }
