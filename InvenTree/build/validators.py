"""Validation methods for the build app"""


def generate_next_build_reference():
    """Generate the next available BuildOrder reference"""

    from build.models import Build

    return Build.generate_reference()


def validate_build_reference_pattern(pattern):
    """Validate the BuildOrder reference 'pattern' setting"""

    from build.models import Build

    Build.validate_reference_pattern(pattern)


def validate_build_order_reference(value):
    """Validate that the BuildOrder reference field matches the required pattern"""

    from build.models import Build

    Build.validate_reference_field(value)
