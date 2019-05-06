"""
Provides helper functions used throughout the InvenTree project
"""

import io
import json
from datetime import datetime
from PIL import Image

from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse


def TestIfImage(img):
    """ Test if an image file is indeed an image """
    try:
        Image.open(img).verify()
        return True
    except:
        return False


def str2bool(text, test=True):
    """ Test if a string 'looks' like a boolean value.

    Args:
        text: Input text
        test (default = True): Set which boolean value to look for

    Returns:
        True if the text looks like the selected boolean value
    """
    if test:
        return str(text).lower() in ['1', 'y', 'yes', 't', 'true', 'ok', ]
    else:
        return str(text).lower() in ['0', 'n', 'no', 'none', 'f', 'false', ]


def WrapWithQuotes(text, quote='"'):
    """ Wrap the supplied text with quotes

    Args:
        text: Input text to wrap
        quote: Quote character to use for wrapping (default = "")

    Returns:
        Supplied text wrapped in quote char
    """

    if not text.startswith(quote):
        text = quote + text

    if not text.endswith(quote):
        text = text + quote

    return text


def MakeBarcode(object_type, object_id, object_url, data={}):
    """ Generate a string for a barcode. Adds some global InvenTree parameters.

    Args:
        object_type: string describing the object type e.g. 'StockItem'
        object_id: ID (Primary Key) of the object in the database
        object_url: url for JSON API detail view of the object
        data: Python dict object containing extra datawhich will be rendered to string (must only contain stringable values)

    Returns:
        json string of the supplied data plus some other data
    """

    # Add in some generic InvenTree data
    data['type'] = object_type
    data['id'] = object_id
    data['url'] = object_url
    data['tool'] = 'InvenTree'
    data['generated'] = str(datetime.now().date())

    return json.dumps(data, sort_keys=True)


def DownloadFile(data, filename, content_type='application/text'):
    """ Create a dynamic file for the user to download.
    
    Args:
        data: Raw file data (string or bytes)
        filename: Filename for the file download
        content_type: Content type for the download

    Return:
        A StreamingHttpResponse object wrapping the supplied data
    """

    filename = WrapWithQuotes(filename)

    if type(data) == str:
        wrapper = FileWrapper(io.StringIO(data))
    else:
        wrapper = FileWrapper(io.BytesIO(data))

    response = StreamingHttpResponse(wrapper, content_type=content_type)
    response['Content-Length'] = len(data)
    response['Content-Disposition'] = 'attachment; filename={f}'.format(f=filename)

    return response
