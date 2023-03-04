"""Template tags for rendering various barcodes."""

import base64
from io import BytesIO

from django import template

import barcode as python_barcode
import qrcode as python_qrcode

register = template.Library()


def image_data(img, fmt='PNG'):
    """Convert an image into HTML renderable data.

    Returns a string ``data:image/FMT;base64,xxxxxxxxx`` which can be rendered to an <img> tag
    """
    buffered = BytesIO()
    img.save(buffered, format=fmt)

    img_str = base64.b64encode(buffered.getvalue())

    return f"data:image/{fmt.lower()};charset=utf-8;base64," + img_str.decode()


@register.simple_tag()
def qrcode(data, **kwargs):
    """Return a byte-encoded QR code image.

    kwargs:
        fill_color: Fill color (default = black)
        back_color: Background color (default = white)
        version: Default = 1
        box_size: Default = 20
        border: Default = 1

    Returns:
        base64 encoded image data

    """
    # Construct "default" values
    params = dict(
        box_size=20,
        border=1,
        version=1,
    )

    fill_color = kwargs.pop('fill_color', 'black')
    back_color = kwargs.pop('back_color', 'white')

    format = kwargs.pop('format', 'PNG')

    params.update(**kwargs)

    qr = python_qrcode.QRCode(**params)

    qr.add_data(data, optimize=20)
    qr.make(fit=True)

    qri = qr.make_image(
        fill_color=fill_color,
        back_color=back_color
    )

    # Render to byte-encoded image
    return image_data(qri, fmt=format)


@register.simple_tag()
def barcode(data, barcode_class='code128', **kwargs):
    """Render a barcode."""
    constructor = python_barcode.get_barcode_class(barcode_class)

    format = kwargs.pop('format', 'PNG')

    data = str(data).zfill(constructor.digits)

    writer = python_barcode.writer.ImageWriter

    barcode_image = constructor(data, writer=writer())

    image = barcode_image.render(writer_options=kwargs)

    # Render to byte-encoded image
    return image_data(image, fmt=format)
