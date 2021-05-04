"""
Files management tools.
"""

from rapidfuzz import fuzz
import tablib
import os

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

# from company.models import ManufacturerPart, SupplierPart


class FileManager:
    """ Class for managing an uploaded file """

    name = ''

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
    ]

    EDITABLE_HEADERS = [
    ]

    HEADERS = REQUIRED_HEADERS + PART_MATCH_HEADERS + OPTIONAL_HEADERS

    def __init__(self, file, name=None):
        """ Initialize the FileManager class with a user-uploaded file object """
        
        # Set name
        if name:
            self.name = name

        # Process initial file
        self.process(file)

    def process(self, file):
        """ Process file """

        self.data = None

        ext = os.path.splitext(file.name)[-1].lower()

        if ext in ['.csv', '.tsv', ]:
            # These file formats need string decoding
            raw_data = file.read().decode('utf-8')
        elif ext in ['.xls', '.xlsx']:
            raw_data = file.read()
        else:
            raise ValidationError(_(f'Unsupported file format: {ext}'))

        try:
            self.data = tablib.Dataset().load(raw_data)
        except tablib.UnsupportedFormat:
            raise ValidationError(_(f'Error reading {self.name} file (invalid format)'))
        except tablib.core.InvalidDimensions:
            raise ValidationError(_(f'Error reading {self.name} file (incorrect dimension)'))

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
