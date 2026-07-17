"""Validation methods for the build app."""


def generate_next_build_reference():
    """Generate the next available BuildOrder reference."""
    from build.models import Build

    return Build.generate_reference()


def validate_build_order_reference_pattern(pattern):
    """Validate the BuildOrder reference 'pattern' setting."""
    from build.models import Build

    Build.validate_reference_pattern(pattern)


def validate_build_order_reference(value):
    """Validate that the BuildOrder reference field matches the required pattern."""
    from build.models import Build

    # If we get to here, run the "default" validation routine
    Build.validate_reference_field(value)


def check_build_output(output, quantity=None):
    """Run a validation check against each output before accepting it for completion.

    Arguments:
        output (StockItem): The build output to check
        quantity (Decimal, optional): The quantity to complete. If None, the full output quantity is assumed.
    """
    output.build.can_complete_output(output, quantity=quantity)
