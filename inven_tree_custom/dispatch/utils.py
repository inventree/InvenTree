# inven_tree_custom/dispatch/utils.py
from collections import defaultdict
from decimal import Decimal, InvalidOperation # Ensure InvalidOperation is imported

def get_dispatch_summary_data(dispatch_instance):
    """
    Processes items in a dispatch to group them by Quality, Color category (White/Colored),
    and Product Type (Roll/Patti), calculating counts and weight sums.

    Args:
        dispatch_instance: The Dispatch model instance.

    Returns:
        A dictionary containing the structured summary data.
        Example structure:
        {
            'Total Items': 15,
            'Total Net Weight': Decimal('150.75'),
            'Total Gross Weight': Decimal('160.20'),
            'Groups': {
                'Good Quality': {
                    'White': {
                        'Roll': {'count': 5, 'net_weight': Decimal('50.0'), 'gross_weight': Decimal('55.0')},
                        'Patti': {'count': 2, 'net_weight': Decimal('10.5'), 'gross_weight': Decimal('12.0')}
                    },
                    'Colored': {
                        'Roll': {'count': 3, 'net_weight': Decimal('30.0'), 'gross_weight': Decimal('33.0')}
                    }
                },
                # ... other quality groups ...
            }
        }
    """
    summary = {
        'Total Items': 0,
        'Total Net Weight': Decimal('0.00'),
        'Total Gross Weight': Decimal('0.00'),
        'Groups': defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
            'count': 0,
            'net_weight': Decimal('0.00'),
            'gross_weight': Decimal('0.00')
        })))
    }

    # These parameter names must match exactly what's defined in InvenTree Parameter Templates
    PARAM_QUALITY = "Quality"
    PARAM_COLOUR = "Colour"
    PARAM_PRODUCT_TYPE = "Product Type"
    PARAM_NET_WEIGHT = "Net Weight"
    PARAM_GROSS_WEIGHT = "Gross Weight"

    # Define which colours are considered "White"
    WHITE_COLOUR_VALUES = ['white', 'off-white', 'natural'] # Case-insensitive matching will be used

    dispatch_items = dispatch_instance.items.all().select_related('stock_item', 'stock_item__part')

    for item in dispatch_items:
        stock_item = item.stock_item
        if not stock_item:
            continue

        summary['Total Items'] += 1 # Assuming item.quantity represents units of this stock_item
                                    # If item.quantity can be > 1 for a single stock_item line, this needs adjustment.
                                    # The issue implies unique StockItem per DispatchItem.

        # Get parameter values from the StockItem
        # InvenTree's get_parameter method is case-sensitive for parameter names.
        quality = stock_item.get_parameter(PARAM_QUALITY)
        colour = stock_item.get_parameter(PARAM_COLOUR)
        product_type = stock_item.get_parameter(PARAM_PRODUCT_TYPE)
        
        try:
            net_weight_str = stock_item.get_parameter(PARAM_NET_WEIGHT)
            net_weight = Decimal(net_weight_str) if net_weight_str else Decimal('0.00')
        except (TypeError, ValueError, InvalidOperation): # Catch InvalidOperation as well
            net_weight = Decimal('0.00')

        try:
            gross_weight_str = stock_item.get_parameter(PARAM_GROSS_WEIGHT)
            gross_weight = Decimal(gross_weight_str) if gross_weight_str else Decimal('0.00')
        except (TypeError, ValueError, InvalidOperation): # Catch InvalidOperation as well
            gross_weight = Decimal('0.00')

        # Accumulate total weights (multiplied by dispatch item quantity)
        # Ensure item.quantity is treated as Decimal if it can be fractional,
        # or ensure it's compatible with Decimal multiplication.
        item_quantity_decimal = Decimal(str(item.quantity)) # Convert quantity to Decimal for consistent math

        current_item_total_net_weight = net_weight * item_quantity_decimal
        current_item_total_gross_weight = gross_weight * item_quantity_decimal
        summary['Total Net Weight'] += current_item_total_net_weight
        summary['Total Gross Weight'] += current_item_total_gross_weight

        # Determine color category
        color_category = "Colored" # Default
        if colour and isinstance(colour, str) and colour.lower() in WHITE_COLOUR_VALUES:
            color_category = "White"
        
        # Normalize parameter values for keys, handle None or empty strings
        quality_key = str(quality) if quality else "Unknown Quality"
        product_type_key = str(product_type) if product_type else "Unknown Type"

        # Grouping
        group = summary['Groups'][quality_key][color_category][product_type_key]
        
        # Based on the problem description, DispatchItem.quantity is the quantity of a specific StockItem.
        # So, group['count'] should accumulate these quantities if multiple units of the same *type*
        # (defined by quality, color, product_type) are dispatched, even if they are different StockItem instances.
        # However, the example shows 'count' as number of lines.
        # If 'count' is number of lines:
        group['count'] += 1 
        # If 'count' is total units of items in that group:
        # group['count'] += item_quantity_decimal

        # The prompt's example data implies group['count'] is the number of lines/DispatchItems.
        # Let's stick to that interpretation for group['count'].
        # The total weight calculation already correctly uses item.quantity.

        group['net_weight'] += current_item_total_net_weight
        group['gross_weight'] += current_item_total_gross_weight
        
    # Convert defaultdicts to dicts for easier template rendering if necessary,
    # though Django templates usually handle defaultdicts fine.
    # This conversion needs to be recursive for nested defaultdicts.
    def convert_defaultdict_to_dict(d):
        if isinstance(d, defaultdict):
            d = {k: convert_defaultdict_to_dict(v) for k, v in d.items()}
        return d

    summary['Groups'] = convert_defaultdict_to_dict(summary['Groups'])
        
    return summary
