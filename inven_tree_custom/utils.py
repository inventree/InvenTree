# inven_tree_custom/utils.py
from datetime import datetime

# It's assumed that InvenTree's models (like StockItem) would be importable here
# e.g., from stock.models import StockItem
# For now, we'll proceed without direct model imports if they are not available
# to the standalone execution of this subtask, but they will be needed in plugin.py.

def generate_pn(instance):
    """
    Generates a product number based on shift, date, month code, and serial.
    'instance' is expected to be a StockItem model instance.
    """
    now = datetime.now()

    # Determine Shift (A for 0-11 AM, B for 12-23 PM)
    shift = 'A' if now.hour < 12 else 'B'

    # Determine Day (DD)
    day_str = now.strftime('%d')

    # Determine Month Code (e.g., JAN, FEB)
    month_code = now.strftime('%b').upper()

    # --- Serial Number Generation ---
    # This is a placeholder and needs to be replaced with a proper database query
    # to count existing items for the current date and shift.
    # For example, something like:
    # current_date = now.date()
    # count = StockItem.objects.filter(
    #     creation_date__date=current_date,
    #     # This part is tricky: how to filter by shift?
    #     # If product_number stores the shift, we can parse it.
    #     # Or, if another field stores shift or creation time precisely.
    #     # product_number__startswith=f"{shift}-" # This is an approximation
    # ).count()
    # serial = count + 1
    # serial_str = f"{serial:03d}"
    #
    # For now, using a fixed serial.
    # IMPORTANT: Replace this with a robust serial number generation logic.
    serial_str = "001"  # Placeholder
    # --- End Serial Number Generation ---

    product_number = f"{shift}-{day_str}{month_code}-{serial_str}"
    
    return product_number
