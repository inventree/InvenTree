"""
Template tags for rendering various barcodes
"""

import os
import base64

from io import BytesIO


from django import template

import qrcode
import barcode

register = template.Library()


def image_data(img, fmt='PNG'):
    """
    Convert an image into HTML renderable data

    Returns a string ``data:image/FMT;base64,xxxxxxxxx`` which can be rendered to an <img> tag
    """

    buffered = BytesIO()
    img.save(buffered, format=fmt)
    
    img_str = base64.b64encode(buffered.getvalue())

    return f"data:image/{fmt.lower()};charset=utf-8;base64," + img_str.decode()


@register.simple_tag()
def qr_code(data, **kwargs):
    """
    Return a byte-encoded QR code image

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

    qr = qrcode.QRCode(**params)

    qr.add_data(data, optimize=20)
    qr.make(fit=True)

    qri = qr.make_image(fill_color=fill_color, back_color=back_color)

    return image_data(qri)