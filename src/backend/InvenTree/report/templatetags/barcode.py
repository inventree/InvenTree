"""Template tags for rendering various barcodes."""

from django import template

import barcode as python_barcode
import qrcode.constants as ECL
from qrcode.main import QRCode

import report.helpers

register = template.Library()

QR_ECL_LEVEL_MAP = {
    'L': ECL.ERROR_CORRECT_L,
    'M': ECL.ERROR_CORRECT_M,
    'Q': ECL.ERROR_CORRECT_Q,
    'H': ECL.ERROR_CORRECT_H,
}


def image_data(img, fmt='PNG'):
    """Convert an image into HTML renderable data.

    Returns a string ``data:image/FMT;base64,xxxxxxxxx`` which can be rendered to an <img> tag
    """
    return report.helpers.encode_image_base64(img, fmt)


@register.simple_tag()
def qrcode(data, **kwargs):
    """Return a byte-encoded QR code image.

    Arguments:
        data: Data to encode

    Keyword Arguments:
        version: QR code version, (None to auto detect) (default = None)
        error_correction: Error correction level (L: 7%, M: 15%, Q: 25%, H: 30%) (default = 'M')
        box_size: pixel dimensions for one black square pixel in the QR code (default = 20)
        border: count white QR square pixels around the qr code, needed as padding (default = 1)
        optimize: data will be split into multiple chunks of at least this length using different modes (text, alphanumeric, binary) to optimize the QR code size. Set to `0` to disable. (default = 1)
        format: Image format (default = 'PNG')
        fill_color: Fill color (default = "black")
        back_color: Background color (default = "white")

    Returns:
        base64 encoded image data

    """
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
def barcode(data, barcode_class='code128', **kwargs):
    """Render a barcode."""
    constructor = python_barcode.get_barcode_class(barcode_class)

    img_format = kwargs.pop('format', 'PNG')

    data = str(data).zfill(constructor.digits)

    writer = python_barcode.writer.ImageWriter

    barcode_image = constructor(data, writer=writer())

    image = barcode_image.render(writer_options=kwargs)

    # Render to byte-encoded image
    return image_data(image, fmt=img_format)
