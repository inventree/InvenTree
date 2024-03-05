"""Functionality for Part import template.

Primarily Part import tools.
"""

from InvenTree.helpers import DownloadFile, GetExportFormats

from .admin import PartImportResource
from .models import Part


def IsValidPartFormat(fmt):
    """Test if a file format specifier is in the valid list of part import template file formats."""
    return fmt.strip().lower() in GetExportFormats()


def MakePartTemplate(fmt):
    """Generate a part import template file (for user download)."""
    fmt = fmt.strip().lower()

    if not IsValidPartFormat(fmt):
        fmt = 'csv'

    # Create an "empty" queryset, essentially.
    # This will then export just the row headers!
    query = Part.objects.filter(pk=None)

    dataset = PartImportResource().export(queryset=query, importing=True)

    data = dataset.export(fmt)

    filename = 'InvenTree_Part_Template.' + fmt

    return DownloadFile(data, filename)
