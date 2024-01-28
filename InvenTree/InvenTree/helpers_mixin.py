"""Provides helper mixins that are used throughout the InvenTree project."""

import inspect
from pathlib import Path

from django.conf import settings

from plugin import registry as plg_registry


class ClassValidationMixin:
    """Mixin to validate class attributes and overrides.

    Class attributes:
        required_attributes: List of class attributes that need to be defined
        required_overrides: List of functions that need override

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
            return base_implementation == getattr(
                cls, base_implementation.__name__, None
            )

        missing_attributes = list(filter(attribute_missing, cls.required_attributes))
        missing_overrides = list(filter(override_missing, cls.required_overrides))

        errors = []

        if len(missing_attributes) > 0:
            errors.append(
                f"did not provide the following attributes: {', '.join(missing_attributes)}"
            )
        if len(missing_overrides) > 0:
            errors.append(
                f"did not override the required attributes: {', '.join(attr.__name__ for attr in missing_overrides)}"
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
        """Is this Class build in the Inventree source code?"""
        try:
            Path(cls.get_provider_file()).relative_to(settings.BASE_DIR)
            return True
        except ValueError:
            # Path(...).relative_to throws an ValueError if its not relative to the InvenTree source base dir
            return False
