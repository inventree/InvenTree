"""
Functionality for Bill of Material (BOM) management.
Primarily BOM upload tools.
"""

from collections import OrderedDict

from django.utils.translation import gettext as _

from InvenTree.helpers import DownloadFile, GetExportFormats

from .admin import BomItemResource
from .models import BomItem
from company.models import ManufacturerPart, SupplierPart


def IsValidBOMFormat(fmt):
    """ Test if a file format specifier is in the valid list of BOM file formats """

    return fmt.strip().lower() in GetExportFormats()


def MakeBomTemplate(fmt):
    """ Generate a Bill of Materials upload template file (for user download) """

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


def ExportBom(part, fmt='csv', cascade=False, max_levels=None, parameter_data=False, stock_data=False, supplier_data=False, manufacturer_data=False):
    """ Export a BOM (Bill of Materials) for a given part.

    Args:
        fmt: File format (default = 'csv')
        cascade: If True, multi-level BOM output is supported. Otherwise, a flat top-level-only BOM is exported.
    """

    if not IsValidBOMFormat(fmt):
        fmt = 'csv'

    bom_items = []

    uids = []

    def add_items(items, level):
        # Add items at a given layer
        for item in items:

            item.level = str(int(level))

            # Avoid circular BOM references
            if item.pk in uids:
                continue

            bom_items.append(item)

            if item.sub_part.assembly:
                if max_levels is None or level < max_levels:
                    add_items(item.sub_part.bom_items.all().order_by('id'), level + 1)

    if cascade:
        # Cascading (multi-level) BOM

        # Start with the top level
        items_to_process = part.bom_items.all().order_by('id')

        add_items(items_to_process, 1)

    else:
        # No cascading needed - just the top-level items
        bom_items = [item for item in part.bom_items.all().order_by('id')]

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
        """
        If requested, add extra columns for each PartParameter associated with each line item
        """

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
        """
        If requested, add extra columns for stock data associated with each line item
        """

        stock_headers = [
            _('Default Location'),
            _('Available Stock'),
        ]

        stock_cols = {}

        for b_idx, bom_item in enumerate(bom_items):
            stock_data = []
            # Get part default location
            try:
                loc = bom_item.sub_part.get_default_location()

                if loc is not None:
                    stock_data.append(str(loc.name))
                else:
                    stock_data.append('')
            except AttributeError:
                stock_data.append('')
            # Get part current stock
            stock_data.append(str(bom_item.sub_part.available_stock))

            for s_idx, header in enumerate(stock_headers):
                try:
                    stock_cols[header].update({b_idx: stock_data[s_idx]})
                except KeyError:
                    stock_cols[header] = {b_idx: stock_data[s_idx]}

        # Add stock columns to dataset
        add_columns_to_dataset(stock_cols, len(bom_items))

    if manufacturer_data and supplier_data:
        """
        If requested, add extra columns for each SupplierPart and ManufacturerPart associated with each line item
        """

        # Expand dataset with manufacturer parts
        manufacturer_headers = [
            _('Manufacturer'),
            _('MPN'),
        ]

        supplier_headers = [
            _('Supplier'),
            _('SKU'),
        ]

        manufacturer_cols = {}

        for b_idx, bom_item in enumerate(bom_items):
            # Get part instance
            b_part = bom_item.sub_part

            # Filter manufacturer parts
            manufacturer_parts = ManufacturerPart.objects.filter(part__pk=b_part.pk)
            manufacturer_parts = manufacturer_parts.prefetch_related('supplier_parts')

            # Process manufacturer part
            for manufacturer_idx, manufacturer_part in enumerate(manufacturer_parts):

                if manufacturer_part and manufacturer_part.manufacturer:
                    manufacturer_name = manufacturer_part.manufacturer.name
                else:
                    manufacturer_name = ''

                if manufacturer_part:
                    manufacturer_mpn = manufacturer_part.MPN
                else:
                    manufacturer_mpn = ''

                # Generate column names for this manufacturer
                k_man = manufacturer_headers[0] + "_" + str(manufacturer_idx)
                k_mpn = manufacturer_headers[1] + "_" + str(manufacturer_idx)

                try:
                    manufacturer_cols[k_man].update({b_idx: manufacturer_name})
                    manufacturer_cols[k_mpn].update({b_idx: manufacturer_mpn})
                except KeyError:
                    manufacturer_cols[k_man] = {b_idx: manufacturer_name}
                    manufacturer_cols[k_mpn] = {b_idx: manufacturer_mpn}

                # Process supplier parts
                for supplier_idx, supplier_part in enumerate(manufacturer_part.supplier_parts.all()):

                    if supplier_part.supplier and supplier_part.supplier:
                        supplier_name = supplier_part.supplier.name
                    else:
                        supplier_name = ''

                    if supplier_part:
                        supplier_sku = supplier_part.SKU
                    else:
                        supplier_sku = ''

                    # Generate column names for this supplier
                    k_sup = str(supplier_headers[0]) + "_" + str(manufacturer_idx) + "_" + str(supplier_idx)
                    k_sku = str(supplier_headers[1]) + "_" + str(manufacturer_idx) + "_" + str(supplier_idx)

                    try:
                        manufacturer_cols[k_sup].update({b_idx: supplier_name})
                        manufacturer_cols[k_sku].update({b_idx: supplier_sku})
                    except KeyError:
                        manufacturer_cols[k_sup] = {b_idx: supplier_name}
                        manufacturer_cols[k_sku] = {b_idx: supplier_sku}

        # Add manufacturer columns to dataset
        add_columns_to_dataset(manufacturer_cols, len(bom_items))

    elif manufacturer_data:
        """
        If requested, add extra columns for each ManufacturerPart associated with each line item
        """

        # Expand dataset with manufacturer parts
        manufacturer_headers = [
            _('Manufacturer'),
            _('MPN'),
        ]

        manufacturer_cols = {}

        for b_idx, bom_item in enumerate(bom_items):
            # Get part instance
            b_part = bom_item.sub_part

            # Filter supplier parts
            manufacturer_parts = ManufacturerPart.objects.filter(part__pk=b_part.pk)

            for idx, manufacturer_part in enumerate(manufacturer_parts):

                if manufacturer_part:
                    manufacturer_name = manufacturer_part.manufacturer.name
                else:
                    manufacturer_name = ''

                manufacturer_mpn = manufacturer_part.MPN

                # Add manufacturer data to the manufacturer columns

                # Generate column names for this manufacturer
                k_man = manufacturer_headers[0] + "_" + str(idx)
                k_mpn = manufacturer_headers[1] + "_" + str(idx)

                try:
                    manufacturer_cols[k_man].update({b_idx: manufacturer_name})
                    manufacturer_cols[k_mpn].update({b_idx: manufacturer_mpn})
                except KeyError:
                    manufacturer_cols[k_man] = {b_idx: manufacturer_name}
                    manufacturer_cols[k_mpn] = {b_idx: manufacturer_mpn}

        # Add manufacturer columns to dataset
        add_columns_to_dataset(manufacturer_cols, len(bom_items))

    elif supplier_data:
        """
        If requested, add extra columns for each SupplierPart associated with each line item
        """

        # Expand dataset with manufacturer parts
        manufacturer_headers = [
            _('Supplier'),
            _('SKU'),
        ]

        manufacturer_cols = {}

        for b_idx, bom_item in enumerate(bom_items):
            # Get part instance
            b_part = bom_item.sub_part

            # Filter supplier parts
            supplier_parts = SupplierPart.objects.filter(part__pk=b_part.pk)

            for idx, supplier_part in enumerate(supplier_parts):

                if supplier_part.supplier:
                    supplier_name = supplier_part.supplier.name
                else:
                    supplier_name = ''

                supplier_sku = supplier_part.SKU

                # Add manufacturer data to the manufacturer columns

                # Generate column names for this supplier
                k_sup = manufacturer_headers[0] + "_" + str(idx)
                k_sku = manufacturer_headers[1] + "_" + str(idx)

                try:
                    manufacturer_cols[k_sup].update({b_idx: supplier_name})
                    manufacturer_cols[k_sku].update({b_idx: supplier_sku})
                except KeyError:
                    manufacturer_cols[k_sup] = {b_idx: supplier_name}
                    manufacturer_cols[k_sku] = {b_idx: supplier_sku}

        # Add manufacturer columns to dataset
        add_columns_to_dataset(manufacturer_cols, len(bom_items))

    data = dataset.export(fmt)

    filename = f"{part.full_name}_BOM.{fmt}"

    return DownloadFile(data, filename)
