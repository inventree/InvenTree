"""Registry for supported serializers for data import operations."""

import logging

from rest_framework.serializers import Serializer

logger = logging.getLogger('inventree')


class DataImportSerializerRegister:
    """Registry for supported serializers for data import operations.

    To add a new serializer to the registry, add the @register_importer decorator to the serializer class.
    """

    supported_serializers: list[Serializer] = []

    def register(self, serializer: Serializer):
        """Register a new serializer with the importer registry."""
        if not isinstance(serializer, Serializer) and not issubclass(
            serializer, Serializer
        ):
            logger.error(f'Invalid serializer type: %s', type(serializer))
            return

        logger.debug('Registering serializer class for import: %s', type(serializer))

        if serializer not in self.supported_serializers:
            self.supported_serializers.append(serializer)


_serializer_registry = DataImportSerializerRegister()


def get_supported_serializers():
    """Return a list of supported serializers which can be used for importing data."""
    return _serializer_registry.supported_serializers


def register_importer():
    """Decorator function to register a serializer with the importer registry."""

    def _decorator(cls):
        _serializer_registry.register(cls)
        return cls

    return _decorator
