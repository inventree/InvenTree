# Map ECIA Data Identifier to human readable identifier
# The following identifiers haven't been implemented: 3S, 4S, 5S, S
DATA_IDENTIFIER_MAP = {
    "K":   "purchase_order_number",
    "1K":  "purchase_order_number",    # DigiKey uses 1K instead of K
    "11K": "packing_list_number",
    "6D":  "ship_date",
    "P":   "supplier_part_number",     # "Customer Part Number"
    "1P":  "manufacturer_part_number", # "Supplier Part Number"
    "4K":  "purchase_order_line",
    "14K": "purchase_order_line",      # Mouser uses 14K instead of 4K
    "Q":   "quantity",
    "9D":  "date_yyww",
    "10D": "date_yyww",
    "1T":  "lot_code",
    "4L":  "country_of_origin",
    "1V":  "manufacturer"
}

def parse_ecia_barcode2d(barcode_data: str) -> dict[str, str]:
    """Parse a standard ECIA 2D barcode, according to
    https://www.ecianow.org/assets/docs/ECIA_Specifications.pdf
    """

    if not (data_split := parse_isoiec_15434_barcode2d(barcode_data)):
        return None

    barcode_fields = {}
    for entry in data_split:
        for identifier, field_name in DATA_IDENTIFIER_MAP.items():
            if entry.startswith(identifier):
                barcode_fields[field_name] = entry[len(identifier):]
                break

    return barcode_fields

def parse_isoiec_15434_barcode2d(barcode_data: str) -> list[str]:
    HEADER = "[)>\x1E06\x1D"
    TRAILER = "\x1E\x04"

    # some old mouser barcodes start with this messed up header
    OLD_MOUSER_HEADER = ">[)>06\x1D"
    if barcode_data.startswith(OLD_MOUSER_HEADER):
        barcode_data = barcode_data.replace(OLD_MOUSER_HEADER, HEADER, 1)

    # most barcodes don't include the trailer, because "why would you stick to
    # the standard, right?" so we only check for the header here
    if not barcode_data.startswith(HEADER):
        return

    actual_data = barcode_data.split(HEADER, 1)[1].rsplit(TRAILER, 1)[0]

    return actual_data.split("\x1D")
