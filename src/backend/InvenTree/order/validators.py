"""Validation methods for the order app."""


def generate_next_sales_order_reference():
    """Generate the next available SalesOrder reference."""
    from order.models import SalesOrder

    return SalesOrder.generate_reference()


def generate_next_purchase_order_reference():
    """Generate the next available PurchasesOrder reference."""
    from order.models import PurchaseOrder

    return PurchaseOrder.generate_reference()


def generate_next_return_order_reference():
    """Generate the next available ReturnOrder reference."""
    from order.models import ReturnOrder

    return ReturnOrder.generate_reference()


def validate_sales_order_reference_pattern(pattern):
    """Validate the SalesOrder reference 'pattern' setting."""
    from order.models import SalesOrder

    SalesOrder.validate_reference_pattern(pattern)


def validate_purchase_order_reference_pattern(pattern):
    """Validate the PurchaseOrder reference 'pattern' setting."""
    from order.models import PurchaseOrder

    PurchaseOrder.validate_reference_pattern(pattern)


def validate_return_order_reference_pattern(pattern):
    """Validate the ReturnOrder reference 'pattern' setting."""
    from order.models import ReturnOrder

    ReturnOrder.validate_reference_pattern(pattern)


def validate_sales_order_reference(value):
    """Validate that the SalesOrder reference field matches the required pattern."""
    from order.models import SalesOrder

    SalesOrder.validate_reference_field(value)


def validate_purchase_order_reference(value):
    """Validate that the PurchaseOrder reference field matches the required pattern."""
    from order.models import PurchaseOrder

    PurchaseOrder.validate_reference_field(value)


def validate_return_order_reference(value):
    """Validate that the ReturnOrder reference field matches the required pattern."""
    from order.models import ReturnOrder

    ReturnOrder.validate_reference_field(value)
