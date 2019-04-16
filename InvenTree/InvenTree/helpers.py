import io

from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse


def WrapWithQuotes(text):
    # TODO - Make this better
    if not text.startswith('"'):
        text = '"' + text

    if not text.endswith('"'):
        text = text + '"'

    return text


def DownloadFile(data, filename, content_type='application/text'):
    """
    Create a dynamic file for the user to download.
    @param data is the raw file data
    """

    filename = WrapWithQuotes(filename)

    wrapper = FileWrapper(io.StringIO(data))

    response = StreamingHttpResponse(wrapper, content_type=content_type)
    response['Content-Length'] = len(data)
    response['Content-Disposition'] = 'attachment; filename={f}'.format(f=filename)

    return response
