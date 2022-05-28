"""Files management tools."""

import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import tablib
from rapidfuzz import fuzz


class FileManager:
    """Class for managing an uploaded file."""

    name = ''

    # Fields which are absolutely necessary for valid upload
    REQUIRED_HEADERS = []

    # Fields which are used for item matching (only one of them is needed)
    ITEM_MATCH_HEADERS = []

    # Fields which would be helpful but are not required
    OPTIONAL_HEADERS = []

    OPTIONAL_MATCH_HEADERS = []

    EDITABLE_HEADERS = []

    HEADERS = []

    def __init__(self, file, name=None):
        """Initialize the FileManager class with a user-uploaded file object."""
        # Set name
        if name:
            self.name = name

        # Process initial file
        self.process(file)

        # Update headers
        self.update_headers()

    @classmethod
    def validate(cls, file):
        """Validate file extension and data."""
        cleaned_data = None

        ext = os.path.splitext(file.name)[-1].lower().replace('.', '')

        try:
            if ext in ['csv', 'tsv', ]:
                # These file formats need string decoding
                raw_data = file.read().decode('utf-8')
                # Reset stream position to beginning of file
                file.seek(0)
            elif ext in ['xls', 'xlsx', 'json', 'yaml', ]:
                raw_data = file.read()
                # Reset stream position to beginning of file
                file.seek(0)
            else:
                raise ValidationError(_(f'Unsupported file format: {ext.upper()}'))
        except UnicodeEncodeError:
            raise ValidationError(_('Error reading file (invalid encoding)'))

        try:
            cleaned_data = tablib.Dataset().load(raw_data, format=ext)
        except tablib.UnsupportedFormat:
            raise ValidationError(_('Error reading file (invalid format)'))
        except tablib.core.InvalidDimensions:
            raise ValidationError(_('Error reading file (incorrect dimension)'))
        except KeyError:
            raise ValidationError(_('Error reading file (data could be corrupted)'))

        return cleaned_data

    def process(self, file):
        """Process file."""
        self.data = self.__class__.validate(file)

    def update_headers(self):
        """Update headers."""
        self.HEADERS = self.REQUIRED_HEADERS + self.ITEM_MATCH_HEADERS + self.OPTIONAL_MATCH_HEADERS + self.OPTIONAL_HEADERS

    def setup(self):
        """Setup headers should be overriden in usage to set the Different Headers."""
        if not self.name:
            return

        # Update headers
        self.update_headers()

    def guess_header(self, header, threshold=80):
        """Try to match a header (from the file) to a list of known headers.

        Args:
            header (Any): Header name to look for
            threshold (int, optional): Match threshold for fuzzy search. Defaults to 80.

        Returns:
            Any: Matched headers
        """
        # Replace null values with empty string
        if header is None:
            header = ''

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
        """Return a list of headers for the thingy."""
        headers = []

        for header in self.data.headers:
            # Guess header
            guess = self.guess_header(header, threshold=95)
            # Check if already present
            guess_exists = False
            for idx, data in enumerate(headers):
                if guess == data['guess']:
                    guess_exists = True
                    break

            if not guess_exists:
                headers.append({
                    'name': header,
                    'guess': guess
                })
            else:
                headers.append({
                    'name': header,
                    'guess': None
                })

        return headers

    def col_count(self):
        if self.data is None:
            return 0

        return len(self.data.headers)

    def row_count(self):
        """Return the number of rows in the file."""
        if self.data is None:
            return 0

        return len(self.data)

    def rows(self):
        """Return a list of all rows."""
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
                    if item == int(item) and str(item) != str(int(item)):
                        data[idx] = int(item)
                except ValueError:
                    pass
                except TypeError:
                    data[idx] = ''

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
        """Retrieve row data at a particular index."""
        if self.data is None or index >= len(self.data):
            return None

        return self.data[index]

    def get_row_dict(self, index):
        """Retrieve a dict object representing the data row at a particular offset."""
        if self.data is None or index >= len(self.data):
            return None

        return self.data.dict[index]
