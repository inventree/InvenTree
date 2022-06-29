"""Validation methods for the build app"""


def validate_build_reference_pattern(pattern):
    """Validate the BuildOrder reference 'pattern' setting"""

    from build.models import Build

    Build.validate_reference_pattern(pattern)
