"""Validation methods for the build app"""


def generate_next_build_reference():
    """Generate the next available BuildOrder reference"""

    from build.models import Build

    return Build.generate_reference()


def validate_build_order_reference_pattern(pattern):
    """Validate the BuildOrder reference 'pattern' setting"""

    from build.models import Build

    Build.validate_reference_pattern(pattern)


def validate_build_order_reference(value):
    """Validate that the BuildOrder reference field matches the required pattern.

    This function is exposed to any Validation plugins, and thus can be customized.
    """

    from build.models import Build
    from plugin.registry import registry

    plugins = registry.with_mixin('validation')

    for plugin in plugins:
        # Run the reference through each custom validator
        # If the plugin returns 'True' we will skip any subsequent validation
        if plugin.validate_build_order_reference(value):
            return

    # If we get to here, run the "default" validation routine
    Build.validate_reference_field(value)
