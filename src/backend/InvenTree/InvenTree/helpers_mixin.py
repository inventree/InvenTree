"""Provides helper mixins that are used throughout the InvenTree project."""

import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.cache import cache

from plugin import registry as plg_registry


class ClassValidationMixin:
    """Mixin to validate class attributes and overrides.

    Class attributes:
        required_attributes: List of class attributes that need to be defined
        required_overrides: List of functions that need override, a nested list mean either one of them needs an override

    Example:
    ```py
    class Parent(ClassValidationMixin):
        NAME: str
        def test(self):
            pass

        required_attributes = ["NAME"]
        required_overrides = [test]

    class MyClass(Parent):
        pass

    myClass = MyClass()
    myClass.validate() # raises NotImplementedError
    ```
    """

    required_attributes = []
    required_overrides = []

    @classmethod
    def validate(cls):
        """Validate the class against the required attributes/overrides."""

        def attribute_missing(key):
            """Check if attribute is missing."""
            return not hasattr(cls, key) or getattr(cls, key) == ''

        def override_missing(base_implementation):
            """Check if override is missing."""
            if isinstance(base_implementation, list):
                return all(override_missing(x) for x in base_implementation)

            return base_implementation == getattr(
                cls, base_implementation.__name__, None
            )

        missing_attributes = list(filter(attribute_missing, cls.required_attributes))
        missing_overrides = list(filter(override_missing, cls.required_overrides))

        errors = []

        if len(missing_attributes) > 0:
            errors.append(
                f'did not provide the following attributes: {", ".join(missing_attributes)}'
            )
        if len(missing_overrides) > 0:
            missing_overrides_list = []
            for base_implementation in missing_overrides:
                if isinstance(base_implementation, list):
                    missing_overrides_list.append(
                        'one of '
                        + ' or '.join(attr.__name__ for attr in base_implementation)
                    )
                else:
                    missing_overrides_list.append(base_implementation.__name__)
            errors.append(
                f'did not override the required attributes: {", ".join(missing_overrides_list)}'
            )

        if len(errors) > 0:
            raise NotImplementedError(f"'{cls}' " + ' and '.join(errors))


class ClassProviderMixin:
    """Mixin to get metadata about a class itself, e.g. the plugin that provided that class."""

    @classmethod
    def get_provider_file(cls):
        """File that contains the Class definition."""
        return inspect.getfile(cls)

    @classmethod
    def get_provider_plugin(cls):
        """Plugin that contains the Class definition, otherwise None."""
        for plg in plg_registry.plugins.values():
            if plg.package_path == cls.__module__:
                return plg

    @classmethod
    def get_is_builtin(cls):
        """Is this Class build in the InvenTree source code?"""
        try:
            Path(cls.get_provider_file()).relative_to(settings.BASE_DIR)
            return True
        except ValueError:
            # Path(...).relative_to throws an ValueError if its not relative to the InvenTree source base dir
            return False


def get_shared_class_instance_state_mixin(get_state_key: Callable[[type], str]):
    """Get a mixin class that provides shared state for classes across the main application and worker.

    Arguments:
        get_state_key: A function that returns the key for the shared state when given a class instance.
    """

    class SharedClassStateMixinClass:
        """Mixin to provide shared state for classes across the main application and worker."""

        def set_shared_state(self, key: str, value: Any):
            """Set a shared state value for this machine.

            Arguments:
                key: The key for the shared state
                value: The value to set
            """
            cache.set(self._get_key(key), value, timeout=None)

        def get_shared_state(self, key: str, default=None):
            """Get a shared state value for this machine.

            Arguments:
                key: The key for the shared state
                default: The default value to return if the key does not exist
            """
            return cache.get(self._get_key(key)) or default

        def _get_key(self, key: str):
            """Get the key for this class instance."""
            return f'{get_state_key(self)}:{key}'

    return SharedClassStateMixinClass
