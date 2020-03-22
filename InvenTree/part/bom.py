"""
Functionality for Bill of Material (BOM) management.
Primarily BOM upload tools.
"""

from rapidfuzz import fuzz
import tablib
import os

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from InvenTree.helpers import DownloadFile, GetExportFormats

from .admin import BomItemResource
from .models import BomItem


def IsValidBOMFormat(fmt):
    """ Test if a file format specifier is in the valid list of BOM file formats """

    return fmt.strip().lower() in GetExportFormats()


def MakeBomTemplate(fmt):
    """ Generate a Bill of Materials upload template file (for user download) """

    fmt = fmt.strip().lower()

    if not IsValidBOMFormat(fmt):
        fmt = 'csv'

    query = BomItem.objects.filter(pk=None)
    dataset = BomItemResource().export(queryset=query)

    data = dataset.export(fmt)

    filename = 'InvenTree_BOM_Template.' + fmt

    return DownloadFile(data, filename)


def ExportBom(part, fmt='csv', cascade=False):
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

            item.level = '-' * level

            # Avoid circular BOM references
            if item.pk in uids:
                continue

            bom_items.append(item)

            if item.sub_part.assembly:
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
    data = dataset.export(fmt)

    filename = '{n}_BOM.{fmt}'.format(n=part.full_name, fmt=fmt)

    return DownloadFile(data, filename)
    

class BomUploadManager:
    """ Class for managing an uploaded BOM file """

    # Fields which are absolutely necessary for valid upload
    REQUIRED_HEADERS = [
        'Part',
        'Quantity'
    ]
    
    # Fields which would be helpful but are not required
    OPTIONAL_HEADERS = [
        'Reference',
        'Notes',
        'Overage',
        'Description',
        'Category',
        'Supplier',
        'Manufacturer',
        'MPN',
        'IPN',
    ]

    EDITABLE_HEADERS = [
        'Reference',
        'Notes'
    ]

    HEADERS = REQUIRED_HEADERS + OPTIONAL_HEADERS

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
            raise ValidationError({'bom_file': _('Unsupported file format: {f}'.format(f=ext))})

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
