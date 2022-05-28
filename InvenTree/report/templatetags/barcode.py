"""Template tags for rendering various barcodes"""

import base64
from io import BytesIO

from django import template

import barcode as python_barcode
import qrcode as python_qrcode

register = template.Library()


def image_data(img, fmt='PNG'):
    """Convert an image into HTML renderable data

    Returns a string ``data:image/FMT;base64,xxxxxxxxx`` which can be rendered to an <img> tag
    """
    buffered = BytesIO()
    img.save(buffered, format=fmt)

    img_str = base64.b64encode(buffered.getvalue())

    return f"data:image/{fmt.lower()};charset=utf-8;base64," + img_str.decode()


@register.simple_tag()
def qrcode(data, **kwargs):
    """Return a byte-encoded QR code image

    Optional kwargs
    ---------------

    fill_color: Fill color (default = black)
    back_color: Background color (default = white)
    """
    # Construct "default" values
    params = dict(
        box_size=20,
        border=1,
    )

    fill_color = kwargs.pop('fill_color', 'black')
    back_color = kwargs.pop('back_color', 'white')

    params.update(**kwargs)

    qr = python_qrcode.QRCode(**params)

    qr.add_data(data, optimize=20)
    qr.make(fit=True)

    qri = qr.make_image(fill_color=fill_color, back_color=back_color)

    return image_data(qri)


@register.simple_tag()
def barcode(data, barcode_class='code128', **kwargs):
    """Render a barcode"""
    constructor = python_barcode.get_barcode_class(barcode_class)

    data = str(data).zfill(constructor.digits)

    writer = python_barcode.writer.ImageWriter

    barcode_image = constructor(data, writer=writer())

    image = barcode_image.render(writer_options=kwargs)

    # Render to byte-encoded PNG
    return image_data(image)
