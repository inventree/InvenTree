"""Template tags for rendering various barcodes."""

from django import template
from django.utils.safestring import mark_safe

import barcode as python_barcode
import qrcode.constants as ECL
from PIL import Image, ImageColor
from qrcode.main import QRCode

import report.helpers

register = template.Library()

QR_ECL_LEVEL_MAP = {
    'L': ECL.ERROR_CORRECT_L,
    'M': ECL.ERROR_CORRECT_M,
    'Q': ECL.ERROR_CORRECT_Q,
    'H': ECL.ERROR_CORRECT_H,
}


def image_data(img, fmt='PNG') -> str:
    """Convert an image into HTML renderable data.

    Returns a string ``data:image/FMT;base64,xxxxxxxxx`` which can be rendered to an <img> tag
    """
    return report.helpers.encode_image_base64(img, fmt)


@register.simple_tag()
def clean_barcode(data):
    """Return a 'cleaned' string for encoding into a barcode / qrcode.

    - This function runs the data through bleach, and removes any malicious HTML content.
    - Used to render raw barcode data into the rendered HTML templates
    """
    from InvenTree.helpers import strip_html_tags

    cleaned_date = strip_html_tags(data)

    # Remove back-tick character (prevent injection)
    cleaned_date = cleaned_date.replace('`', '')

    return mark_safe(cleaned_date)


@register.simple_tag()
def qrcode(data: str, **kwargs) -> str:
    """Return a byte-encoded QR code image.

    Arguments:
        data: Data to encode

    Keyword Arguments:
        version (int): QR code version, (None to auto detect) (default = None)
        error_correction (str): Error correction level (L: 7%, M: 15%, Q: 25%, H: 30%) (default = 'M')
        box_size (int): pixel dimensions for one black square pixel in the QR code (default = 20)
        border (int): count white QR square pixels around the qr code, needed as padding (default = 1)
        optimize (int): data will be split into multiple chunks of at least this length using different modes (text, alphanumeric, binary) to optimize the QR code size. Set to `0` to disable. (default = 1)
        format (str): Image format (default = 'PNG')
        fill_color (str): Fill color (default = "black")
        back_color (str): Background color (default = "white")

    Returns:
        image (str): base64 encoded image data

    """
    data = str(data).strip()

    if not data:
        raise ValueError("No data provided to 'qrcode' template tag")

    # Extract other arguments from kwargs
    fill_color = kwargs.pop('fill_color', 'black')
    back_color = kwargs.pop('back_color', 'white')
    image_format = kwargs.pop('format', 'PNG')
    optimize = kwargs.pop('optimize', 1)

    # Construct QR code object
    qr = QRCode(**{
        'box_size': 20,
        'border': 1,
        'version': None,
        **kwargs,
        'error_correction': QR_ECL_LEVEL_MAP[kwargs.get('error_correction', 'M')],
    })
    qr.add_data(data, optimize=optimize)
    qr.make(fit=False)  # if version is None, it will automatically use fit=True

    qri = qr.make_image(fill_color=fill_color, back_color=back_color)

    # Render to byte-encoded image
    return image_data(qri, fmt=image_format)


@register.simple_tag()
def barcode(data: str, barcode_class='code128', **kwargs) -> str:
    """Render a 1D barcode.

    Arguments:
        data: Data to encode

    Keyword Arguments:
        format (str): Image format (default = 'PNG')
        fill_color (str): Foreground color (default = 'black')
        back_color (str): Background color (default = 'white')
        scale (float): Scaling factor (default = 1)

    Returns:
        image (str): base64 encoded image data
    """
    data = str(data).strip()

    if not data:
        raise ValueError("No data provided to 'barcode' template tag")

    constructor = python_barcode.get_barcode_class(barcode_class)

    img_format = kwargs.pop('format', 'PNG')

    data = str(data).zfill(constructor.digits)

    writer = python_barcode.writer.ImageWriter

    barcode_image = constructor(data, writer=writer())

    image = barcode_image.render(writer_options=kwargs)

    # Render to byte-encoded image
    return image_data(image, fmt=img_format)


@register.simple_tag()
def datamatrix(data: str, **kwargs) -> str:
    """Render a DataMatrix barcode.

    Arguments:
        data: Data to encode

    Keyword Arguments:
        fill_color (str): Foreground color (default = 'black')
        back_color (str): Background color (default = 'white')
        scale (float): Matrix scaling factor (default = 1)
        border (int): Border width (default = 1)

    Returns:
        image (str): base64 encoded image data
    """
    from ppf.datamatrix import DataMatrix

    data = str(data).strip()

    if not data:
        raise ValueError("No data provided to 'datamatrix' template tag")

    dm = DataMatrix(data)

    fill_color = kwargs.pop('fill_color', 'black')
    back_color = kwargs.pop('back_color', 'white')

    border = kwargs.pop('border', 1)

    try:
        border = int(border)
    except Exception:
        border = 1

    border = max(0, border)

    try:
        fg = ImageColor.getcolor(fill_color, 'RGB')
    except Exception:
        fg = ImageColor.getcolor('black', 'RGB')

    try:
        bg = ImageColor.getcolor(back_color, 'RGB')
    except Exception:
        bg = ImageColor.getcolor('white', 'RGB')

    scale = kwargs.pop('scale', 1)

    height = len(dm.matrix) + 2 * border
    width = len(dm.matrix[0]) + 2 * border

    # Generate raw image from the matrix
    img = Image.new('RGB', (width, height), color=bg)

    for y, row in enumerate(dm.matrix):
        for x, value in enumerate(row):
            if value:
                img.putpixel((x + border, y + border), fg)

    if scale != 1:
        img = img.resize((int(width * scale), int(height * scale)))

    return image_data(img, fmt='PNG')
