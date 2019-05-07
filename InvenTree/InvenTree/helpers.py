"""
Provides helper functions used throughout the InvenTree project
"""

import io
import json
import os.path
from PIL import Image
import requests

from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse


def TestIfImage(img):
    """ Test if an image file is indeed an image """
    try:
        Image.open(img).verify()
        return True
    except:
        return False


def TestIfImageURL(url):
    """ Test if an image URL (or filename) looks like a valid image format.

    Simply tests the extension against a set of allowed values
    """
    return os.path.splitext(os.path.basename(url))[-1].lower() in [
        '.jpg', '.jpeg',
        '.png', '.bmp',
        '.tif', '.tiff',
        '.webp',
    ]


def DownloadExternalFile(url, **kwargs):
    """ Attempt to download an external file

    Args:
        url - External URL
    
    """

    result = {
        'status': False,
        'url': url,
        'file': None,
        'status_code': 200,
    }

    headers = {'User-Agent': 'Mozilla/5.0'}
    max_size = kwargs.get('max_size', 1048576)  # 1MB default limit

    # Get the HEAD for the file
    try:
        head = requests.head(url, stream=True, headers=headers)
    except:
        result['error'] = 'Error retrieving HEAD data'
        return result

    if not head.status_code == 200:
        result['error'] = 'Incorrect HEAD status code'
        result['status_code'] = head.status_code
        return result

    try:
        filesize = int(head.headers['Content-Length'])
    except ValueError:
        result['error'] = 'Could not decode filesize'
        result['extra'] = head.headers['Content-Length']
        return result

    if filesize > max_size:
        result['error'] = 'File size too large ({s})'.format(s=filesize)
        return result

    # All checks have passed - download the file

    try:
        request = requests.get(url, stream=True, headers=headers)
    except:
        result['error'] = 'Error retriving GET data'
        return result

    try:
        dl_file = io.StringIO(request.text)
        result['status'] = True
        result['file'] = dl_file
        return result
    except:
        result['error'] = 'Could not convert downloaded data to file'
        return result
        

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
