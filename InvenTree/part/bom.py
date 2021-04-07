"""
Functionality for Bill of Material (BOM) management.
Primarily BOM upload tools.
"""

from rapidfuzz import fuzz
import tablib
import os

from collections import OrderedDict

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

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
                stock_data.append(bom_item.sub_part.get_default_location().name)
            except AttributeError:
                stock_data.append('')
            # Get part current stock
            stock_data.append(bom_item.sub_part.available_stock)

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

                if manufacturer_part:
                    manufacturer_name = manufacturer_part.manufacturer.name
                else:
                    manufacturer_name = ''

                manufacturer_mpn = manufacturer_part.MPN

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

                    if supplier_part.supplier:
                        supplier_name = supplier_part.supplier.name
                    else:
                        supplier_name = ''

                    supplier_sku = supplier_part.SKU

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

    filename = '{n}_BOM.{fmt}'.format(n=part.full_name, fmt=fmt)

    return DownloadFile(data, filename)
    

class BomUploadManager:
    """ Class for managing an uploaded BOM file """

    # Fields which are absolutely necessary for valid upload
    REQUIRED_HEADERS = [
        'Quantity'
    ]

    # Fields which are used for part matching (only one of them is needed)
    PART_MATCH_HEADERS = [
        'Part_Name',
        'Part_IPN',
        'Part_ID',
    ]
    
    # Fields which would be helpful but are not required
    OPTIONAL_HEADERS = [
        'Reference',
        'Note',
        'Overage',
    ]

    EDITABLE_HEADERS = [
        'Reference',
        'Note',
        'Overage'
    ]

    HEADERS = REQUIRED_HEADERS + PART_MATCH_HEADERS + OPTIONAL_HEADERS

    def __init__(self, bom_file):
        """ Initialize the BomUpload class with a user-uploaded file object """
        
        self.process(bom_file)

    def process(self, bom_file):
        """ Process a BOM file """

        self.data = None

        ext = os.path.splitext(bom_file.name)[-1].lower()

        if ext in ['.csv', '.tsv', ]:
            # These file formats need string decoding
            raw_data = bom_file.read().decode('utf-8')
        elif ext in ['.xls', '.xlsx']:
            raw_data = bom_file.read()
        else:
            raise ValidationError({'bom_file': _('Unsupported file format: {f}').format(f=ext)})

        try:
            self.data = tablib.Dataset().load(raw_data)
        except tablib.UnsupportedFormat:
            raise ValidationError({'bom_file': _('Error reading BOM file (invalid data)')})
        except tablib.core.InvalidDimensions:
            raise ValidationError({'bom_file': _('Error reading BOM file (incorrect row size)')})

    def guess_header(self, header, threshold=80):
        """ Try to match a header (from the file) to a list of known headers
        
        Args:
            header - Header name to look for
            threshold - Match threshold for fuzzy search
        """

        # Try for an exact match
        for h in self.HEADERS:
            if h == header:
                return h

        # Try for a case-insensitive match
        for h in self.HEADERS:
            if h.lower() == header.lower():
                return h

        # Try for a case-insensitive match with space replacement
        for h in self.HEADERS:
            if h.lower() == header.lower().replace(' ', '_'):
                return h

        # Finally, look for a close match using fuzzy matching
        matches = []

        for h in self.HEADERS:
            ratio = fuzz.partial_ratio(header, h)
            if ratio > threshold:
                matches.append({'header': h, 'match': ratio})

        if len(matches) > 0:
            matches = sorted(matches, key=lambda item: item['match'], reverse=True)
            return matches[0]['header']

        return None
    
    def columns(self):
        """ Return a list of headers for the thingy """
        headers = []

        for header in self.data.headers:
            headers.append({
                'name': header,
                'guess': self.guess_header(header)
            })

        return headers

    def col_count(self):
        if self.data is None:
            return 0

        return len(self.data.headers)

    def row_count(self):
        """ Return the number of rows in the file. """

        if self.data is None:
            return 0

        return len(self.data)

    def rows(self):
        """ Return a list of all rows """
        rows = []

        for i in range(self.row_count()):

            data = [item for item in self.get_row_data(i)]

            # Is the row completely empty? Skip!
            empty = True

            for idx, item in enumerate(data):
                if len(str(item).strip()) > 0:
                    empty = False

                try:
                    # Excel import casts number-looking-items into floats, which is annoying
                    if item == int(item) and not str(item) == str(int(item)):
                        data[idx] = int(item)
                except ValueError:
                    pass

            # Skip empty rows
            if empty:
                continue

            row = {
                'data': data,
                'index': i
            }

            rows.append(row)

        return rows

    def get_row_data(self, index):
        """ Retrieve row data at a particular index """
        if self.data is None or index >= len(self.data):
            return None

        return self.data[index]

    def get_row_dict(self, index):
        """ Retrieve a dict object representing the data row at a particular offset """

        if self.data is None or index >= len(self.data):
            return None

        return self.data.dict[index]
