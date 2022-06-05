"""Functionality for Bill of Material (BOM) management.

Primarily BOM upload tools.
"""

from collections import OrderedDict

from django.utils.translation import gettext as _

from company.models import ManufacturerPart, SupplierPart
from InvenTree.helpers import DownloadFile, GetExportFormats, normalize

from .admin import BomItemResource
from .models import BomItem, Part


def IsValidBOMFormat(fmt):
    """Test if a file format specifier is in the valid list of BOM file formats."""
    return fmt.strip().lower() in GetExportFormats()


def MakeBomTemplate(fmt):
    """Generate a Bill of Materials upload template file (for user download)."""
    fmt = fmt.strip().lower()

    if not IsValidBOMFormat(fmt):
        fmt = 'csv'

    # Create an "empty" queryset, essentially.
    # This will then export just the row headers!
    query = BomItem.objects.filter(pk=None)

    dataset = BomItemResource().export(
        queryset=query,
        importing=True
    )

    data = dataset.export(fmt)

    filename = 'InvenTree_BOM_Template.' + fmt

    return DownloadFile(data, filename)


def ExportBom(part: Part, fmt='csv', cascade: bool = False, max_levels: int = None, parameter_data=False, stock_data=False, supplier_data=False, manufacturer_data=False):
    """Export a BOM (Bill of Materials) for a given part.

    Args:
        part (Part): Part for which the BOM should be exported
        fmt (str, optional): file format. Defaults to 'csv'.
        cascade (bool, optional): If True, multi-level BOM output is supported. Otherwise, a flat top-level-only BOM is exported.. Defaults to False.
        max_levels (int, optional): Levels of items that should be included. None for np sublevels. Defaults to None.
        parameter_data (bool, optional): Additonal data that should be added. Defaults to False.
        stock_data (bool, optional): Additonal data that should be added. Defaults to False.
        supplier_data (bool, optional): Additonal data that should be added. Defaults to False.
        manufacturer_data (bool, optional): Additonal data that should be added. Defaults to False.

    Returns:
        StreamingHttpResponse: Response that can be passed to the endpoint
    """
    if not IsValidBOMFormat(fmt):
        fmt = 'csv'

    bom_items = []

    uids = []

    def add_items(items, level, cascade=True):
        # Add items at a given layer
        for item in items:

            item.level = str(int(level))

            # Avoid circular BOM references
            if item.pk in uids:
                continue

            bom_items.append(item)

            if cascade and item.sub_part.assembly:
                if max_levels is None or level < max_levels:
                    add_items(item.sub_part.bom_items.all().order_by('id'), level + 1)

    top_level_items = part.get_bom_items().order_by('id')

    add_items(top_level_items, 1, cascade)

    dataset = BomItemResource().export(queryset=bom_items, cascade=cascade)

    def add_columns_to_dataset(columns, column_size):
        try:
            for header, column_dict in columns.items():
                # Construct column tuple
                col = tuple(column_dict.get(c_idx, '') for c_idx in range(column_size))
                # Add column to dataset
                dataset.append_col(col, header=header)
        except AttributeError:
            pass

    if parameter_data:
        """If requested, add extra columns for each PartParameter associated with each line item."""

        parameter_cols = {}

        for b_idx, bom_item in enumerate(bom_items):
            # Get part parameters
            parameters = bom_item.sub_part.get_parameters()
            # Add parameters to columns
            if parameters:
                for parameter in parameters:
                    name = parameter.template.name
                    value = parameter.data

                    try:
                        parameter_cols[name].update({b_idx: value})
                    except KeyError:
                        parameter_cols[name] = {b_idx: value}

        # Add parameter columns to dataset
        parameter_cols_ordered = OrderedDict(sorted(parameter_cols.items(), key=lambda x: x[0]))
        add_columns_to_dataset(parameter_cols_ordered, len(bom_items))

    if stock_data:
        """If requested, add extra columns for stock data associated with each line item."""

        stock_headers = [
            _('Default Location'),
            _('Total Stock'),
            _('Available Stock'),
            _('On Order'),
        ]

        stock_cols = {}

        for b_idx, bom_item in enumerate(bom_items):

            stock_data = []

            sub_part = bom_item.sub_part

            # Get part default location
            try:
                loc = sub_part.get_default_location()

                if loc is not None:
                    stock_data.append(str(loc.name))
                else:
                    stock_data.append('')
            except AttributeError:
                stock_data.append('')

            # Total "in stock" quantity for this part
            stock_data.append(
                str(normalize(sub_part.total_stock))
            )

            # Total "available stock" quantity for this part
            stock_data.append(
                str(normalize(sub_part.available_stock))
            )

            # Total "on order" quantity for this part
            stock_data.append(
                str(normalize(sub_part.on_order))
            )

            for s_idx, header in enumerate(stock_headers):
                try:
                    stock_cols[header].update({b_idx: stock_data[s_idx]})
                except KeyError:
                    stock_cols[header] = {b_idx: stock_data[s_idx]}

        # Add stock columns to dataset
        add_columns_to_dataset(stock_cols, len(bom_items))

    if manufacturer_data or supplier_data:
        """If requested, add extra columns for each SupplierPart and ManufacturerPart associated with each line item."""

        # Keep track of the supplier parts we have already exported
        supplier_parts_used = set()

        manufacturer_cols = {}

        for bom_idx, bom_item in enumerate(bom_items):
            # Get part instance
            b_part = bom_item.sub_part

            # Include manufacturer data for each BOM item
            if manufacturer_data:

                # Filter manufacturer parts
                manufacturer_parts = ManufacturerPart.objects.filter(part__pk=b_part.pk).prefetch_related('supplier_parts')

                for mp_idx, mp_part in enumerate(manufacturer_parts):

                    # Extract the "name" field of the Manufacturer (Company)
                    if mp_part and mp_part.manufacturer:
                        manufacturer_name = mp_part.manufacturer.name
                    else:
                        manufacturer_name = ''

                    # Extract the "MPN" field from the Manufacturer Part
                    if mp_part:
                        manufacturer_mpn = mp_part.MPN
                    else:
                        manufacturer_mpn = ''

                    # Generate a column name for this manufacturer
                    k_man = f'{_("Manufacturer")}_{mp_idx}'
                    k_mpn = f'{_("MPN")}_{mp_idx}'

                    try:
                        manufacturer_cols[k_man].update({bom_idx: manufacturer_name})
                        manufacturer_cols[k_mpn].update({bom_idx: manufacturer_mpn})
                    except KeyError:
                        manufacturer_cols[k_man] = {bom_idx: manufacturer_name}
                        manufacturer_cols[k_mpn] = {bom_idx: manufacturer_mpn}

                    # We wish to include supplier data for this manufacturer part
                    if supplier_data:

                        for sp_idx, sp_part in enumerate(mp_part.supplier_parts.all()):

                            supplier_parts_used.add(sp_part)

                            if sp_part.supplier:
                                supplier_name = sp_part.supplier.name
                            else:
                                supplier_name = ''

                            if sp_part:
                                supplier_sku = sp_part.SKU
                            else:
                                supplier_sku = ''

                            # Generate column names for this supplier
                            k_sup = str(_("Supplier")) + "_" + str(mp_idx) + "_" + str(sp_idx)
                            k_sku = str(_("SKU")) + "_" + str(mp_idx) + "_" + str(sp_idx)

                            try:
                                manufacturer_cols[k_sup].update({bom_idx: supplier_name})
                                manufacturer_cols[k_sku].update({bom_idx: supplier_sku})
                            except KeyError:
                                manufacturer_cols[k_sup] = {bom_idx: supplier_name}
                                manufacturer_cols[k_sku] = {bom_idx: supplier_sku}

            if supplier_data:
                # Add in any extra supplier parts, which are not associated with a manufacturer part

                for sp_idx, sp_part in enumerate(SupplierPart.objects.filter(part__pk=b_part.pk)):

                    if sp_part in supplier_parts_used:
                        continue

                    supplier_parts_used.add(sp_part)

                    if sp_part.supplier:
                        supplier_name = sp_part.supplier.name
                    else:
                        supplier_name = ''

                    supplier_sku = sp_part.SKU

                    # Generate column names for this supplier
                    k_sup = str(_("Supplier")) + "_" + str(sp_idx)
                    k_sku = str(_("SKU")) + "_" + str(sp_idx)

                    try:
                        manufacturer_cols[k_sup].update({bom_idx: supplier_name})
                        manufacturer_cols[k_sku].update({bom_idx: supplier_sku})
                    except KeyError:
                        manufacturer_cols[k_sup] = {bom_idx: supplier_name}
                        manufacturer_cols[k_sku] = {bom_idx: supplier_sku}

        # Add supplier columns to dataset
        add_columns_to_dataset(manufacturer_cols, len(bom_items))

    data = dataset.export(fmt)

    filename = f"{part.full_name}_BOM.{fmt}"

    return DownloadFile(data, filename)
