"""Helper functions for barcode generation."""

import logging
from typing import Type, cast

import InvenTree.helpers_model
from InvenTree.models import InvenTreeBarcodeMixin

logger = logging.getLogger('inventree')


def cache_ignore_none(func):
    """Cache the result of a function, but do not cache None results."""
    cache = {}

    def wrapper():
        """Wrapper function for caching."""
        if 'default' not in cache:
            res = func()

            if res:
                cache['default'] = res
                print('===> update cache', func.__name__, res)
            else:
                print('===> ignore none cache', func.__name__, res)

            return res

        print('===> retrieve from cache', func.__name__, cache['default'])

        return cache['default']

    return wrapper


def barcode_plugins() -> list:
    """Return a list of plugin choices which can be used for barcode generation."""
    try:
        from plugin import registry

        plugins = registry.with_mixin('barcode', active=True)
    except Exception:
        plugins = []

    return [
        (plug.slug, plug.human_name) for plug in plugins if plug.has_barcode_generation
    ]


def generate_barcode(model_instance: InvenTreeBarcodeMixin):
    """Generate a barcode for a given model instance."""
    from common.settings import get_global_setting
    from plugin import registry
    from plugin.mixins import BarcodeMixin

    # Find the selected barcode generation plugin
    slug = get_global_setting('BARCODE_GENERATION_PLUGIN', create=False)

    plugin = cast(BarcodeMixin, registry.get_plugin(slug))

    return plugin.generate(model_instance)


@cache_ignore_none
def get_supported_barcode_models() -> list[Type[InvenTreeBarcodeMixin]]:
    """Returns a list of database models which support barcode functionality."""
    return InvenTree.helpers_model.getModelsWithMixin(InvenTreeBarcodeMixin)


@cache_ignore_none
def get_supported_barcode_models_map():
    """Return a mapping of barcode model types to the model class."""
    return {
        model.barcode_model_type(): model for model in get_supported_barcode_models()
    }


@cache_ignore_none
def get_supported_barcode_model_codes_map():
    """Return a mapping of barcode model type codes to the model class."""
    return {
        model.barcode_model_type_code(): model
        for model in get_supported_barcode_models()
    }
