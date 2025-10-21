"""Registry for supported serializers for data import operations."""

import structlog
from rest_framework.serializers import Serializer

from importer.mixins import DataImportSerializerMixin

logger = structlog.get_logger('inventree')


class DataImportSerializerRegister:
    """Registry for supported serializers for data import operations.

    To add a new serializer to the registry, add the @register_importer decorator to the serializer class.
    """

    supported_serializers: list[Serializer] = []

    def register(self, serializer) -> None:
        """Register a new serializer with the importer registry."""
        if not issubclass(serializer, DataImportSerializerMixin):
            logger.debug('Invalid serializer class: %s', type(serializer))
            return

        if not issubclass(serializer, Serializer):
            logger.debug('Invalid serializer class: %s', type(serializer))
            return

        logger.debug('Registering serializer class for import: %s', type(serializer))

        if serializer not in self.supported_serializers:
            self.supported_serializers.append(serializer)


_serializer_registry = DataImportSerializerRegister()


def get_supported_serializers():
    """Return a list of supported serializers which can be used for importing data."""
    return _serializer_registry.supported_serializers


def supported_models():
    """Return a map of supported models to their respective serializers."""
    data = {}

    for serializer in get_supported_serializers():
        model = serializer.Meta.model
        data[model.__name__.lower()] = serializer

    return data


def supported_model_options():
    """Return a list of supported model options for importing data."""
    options = []

    for model_name, serializer in supported_models().items():
        options.append((model_name, serializer.Meta.model._meta.verbose_name))

    return options


def register_importer():
    """Decorator function to register a serializer with the importer registry."""

    def _decorator(cls):
        _serializer_registry.register(cls)
        return cls

    return _decorator
